import re

BUNDESLAENDER = [
    "Baden-Württemberg",
    "Bayern",
    "Berlin",
    "Brandenburg",
    "Bremen",
    "Hamburg",
    "Hessen",
    "Mecklenburg-Vorpommern",
    "Niedersachsen",
    "Nordrhein-Westfalen",
    "Rheinland-Pfalz",
    "Saarland",
    "Sachsen",
    "Sachsen-Anhalt",
    "Schleswig-Holstein",
    "Thüringen",
]

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _require(form, field, errors, label):
    """Check that a field is present and non-empty."""
    val = form.get(field, "").strip()
    if not val:
        errors[field] = f"{label} ist ein Pflichtfeld."
        return ""
    return val


def _parse_float(form, field, errors, label, default=0.0):
    """Parse a float field, must be >= 0."""
    raw = form.get(field, "").strip()
    if not raw:
        return default
    try:
        val = float(raw)
    except ValueError:
        errors[field] = f"{label} muss eine Zahl sein."
        return default
    if val < 0:
        errors[field] = f"{label} darf nicht negativ sein."
    return val


def _parse_int(form, field, errors, label, default=0):
    """Parse an int field, must be >= 0."""
    raw = form.get(field, "").strip()
    if not raw:
        return default
    try:
        val = int(float(raw))
    except ValueError:
        errors[field] = f"{label} muss eine ganze Zahl sein."
        return default
    if val < 0:
        errors[field] = f"{label} darf nicht negativ sein."
    return val


def validate_game(form):
    """Validate game form data. Returns (data, errors)."""
    errors = {}
    data = {}

    # Required fields
    date_str = _require(form, "game_date", errors, "Datum")
    if date_str and not _ISO_DATE.match(date_str):
        errors["game_date"] = "Datum muss im Format JJJJ-MM-TT sein."
    data["game_date"] = date_str

    data["game_time"] = form.get("game_time", "").strip() or None

    # Team IDs
    home_raw = _require(form, "home_team_id", errors, "Heimteam")
    away_raw = _require(form, "away_team_id", errors, "Gastteam")
    try:
        data["home_team_id"] = int(home_raw) if home_raw else 0
    except ValueError:
        errors["home_team_id"] = "Heimteam ist ungültig."
        data["home_team_id"] = 0
    try:
        data["away_team_id"] = int(away_raw) if away_raw else 0
    except ValueError:
        errors["away_team_id"] = "Gastteam ist ungültig."
        data["away_team_id"] = 0

    if (
        data["home_team_id"]
        and data["away_team_id"]
        and data["home_team_id"] == data["away_team_id"]
    ):
        errors["away_team_id"] = "Heim- und Gastteam dürfen nicht identisch sein."

    # League + Position
    league_raw = _require(form, "league_id", errors, "Liga")
    try:
        data["league_id"] = int(league_raw) if league_raw else 0
    except ValueError:
        errors["league_id"] = "Liga ist ungültig."
        data["league_id"] = 0

    data["position"] = _require(form, "position", errors, "Position")

    # Numeric fields
    data["referee_fee"] = _parse_float(form, "referee_fee", errors, "Honorar")
    data["travel_costs"] = _parse_float(form, "travel_costs", errors, "Fahrtkosten")
    data["km_driven"] = _parse_int(form, "km_driven", errors, "Kilometer")

    # Optional
    data["venue"] = form.get("venue", "").strip()
    data["exhibition"] = 1 if form.get("exhibition") else 0
    data["remarks"] = form.get("remarks", "").strip()

    return data, errors


def validate_team(form):
    """Validate team form data. Returns (data, errors)."""
    errors = {}
    data = {}

    data["name"] = _require(form, "name", errors, "Name")
    data["state"] = form.get("state", "").strip()
    data["is_active"] = 1 if form.get("is_active") else 0
    data["remarks"] = form.get("remarks", "").strip()

    return data, errors


def validate_league(form):
    """Validate league form data. Returns (data, errors)."""
    errors = {}
    data = {}

    data["name"] = _require(form, "name", errors, "Name")
    data["sorter"] = _parse_int(form, "sorter", errors, "Sortierung")
    data["remarks"] = form.get("remarks", "").strip()

    return data, errors
