from flask import Flask, Response, redirect, url_for, request, session, abort, render_template, send_from_directory, make_response
from flask import g
from functools import wraps
from flask_cache import Cache
import urllib.request as urllib2
import json
import db
import helper
import config

app = Flask(__name__)

# config
app.config.update(
    DEBUG=config.DEBUG,
    SECRET_KEY=config.SECRET_KEY
)
app.config['CACHE_TYPE'] = 'simple'

app.cache = Cache(app)

db.init(config.NUMBER_OF_TEAMS, config.NUMBER_OF_PLAYERS, config.START_TIME, config.TIME_PER_MATCH)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if ('found' in request.cookies) and (request.cookies['found'] == 'authenticated'):
            return f(*args, **kwargs)
        return redirect(url_for('login'))
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

# some protected url
@app.route('/')
@app.cache.cached(timeout=20)
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
            response.set_cookie('found',value='authenticated')
            return response
        else:
            return redirect(url_for('/login'))
    else:
        if ('found' in request.cookies) and (request.cookies['found'] == 'authenticated'):
            return redirect(url_for('/admin'))
        else:
            return render_template("login.html", config=config)

@app.route("/admin")
@login_required
def admin():
    return render_template('bracket.html', config=config, matches=db.get_all_matches(), editable=True, admin=True, form_target="/admin/set_teams")

@app.route("/admin/preview")
@login_required
def preview():
    return render_template('bracket.html', config=config, matches=db.get_all_matches(), editable=False, admin=True)


@app.route("/admin/set_teams", methods=["POST"])
@login_required
def set_teams():
    teams = db.get_all_teams()
    for i in range(config.NUMBER_OF_TEAMS):
        team = teams[i]
        for j in range(config.NUMBER_OF_PLAYERS):
            team.names[j] = request.form["team"+str(i)+"player"+str(j)]
        team.save()

    return "Success"

@app.route("/admin/match/<id>", methods=["GET", "POST"])
@login_required
def match(id):
    if request.method == 'POST':
        try:
            dirty = False
            match = db.get_match(id)
            old_winner = match.winner
            match.winner = 0
            if "team1-wins" in request.form:
                match.winner = 1
            elif "team2-wins" in request.form:
                match.winner = 2

            if request.form['team1-score'] != match.team1_score:
                match.team1_score = request.form['team1-score']
                dirty = True

            if request.form['team2-score'] != match.team2_score:
                match.team2_score = request.form['team2-score']
                dirty = True


            if old_winner != match.winner:
                match.save()
                match.advance_winner()
            elif dirty:
                match.save()
            return "Success"
        except ValueError:
            return "Failure", 500
    else:
        try:
            return render_template("edit_match.html", match=db.get_match(int(id)), config=config, form_target=("/admin/match/" + str(id)))
        except ValueError:
            return abort(401)

@app.route("/admin/start_recording/<id>")
@login_required
def start_recording(id):
    try:
        #get various parameters
        match = db.get_match(id)
        if match.live:
            return "Already Recording", 500
        elif match.video != "":
            return "Recording Already Exists", 500

        description = ""
        for player in match.team1.names:
            description += player + "\n"

        description += "vs.\n"

        for player in match.team2.names:
            description += player + "\n"

        data = {
            'title': config.NAME + ': Match ' + str(match.id + 1),
            'description': description,
            'tournament_name': config.NAME,
            'stream': config.TWITCH_STREAM,
            'auth': config.VIDEO_SERVER_CREDENTIAL,
            'return_url': request.url_root + 'admin/video/' + str(match.id)
        }
        req = urllib2.Request(config.VIDEO_SERVER_ADDRESS + '/start')
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req, json.dumps(data).encode('utf-8'))

        json_data = json.loads(response.read().decode('utf-8')) 
        
        match.key = json_data['key']
        match.live = True;
        match.save()
        return "Success"
    except ValueError:
        return "Failure", 500

@app.route("/admin/stop_recording/<id>")
@login_required
def stop_recording(id):
    try:
        #get various parameters
        match = db.get_match(id)
        if (not match.live):
            return "Not Recording", 500

        data = {'id': match.key, 'auth': config.VIDEO_SERVER_CREDENTIAL}
        req = urllib2.Request(config.VIDEO_SERVER_ADDRESS + '/stop')
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req, json.dumps(data).encode('utf-8'))

        match.live = False
        match.save()
        return "Success"
    except ValueError:
        return "Failure", 500

@app.route("/admin/video/<id>", methods=['POST'])
def register_video(id):
    try:
        #get various parameters
        match = db.get_match(id)
        json_dict = request.get_json()

        if json_dict['key'] == match.key:
            match.video = json_dict['video']
            match.key = ""
            match.save()

        return "Success"
    except ValueError:
        return "Failure", 500

@app.route("/admin/delete_video/<id>")
@login_required
def delete_video(id):
    try:
        #get various parameters
        match = db.get_match(id)
        match.video = ""
        match.save()
        return "Success"
    except ValueError:
        return "Failure"


# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return 'Not Found', 401

@app.errorhandler(404)
def page_not_found(e):
    return 'Hey, Come on... Don\'t wander too far...', 404


@app.route('/js/<path:path>')
@cache_resource(100000)
def send_js(path):
    return send_from_directory('js', path)

@app.route('/css/<path:path>')
@cache_resource(100000)
def send_css(path):
    return send_from_directory('css', path)

@app.route('/images/<path:path>')
@cache_resource(100000)
def send_image(path):
    return send_from_directory('images', path)

if __name__ == "__main__":
    app.jinja_env.cache = {}
    app.run(host='0.0.0.0', port=8080)
