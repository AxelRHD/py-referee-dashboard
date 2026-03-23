import csv
import io
import re

from referee_dashboard.db import db
from referee_dashboard.models import Game, League, Team
from referee_dashboard.validation import validate_game, validate_league, validate_team

ALLOWED_PREFIXES = re.compile(r"^\s*(INSERT|CREATE\s+TABLE)", re.IGNORECASE)
BLOCKED_KEYWORDS = re.compile(
    r"^\s*(DROP|DELETE|UPDATE|ALTER|TRUNCATE|REPLACE|ATTACH|DETACH|PRAGMA|VACUUM)",
    re.IGNORECASE,
)


def sanitize_sql(text: str) -> tuple[list[str], list[str]]:
    """Parse SQL text and return (allowed_statements, errors).

    Only INSERT and CREATE TABLE statements are allowed.
    """
    errors = []
    statements = []

    # Split on semicolons, keeping each statement
    raw_stmts = [s.strip() for s in text.split(";") if s.strip()]

    # Transaction wrappers to silently skip (from dumps)
    skip_re = re.compile(r"^\s*(BEGIN|COMMIT|ROLLBACK)", re.IGNORECASE)

    for stmt in raw_stmts:
        # Skip comments and transaction wrappers
        if stmt.startswith("--") or skip_re.match(stmt):
            continue

        if BLOCKED_KEYWORDS.match(stmt):
            keyword = stmt.split()[0].upper()
            errors.append(f"{keyword}-Statements sind nicht erlaubt: {stmt[:80]}...")
        elif ALLOWED_PREFIXES.match(stmt):
            statements.append(stmt)
        elif stmt:
            errors.append(f"Statement nicht erlaubt: {stmt[:80]}...")

    return statements, errors


def execute_sql(statements: list[str]) -> tuple[int, list[str]]:
    """Execute a list of SQL statements. Returns (success_count, errors)."""
    errors = []
    count = 0
    conn = db.engine.raw_connection()
    try:
        cursor = conn.connection.cursor()
        for stmt in statements:
            try:
                cursor.execute(stmt)
                count += 1
            except Exception as e:
                errors.append(f"Fehler: {e} — {stmt[:80]}...")
        conn.connection.commit()
    except Exception as e:
        errors.append(f"Fehler beim Commit: {e}")
    finally:
        conn.close()
    return count, errors


ENTITY_MAP = {
    "games": ("Spiele", validate_game, Game),
    "teams": ("Teams", validate_team, Team),
    "leagues": ("Ligen", validate_league, League),
}


def import_csv(text: str, entity: str) -> tuple[int, list[str]]:
    """Import CSV text for a given entity. Returns (count, errors)."""
    if entity not in ENTITY_MAP:
        return 0, [f"Unbekannte Entity: {entity}"]

    label, validate_fn, model_cls = ENTITY_MAP[entity]
    errors = []
    count = 0

    # Detect delimiter
    delimiter = ";" if ";" in text.split("\n", 1)[0] else ","

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

    for i, row in enumerate(reader, start=2):
        # Build form-like dict for validation
        form = _csv_row_to_form(row, entity)
        data, row_errors = validate_fn(form)
        if row_errors:
            msgs = "; ".join(f"{k}: {v}" for k, v in row_errors.items())
            errors.append(f"Zeile {i}: {msgs}")
            continue
        try:
            obj = model_cls(**data)
            db.session.add(obj)
            count += 1
        except Exception as e:
            errors.append(f"Zeile {i}: {e}")

    if count > 0:
        db.session.commit()

    return count, errors


# CSV column name mapping (German headers → form field names)

_GAME_COLUMNS = {
    "datum": "game_date",
    "uhrzeit": "game_time",
    "heimteam": "home_team_id",
    "gastteam": "away_team_id",
    "spielort": "venue",
    "liga": "league_id",
    "position": "position",
    "honorar": "referee_fee",
    "fahrtkosten": "travel_costs",
    "kilometer": "km_driven",
    "freundschaftsspiel": "exhibition",
    "bemerkungen": "remarks",
}

_TEAM_COLUMNS = {
    "name": "name",
    "bundesland": "state",
    "aktiv": "is_active",
    "bemerkungen": "remarks",
}

_LEAGUE_COLUMNS = {
    "name": "name",
    "kürzel": "short_name",
    "sortierung": "sorter",
    "bemerkungen": "remarks",
}


def _normalize_key(key: str) -> str:
    """Normalize CSV column header for matching."""
    return key.strip().lower().replace(" ", "").replace("_", "")


def _csv_row_to_form(row: dict, entity: str) -> dict:
    """Map CSV row (German headers) to form field names."""
    column_map = {"games": _GAME_COLUMNS, "teams": _TEAM_COLUMNS, "leagues": _LEAGUE_COLUMNS}[
        entity
    ]

    form = {}
    for csv_key, value in row.items():
        if csv_key is None:
            continue
        normalized = _normalize_key(csv_key)
        for german, field in column_map.items():
            if _normalize_key(german) == normalized:
                form[field] = _transform_csv_value(field, value or "")
                break
    return form


def _resolve_name_to_id(field: str, value: str) -> str:
    """Resolve a name to a DB id for FK fields. Returns ID as string or original value."""
    from referee_dashboard.models import League, Team

    if field in ("home_team_id", "away_team_id"):
        # If already numeric, keep as-is
        if value.isdigit():
            return value
        team = Team.query.filter(Team.name == value).first()
        return str(team.id) if team else value

    if field == "league_id":
        if value.isdigit():
            return value
        league = League.query.filter(League.name == value).first()
        return str(league.id) if league else value

    return value


def _transform_csv_value(field: str, value: str) -> str:
    """Transform CSV values to form-compatible strings."""
    value = value.strip()

    # German decimal comma → dot for numeric fields
    if field in ("referee_fee", "travel_costs"):
        value = value.replace("€", "").replace(" ", "").strip()
        value = value.replace(".", "").replace(",", ".")

    # Boolean fields
    if field in ("exhibition", "is_active"):
        value = "1" if value.lower() in ("ja", "1", "true", "yes", "x") else ""

    # FK fields: resolve names to IDs
    if field in ("home_team_id", "away_team_id", "league_id"):
        value = _resolve_name_to_id(field, value)

    return value
