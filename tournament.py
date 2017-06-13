from flask import Flask, Response, redirect, url_for, request, session, abort, render_template, send_from_directory, make_response
from flask import g, after_this_request
from functools import wraps
from flask_cache import Cache
import urllib.request as urllib2
from datetime import datetime, timedelta

import json
import gzip
import db
import helper
import config

app = Flask(__name__)

# config
app.config.update(
    DEBUG=config.DEBUG,
    SECRET_KEY=config.SECRET_KEY
)

# from flask.ext.profile import Profiler
# Profiler(app)

app.config['CACHE_TYPE'] = 'simple'

app.cache = Cache(app)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

db.init(config.NUMBER_OF_TEAMS, config.NUMBER_OF_PLAYERS, config.START_TIME, config.TIME_PER_MATCH)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if ('found' in request.cookies) and (request.cookies['found'] == db.cookie_value()):
            return f(*args, **kwargs)
        return redirect('/login')
    return decorated


def cache_resource(time):
    def cr(view):
        @wraps(view)
        def no_cache(*args, **kwargs):
            response = make_response(view(*args, **kwargs))
            response.headers['Cache-Control'] = 'public, max-age=' + str(time)
            return response
        return no_cache
    return cr

def gzipped(view):
    @wraps(view)
    def zipper(*args, **kwargs):
        accept_encoding = request.headers.get('Accept-Encoding', '')
        response = make_response(view(*args, **kwargs))
        if 'gzip' not in accept_encoding.lower():
            return response

        response.direct_passthrough = False

        if (response.status_code < 200 or
            response.status_code >= 300 or
            'Content-Encoding' in response.headers):
            return response

        response.data = gzip.compress(response.data)
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Vary'] = 'Accept-Encoding'
        response.headers['Content-Length'] = len(response.data)

        return response
    return zipper

# some protected url
@app.route('/')
@app.cache.cached(timeout=20)
@gzipped
def home():
    return render_template('bracket.html', config=config, matches=db.get_all_matches(), editable=False, admin=False)

# somewhere to login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == config.PASSWORD:
            redirect_to_index = redirect('/admin')
            response = make_response(redirect_to_index )
            response.set_cookie('found',value=db.cookie_value())
            return response
        else:
            return redirect('/login')
    else:
        if ('found' in request.cookies) and (request.cookies['found'] == db.cookie_value()):
            return redirect('/admin')
        else:
            return render_template("login.html", config=config)

@app.route("/admin")
@login_required
@gzipped
def admin():
    return render_template('bracket.html', config=config, matches=db.get_all_matches(), editable=True, admin=True, form_target="/admin/set_teams")

@app.route("/admin/preview")
@login_required
@gzipped
def preview():
    return render_template('bracket.html', config=config, matches=db.get_all_matches(), editable=False, admin=True)


@app.route("/admin/set_teams", methods=["POST"])
@login_required
def set_teams():
    teams = db.get_all_teams()
    for i in range(config.NUMBER_OF_TEAMS):
        team = teams[i]
        names = team.names[:]
        for j in range(config.NUMBER_OF_PLAYERS):
            names[j] = request.form["team"+str(i)+"player"+str(j)]
        team.names = names
    db.session.commit()
    return "Success"

@app.route("/admin/delay_matches", methods=["POST"])
@login_required
def delay_matches():
    delta = int(request.form["minutes"])
    db.delay_matches(delta)
    return "Success"

@app.route("/admin/switch_matches", methods=["POST"])
@login_required
def swap_matches():
    match1_number = int(request.form["match1"]) - 1
    match2_number = int(request.form["match2"]) - 1


    if match1_number >= int(config.NUMBER_OF_TEAMS/2) or match2_number >= int(config.NUMBER_OF_TEAMS/2):
        return "Both matches must take place in the first round to be swapped.", 400
    elif match1_number < 0 or match2_number < 0:
        return "No negative or zero matches", 400
    elif match1_number == match2_number:
        return "Success"

    match1 = db.get_match(match1_number)
    match2 = db.get_match(match2_number)
    if match1.live or match2.live or match1.video_pending or match2.video_pending:
        return "Neither match can be live or awaiting video when swapping.", 400

    match1.number = match2_number
    match2.number = match1_number
    temp_time = match1.time
    match1.time = match2.time
    match2.time = temp_time
    db.session.commit()
    match1.advance_winner()
    match2.advance_winner()
    return "Success"

