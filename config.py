from datetime import datetime, timedelta
import helper

DEBUG = True
SECRET_KEY = "AkduHivuYkUGVBdjv879JGdhbDVsfaSRfEDdfHFsdfsV"
TWITCH_STREAM = "https://www.twitch.tv/streamer_name"
NUMBER_OF_TEAMS = 32
NUMBER_OF_PLAYERS = 1
SINGLE_ELIMINATION = True
NAME = "Test Tournament"
DB_NAME = "mongoengine_test"
PASSWORD = "password"
START_TIME = datetime(2017, 1, 1, 12, 0, 0)
TIME_PER_MATCH = timedelta(minutes=10)
TIMEZONE_ABBR = "EDT"
DATE_STRING = helper.custom_strftime('%B {S}, %Y', START_TIME)
VIDEO_SERVER_ADDRESS = ""
VIDEO_SERVER_CREDENTIAL = ""
