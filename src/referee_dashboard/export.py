import csv
import io

from referee_dashboard.db import db
from referee_dashboard.models import Game, League, Position, Team

# ── CSV ──────────────────────────────────────────────────

BOM = "\ufeff"
DELIMITER = ";"


def _csv_string(header: list[str], rows: list[list[str]]) -> str:
    """Build a semicolon-separated CSV string with BOM for Excel."""
    buf = io.StringIO()
    buf.write(BOM)
    writer = csv.writer(buf, delimiter=DELIMITER, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(header)
    writer.writerows(rows)
    return buf.getvalue()


def games_csv() -> str:
    games = Game.query.order_by(Game.game_date.desc(), Game.game_time.asc()).all()
    header = [
        "Datum",
        "Uhrzeit",
        "Heimteam",
        "Gastteam",
        "Spielort",
        "Liga",
        "Position",
        "Honorar",
        "Fahrtkosten",
        "Kilometer",
        "Freundschaftsspiel",
        "Bemerkungen",
    ]
    rows = [
        [
            g.game_date,
            g.game_time or "",
            g.home_team.name,
            g.away_team.name,
            g.venue or "",
            g.league.name,
            g.position,
            str(g.referee_fee).replace(".", ","),
            str(g.travel_costs).replace(".", ","),
            str(g.km_driven),
            "Ja" if g.exhibition else "Nein",
            g.remarks or "",
        ]
        for g in games
    ]
    return _csv_string(header, rows)


def teams_csv() -> str:
    teams = Team.query.order_by(Team.name).all()
    header = ["Name", "Bundesland", "Aktiv", "Bemerkungen"]
    rows = [
        [t.name, t.state or "", "Ja" if t.is_active else "Nein", t.remarks or ""] for t in teams
    ]
    return _csv_string(header, rows)


def leagues_csv() -> str:
    leagues = League.query.order_by(League.sorter, League.name).all()
    header = ["Name", "Sortierung", "Bemerkungen"]
    rows = [[lg.name, str(lg.sorter), lg.remarks or ""] for lg in leagues]
    return _csv_string(header, rows)


# ── SQL (INSERT statements) ─────────────────────────────


def _escape(val) -> str:
    """Escape a value for SQL INSERT."""
    if val is None:
        return "NULL"
    if isinstance(val, int | float):
        return str(val)
    return "'" + str(val).replace("'", "''") + "'"


def _inserts(table: str, columns: list[str], rows: list[list], or_ignore: bool = False) -> str:
    """Generate INSERT statements."""
    keyword = "INSERT OR IGNORE" if or_ignore else "INSERT"
    lines = []
    for row in rows:
        vals = ", ".join(_escape(v) for v in row)
        cols = ", ".join(columns)
        lines.append(f"{keyword} INTO {table} ({cols}) VALUES ({vals});")
    return "\n".join(lines)


def games_sql() -> str:
    games = Game.query.order_by(Game.game_date.desc()).all()
    columns = [
        "game_date",
        "game_time",
        "home_team_id",
        "away_team_id",
        "venue",
        "league_id",
        "position",
        "referee_fee",
        "travel_costs",
        "km_driven",
        "exhibition",
        "remarks",
    ]
    rows = [
        [
            g.game_date,
            g.game_time,
            g.home_team_id,
            g.away_team_id,
            g.venue,
            g.league_id,
            g.position,
            g.referee_fee,
            g.travel_costs,
            g.km_driven,
            g.exhibition,
            g.remarks,
        ]
        for g in games
    ]
    return _inserts("games", columns, rows)


def teams_sql() -> str:
    teams = Team.query.order_by(Team.name).all()
    columns = ["name", "state", "is_active", "remarks"]
    rows = [[t.name, t.state, t.is_active, t.remarks] for t in teams]
    return _inserts("teams", columns, rows)


def leagues_sql() -> str:
    leagues = League.query.order_by(League.sorter, League.name).all()
    columns = ["name", "sorter", "remarks"]
    rows = [[lg.name, lg.sorter, lg.remarks] for lg in leagues]
    return _inserts("leagues", columns, rows)


# ── Full dump (schema + data) ───────────────────────────


def full_dump() -> str:
    """Complete SQLite dump: CREATE TABLE + INSERT for all tables in FK order."""
    # FK order: positions, leagues, teams, games
    table_order = ["positions", "leagues", "teams", "games"]

    engine = db.engine
    raw = engine.raw_connection()
    conn = raw.connection
    cursor = conn.cursor()

    parts = ["BEGIN TRANSACTION;"]

    # Collect CREATE TABLE statements in FK order
    for table in table_order:
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        )
        row = cursor.fetchone()
        if row and row[0]:
            sql = row[0].replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1)
            parts.append(f"{sql};")

    # Collect INSERT statements in FK order
    for table in table_order:
        cursor.execute(f"SELECT * FROM [{table}]")  # noqa: S608
        cols = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            vals = ", ".join(_escape(v) for v in row)
            col_str = ", ".join(cols)
            parts.append(f"INSERT OR IGNORE INTO {table} ({col_str}) VALUES ({vals});")

    parts.append("COMMIT;")
    raw.close()
    return "\n".join(parts)


# ── All data (INSERTs only, all tables, FK order) ───────


def all_data_sql() -> str:
    """INSERT statements for all tables in FK order (no schema)."""
    parts = []

    # Positions
    positions = Position.query.order_by(Position.sorter).all()
    if positions:
        cols = ["position", "long", "sorter"]
        rows = [[p.position, p.long, p.sorter] for p in positions]
        parts.append("-- positions")
        parts.append(_inserts("positions", cols, rows))

    # Leagues
    leagues = League.query.order_by(League.id).all()
    if leagues:
        cols = ["id", "name", "sorter", "remarks"]
        rows = [[lg.id, lg.name, lg.sorter, lg.remarks] for lg in leagues]
        parts.append("\n-- leagues")
        parts.append(_inserts("leagues", cols, rows))

    # Teams
    teams = Team.query.order_by(Team.id).all()
    if teams:
        cols = ["id", "name", "state", "is_active", "remarks"]
        rows = [[t.id, t.name, t.state, t.is_active, t.remarks] for t in teams]
        parts.append("\n-- teams")
        parts.append(_inserts("teams", cols, rows))

    # Games
    games = Game.query.order_by(Game.id).all()
    if games:
        cols = [
            "id",
            "game_date",
            "game_time",
            "home_team_id",
            "away_team_id",
            "venue",
            "league_id",
            "position",
            "referee_fee",
            "travel_costs",
            "km_driven",
            "exhibition",
            "remarks",
        ]
        rows = [
            [
                g.id,
                g.game_date,
                g.game_time,
                g.home_team_id,
                g.away_team_id,
                g.venue,
                g.league_id,
                g.position,
                g.referee_fee,
                g.travel_costs,
                g.km_driven,
                g.exhibition,
                g.remarks,
            ]
            for g in games
        ]
        parts.append("\n-- games")
        parts.append(_inserts("games", cols, rows))

    return "\n".join(parts)
