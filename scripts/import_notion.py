"""Import games from Notion CSV export into the referee dashboard database."""

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from referee_dashboard.app import create_app
from referee_dashboard.db import db
from referee_dashboard.models import Game, League, Team

PLACEHOLDER_LEAGUE = "Unbekannt"
PLACEHOLDER_TEAM = "Unbekannt"


def parse_euro(value: str) -> float:
    """Parse '50,00 €' or '0,70 €' to float."""
    if not value or not value.strip():
        return 0.0
    cleaned = value.replace("€", "").replace(".", "").replace(",", ".").strip()
    return float(cleaned)


def parse_team_name(value: str) -> str:
    """Extract team name from 'Name (https://...)'."""
    if " (http" in value:
        return value.split(" (http")[0].strip()
    return value.strip()


def parse_datum(value: str) -> tuple[str, str | None]:
    """Parse 'DD/MM/YYYY' or 'DD/MM/YYYY HH:MM (TZ)' to (YYYY-MM-DD, HH:MM|None)."""
    value = value.strip()
    value = re.sub(r"\s*\([^)]+\)\s*$", "", value)

    parts = value.split(" ")
    date_part = parts[0]
    time_part = parts[1] if len(parts) > 1 else None

    day, month, year = date_part.split("/")
    game_date = f"{year}-{month}-{day}"

    return game_date, time_part


def import_csv(csv_path: str):
    app = create_app()

    with app.app_context():
        # Clear existing data
        Game.query.delete()
        Team.query.delete()
        League.query.delete()
        db.session.commit()

        # Read CSV
        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        # Collect unique leagues and teams
        league_names = set()
        team_names = set()
        for row in rows:
            liga = row["Liga"].strip()
            if liga:
                league_names.add(liga)
            for col in ["👥 Heim", "👥 Gast"]:
                name = parse_team_name(row[col])
                if name:
                    team_names.add(name)

        # Add placeholder for incomplete data
        league_names.add(PLACEHOLDER_LEAGUE)
        team_names.add(PLACEHOLDER_TEAM)

        # Create leagues
        league_map = {}
        for name in sorted(league_names):
            league = League(name=name)
            db.session.add(league)
            db.session.flush()
            league_map[name] = league.id
        print(f"Ligen angelegt: {len(league_map)}")

        # Create teams (placeholder as inactive)
        team_map = {}
        for name in sorted(team_names):
            is_active = 0 if name == PLACEHOLDER_TEAM else 1
            team = Team(name=name, is_active=is_active)
            db.session.add(team)
            db.session.flush()
            team_map[name] = team.id
        print(f"Teams angelegt: {len(team_map)}")

        # Import games (skip Notion template rows)
        imported = 0
        for row in rows:
            if row.get("Spiel", "").startswith("["):
                continue
            home_name = parse_team_name(row["👥 Heim"]) or PLACEHOLDER_TEAM
            away_name = parse_team_name(row["👥 Gast"]) or PLACEHOLDER_TEAM
            liga = row["Liga"].strip() or PLACEHOLDER_LEAGUE

            game_date, game_time = parse_datum(row["Datum"])
            venue = row.get("Spielort", "").strip()

            position_val = row["Position"].strip()
            if not position_val:
                position_val = "R"

            game = Game(
                game_date=game_date,
                game_time=game_time,
                home_team_id=team_map[home_name],
                away_team_id=team_map[away_name],
                venue=venue,
                league_id=league_map[liga],
                position=position_val,
                referee_fee=parse_euro(row.get("Pauschale", "")),
                travel_costs=parse_euro(row.get("Fahrtkosten", "")),
                km_driven=int(float(row["Kilometer"].replace(",", ".")))
                if row.get("Kilometer")
                else 0,
                exhibition=1 if row.get("Freundschaftsspiel", "").strip() == "Yes" else 0,
                remarks="",
            )
            db.session.add(game)
            imported += 1

        db.session.commit()
        print(f"Spiele importiert: {imported}")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    if not csv_path:
        print("Usage: python scripts/import_notion.py <path-to-csv>")
        sys.exit(1)
    import_csv(csv_path)
