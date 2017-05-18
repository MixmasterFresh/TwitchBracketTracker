from mongoengine import *
from datetime import datetime
import config
import math

connect(config.DB_NAME, host='localhost', port=27017)

class Team(Document):
    number = IntField(primary_key=True)
    names = ListField(StringField())

class Match(Document):
    number = IntField(primary_key=True)
    team1 = ReferenceField(Team, required=True)
    team2 = ReferenceField(Team, required=True)
    live = BooleanField(live=False)
    team1_score = IntField(default=0)
    team2_score = IntField(default=0)
    winner = IntField(default=0)
    video = StringField(default="", required=True)
    key = StringField(default="", required=True)
    note = StringField(default="", required=True)
    time = DateTimeField()

    def get_round(self):
        rounds_left = int(math.log(config.NUMBER_OF_TEAMS - self.id - 1, 2))
        if rounds_left == 0:
            return "Finals"
        elif rounds_left == 1:
            return "Semifinals"
        else:
            total_rounds = int(math.log(config.NUMBER_OF_TEAMS, 2))
            return "Round " + str(total_rounds - rounds_left)

    def get_time(self):
        return '{d:%I}:{d.minute:02} {d:%p}'.format(d=self.time).lower().lstrip('0')

    def advance_winner(self):
        if self.id != config.NUMBER_OF_TEAMS - 2:
            next_match = self.next_match()
            if self.winner == 0:
                if self.id % 2 == 0:
                    next_match.team1 = null_team()
                    next_match.winner = 0
                else:
                    next_match.team2 = null_team()
                    next_match.winner = 0
            elif self.winner == 1:
                if self.id % 2 == 0:
                    next_match.team1 = self.team1
                else:
                    next_match.team2 = self.team1
            else:
                if self.id % 2 == 0:
                    next_match.team1 = self.team2
                else:
                    next_match.team2 = self.team2
            next_match.save()
            next_match.advance_winner()

    def next_match(self):
        total_rounds = int(math.log(config.NUMBER_OF_TEAMS, 2))
        rounds_left = int(math.log(config.NUMBER_OF_TEAMS - self.id - 1, 2))
        offset = int((self.id - config.NUMBER_OF_TEAMS + 2**(rounds_left + 1)))
        print(offset)
        round_diff = 2**rounds_left
        next_match_id = (self.id - offset) + round_diff + int(offset/2)
        return Match.objects.get(number=next_match_id)

def null_team():
    return Team.objects.get(number=-1)

def blank_team(id, team_size):
    blank_team = Team(id=id, names=["" for i in range(team_size)])
    blank_team.save()
    return blank_team

def init(num_of_teams, team_size, start_time, time_diff):
    if len(Team.objects) >= num_of_teams:
        return
    null_team = Team(id=-1, names=["" for i in range(team_size)])
    null_team.save()
    start = start_time
    for i in range(int(num_of_teams/2)):
        new_match = Match(id=i, team1=blank_team(i*2, team_size), team2=blank_team(i*2+1, team_size), time=start)
        new_match.save()
        start = start + time_diff
    for i in range(int(num_of_teams/2), num_of_teams-1):
        new_match = Match(id=i, team1=null_team, team2=null_team, time=start)
        new_match.save()
        start = start + time_diff

def get_all_matches():
    return Match.objects.order_by('id')

def get_all_teams():
    return Team.objects.filter(number__ne=-1).order_by('id')

def get_team(id):
    return Team.objects.get(number=id)

def get_match(id):
    return Match.objects.get(number=id)


