from sqlalchemy import Table, Column, Integer, ForeignKey, String, Boolean, PickleType, DateTime, create_engine
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
from datetime import datetime, timedelta
import config
import math
import random
import string

engine = create_engine(URL(**config.DATABASE))
session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = session.query_property()

class Team(Base):
    __tablename__ = "team"
    id = Column(Integer, primary_key=True)
    number = Column(Integer)
    title = Column(String(50))
    names = Column(PickleType)


class Token(Base):
    __tablename__ = "token"
    name = Column(String(50), primary_key=True)
    value = Column(String(50))

    def refresh(self):
        self.value = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(32))


class Match(Base):
    __tablename__ = "match"
    id = Column(Integer, primary_key=True)
    number = Column(Integer)
    team1_id = Column(Integer, ForeignKey('team.id'))
    team2_id = Column(Integer, ForeignKey('team.id'))
    team1 = relationship("Team", foreign_keys='Match.team1_id', lazy='joined')
    team2 = relationship("Team", foreign_keys='Match.team2_id', lazy='joined')
    live = Column(Boolean, default=False)
    video_pending = Column(Boolean, default=False)
    team1_score = Column(Integer, default=0)
    team2_score = Column(Integer, default=0)
    winner = Column(Integer, default=0)
    video = Column(String(200), default="")
    key = Column(String(50), default="")
    time = Column(DateTime)

    def get_round(self):
        rounds_left = int(math.log(config.NUMBER_OF_TEAMS - self.number - 1, 2))
        if rounds_left == 0:
            return "Finals"
        elif rounds_left == 1:
            return "Semifinals"
        else:
            total_rounds = int(math.log(config.NUMBER_OF_TEAMS, 2))
            return "Round " + str(total_rounds - rounds_left)

    def get_time(self):
        return '{d:%I}:{d.minute:02} {d:%p}'.format(d=self.time).lower().lstrip('0')

    def raw_time(self):
        return '{d.hour:02}:{d.minute:02}'.format(d=self.time)

    def advance_winner(self):
        if self.number != config.NUMBER_OF_TEAMS - 2:
            next_match = self.next_match()
            if self.winner == 0:
                if self.number % 2 == 0:
                    next_match.team1 = null_team()
                    next_match.winner = 0
                else:
                    next_match.team2 = null_team()
                    next_match.winner = 0
            elif self.winner == 1:
                if self.number % 2 == 0:
                    next_match.team1 = self.team1
                else:
                    next_match.team2 = self.team1
            else:
                if self.number % 2 == 0:
                    next_match.team1 = self.team2
                else:
                    next_match.team2 = self.team2
            session.commit()
            next_match.advance_winner()

    def next_match(self):
        total_rounds = int(math.log(config.NUMBER_OF_TEAMS, 2))
        rounds_left = int(math.log(config.NUMBER_OF_TEAMS - self.number - 1, 2))
        offset = int((self.number - config.NUMBER_OF_TEAMS + 2**(rounds_left + 1)))
        round_diff = 2**rounds_left
        next_match_number = (self.number - offset) + round_diff + int(offset/2)
        return Match.query.filter(Match.number==next_match_number).first()


def cookie_value():
    return Token.query.filter(Token.name==config.NAME).first().value

def null_team():
    return Team.query.filter(Team.number==-1).first()

def blank_team(number, team_size):
    blank_team = Team(number=number, names=["" for i in range(team_size)])
    session.add(blank_team)
    session.commit()
    return blank_team

def init(num_of_teams, team_size, start_time, time_diff):
    if Token.query.filter(Token.name==config.NAME).count() == 0:
        cookie = Token(name=config.NAME,value="")
        cookie.refresh()
        session.add(cookie)
        session.commit()

    if Team.query.filter(Team.number != -1).count() >= num_of_teams:
        return

    null_team = Team(number=-1, names=["" for i in range(team_size)])
    session.add(null_team)
    session.commit()
    start = start_time
    for i in range(int(num_of_teams/2)):
        team1 = blank_team(i*2, team_size)
        team2 = blank_team(i*2+1, team_size)
        new_match = Match(number=i, team1=team1, team2=team2, time=start)
        session.add(new_match)
        start = start + time_diff
    for i in range(int(num_of_teams/2), num_of_teams-1):
        new_match = Match(number=i, team1=null_team, team2=null_team, time=start)
        session.add(new_match)
        start = start + time_diff
    session.commit()

def get_all_matches():
    return Match.query.order_by(Match.number).all()

def get_all_teams():
    return Team.query.filter(Team.number != -1).order_by(Team.number)

def get_match(number):
    return Match.query.filter(Match.number == number).first()

def update_times():
    matches = get_all_matches()
    start_time = config.START_TIME
    time_diff = config.TIME_PER_MATCH
    for match in matches:
        match.time = start_time
        start_time += time_diff
    session.commit()

def delay_matches(minutes):
    matches = get_all_matches()
    diff = timedelta(minutes=minutes)
    for match in matches:
        match.time = match.time + diff
    session.commit()

def migrate():
    Base.metadata.create_all(bind=engine)