@app.route("/admin/switch_match_times", methods=["POST"])
@login_required
def swap_match_times():
    match1_number = int(request.form["match1"]) - 1
    match2_number = int(request.form["match2"]) - 1

    if match1_number >= int(config.NUMBER_OF_TEAMS - 1) or match2_number >= int(config.NUMBER_OF_TEAMS - 1):
        return "Both matches must be valid match indexes.", 400
    elif match1_number < 0 or match2_number < 0:
        return "No negative or zero matches", 400
    elif match1_number == match2_number:
        return "Success"

    match1 = db.get_match(match1_number)
    match2 = db.get_match(match2_number)
    temp_time = match1.time
    match1.time = match2.time
    match2.time = temp_time
    db.session.commit()
    return "Success"

@app.route("/admin/settings")
@login_required
def get_settings():
    return render_template("settings.html", config=config, form_target="/admin/delay_matches", admin=True, editable=False)

@app.route("/admin/match/<number>", methods=["GET", "POST"])
@login_required
def match(number):
    if request.method == 'POST':
        try:
            match = db.get_match(number)
            old_winner = match.winner
            match.winner = 0
            if "team1-wins" in request.form:
                match.winner = 1
            elif "team2-wins" in request.form:
                match.winner = 2

            match.team1_score = request.form['team1-score']
            match.team2_score = request.form['team2-score']

            minutes = int(request.form['minutes'])

            if minutes != 0:
                diff = timedelta(minutes=minutes)
                match.time = match.time + diff

            if old_winner != match.winner:
                db.session.commit()
                match.advance_winner()
            else:
                db.session.commit()

            return "Success"
        except ValueError:
            return "Failure", 500
    else:
        try:
            return render_template("edit_match.html", match=db.get_match(int(number)), config=config, form_target=("/admin/match/" + str(number)))
        except ValueError:
            return abort(401)

@app.route("/admin/start_recording/<number>")
@login_required
def start_recording(number):
    match = db.get_match(number)
    if match.live:
        return "Already Recording", 500
    elif match.video != "":
        return "Recording Already Exists", 500
    elif match.video_pending:
        return "Video Processing"

    description = ""
    for player in match.team1.names:
        description += player + "\n"

    description += "vs.\n"

    for player in match.team2.names:
        description += player + "\n"

    data = {
        'title': config.NAME + ' Tournament: Match ' + str(match.number + 1),
        'description': description,
        'tournament_name': config.NAME + " Tournament",
        'stream': config.TWITCH_STREAM,
        'auth': config.VIDEO_SERVER_CREDENTIAL,
        'return_url': request.url_root + 'admin/video/' + str(match.number)
    }
    req = urllib2.Request(config.VIDEO_SERVER_ADDRESS + '/start')
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req, json.dumps(data).encode('utf-8'))

    json_data = json.loads(response.read().decode('utf-8'))

    match.key = json_data['key']
    match.live = True;
    db.session.commit()
    return "Success"

@app.route("/admin/stop_recording/<number>")
@login_required
def stop_recording(number):
    match = db.get_match(number)
    if (not match.live):
        return "Not Recording", 500

    data = {'id': match.key, 'auth': config.VIDEO_SERVER_CREDENTIAL}
    req = urllib2.Request(config.VIDEO_SERVER_ADDRESS + '/stop')
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req, json.dumps(data).encode('utf-8'))

    match.live = False
    match.video_pending = True
    db.session.commit()
    return "Success"

@app.route("/admin/video/<number>", methods=['POST'])
def register_video(number):
    try:
        #get various parameters
        match = db.get_match(number)
        json_dict = request.get_json()

        if json_dict['key'] == match.key:
            match.video = json_dict['video']
            match.key = ""
            match.live = False
            match.video_pending = False
            db.session.commit()

        return "Success"
    except ValueError:
        return "Failure", 500

@app.route("/admin/delete_video/<number>")
@login_required
def delete_video(number):
    try:
        #get various parameters
        match = db.get_match(number)
        if match.video == "":
            return "No video is currently on file.\nIf you were expecting one perhaps it is still processing.\nIn that case it should be around shortly.", 500
        match.video = ""
        db.session.commit()
        return "Success"
    except ValueError:
        return "Failure", 500


# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return 'Not Found', 401

@app.errorhandler(404)
def page_not_found(e):
    return 'Hey, Come on... Don\'t wander too far...', 404


@app.route('/js/<path:path>')
@cache_resource(100000)
@gzipped
def send_js(path):
    return send_from_directory('js', path)

@app.route('/css/<path:path>')
@cache_resource(100000)
@gzipped
def send_css(path):
    return send_from_directory('css', path)

@app.route('/images/<path:path>')
@cache_resource(100000)
@gzipped
def send_image(path):
    return send_from_directory('images', path)

if __name__ == "__main__":
    app.jinja_env.cache = {}
    app.run(host='0.0.0.0', port=8080)
