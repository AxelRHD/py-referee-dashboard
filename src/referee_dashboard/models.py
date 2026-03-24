from datetime import datetime

from referee_dashboard.db import db


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class League(db.Model):
    __tablename__ = "leagues"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    short_name = db.Column(db.String, nullable=False, default="")
    sorter = db.Column(db.Integer, nullable=False, default=0)
    remarks = db.Column(db.String, default="")
    created_at = db.Column(db.String, nullable=False, default=_now)
    updated_at = db.Column(db.String, nullable=False, default=_now, onupdate=_now)


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    state = db.Column(db.String, default="Baden-Württemberg")
    is_active = db.Column(db.Integer, nullable=False, default=1)
    remarks = db.Column(db.String, default="")
    created_at = db.Column(db.String, nullable=False, default=_now)
    updated_at = db.Column(db.String, nullable=False, default=_now, onupdate=_now)


class Position(db.Model):
    __tablename__ = "positions"

    position = db.Column(db.String, primary_key=True)
    long = db.Column(db.String, nullable=False)
    sorter = db.Column(db.Integer, nullable=False, unique=True)


class Venue(db.Model):
    __tablename__ = "venues"

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String, nullable=False)
    stadium = db.Column(db.String, nullable=False, default="")
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    created_at = db.Column(db.String, nullable=False, default=_now)
    updated_at = db.Column(db.String, nullable=False, default=_now, onupdate=_now)

    @property
    def display_name(self):
        if self.stadium:
            return f"{self.stadium}, {self.city}"
        return self.city


class Game(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True)
    game_date = db.Column(db.String, nullable=False)
    game_time = db.Column(db.String)
    home_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey("venues.id"))
    league_id = db.Column(db.Integer, db.ForeignKey("leagues.id"), nullable=False)
    position = db.Column(db.String, db.ForeignKey("positions.position"), nullable=False)
    referee_fee = db.Column(db.Float, nullable=False, default=0.0)
    travel_costs = db.Column(db.Float, nullable=False, default=0.0)
    km_driven = db.Column(db.Integer, nullable=False, default=0)
    exhibition = db.Column(db.Integer, nullable=False, default=0)
    remarks = db.Column(db.String, default="")
    created_at = db.Column(db.String, nullable=False, default=_now)
    updated_at = db.Column(db.String, nullable=False, default=_now, onupdate=_now)

    home_team = db.relationship("Team", foreign_keys=[home_team_id])
    away_team = db.relationship("Team", foreign_keys=[away_team_id])
    venue = db.relationship("Venue", foreign_keys=[venue_id])
    league = db.relationship("League", foreign_keys=[league_id])
    pos = db.relationship("Position", foreign_keys=[position])
