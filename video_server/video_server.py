from flask import Flask, Response, redirect, url_for, request, session, abort, render_template, send_from_directory, make_response
from flask import g
from concurrent.futures import ThreadPoolExecutor
from livestreamer import Livestreamer
import random
import os
import urllib.request as urllib2
import upload


procs = {}
executor = ThreadPoolExecutor(5)

app = Flask(__name__)

# config
app.config.update(
    DEBUG=True,
    SECRET_KEY="some_secret_key"
)

def set_proc(id, proc):
    procs[id] = proc

def set_status(id, status):
    procs[id].status = status

def get_status(id, status):
    procs[id].status

def make_random_key():
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(32))

def notify_tournament(attrs, video_id):
    data = {'video': video_id}
    req = urllib2.Request(attrs['return_url'])
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req, json.dumps(data))

def record(attrs):
    root_path = os.path.dirname(os.path.realpath(__file__))

    streams_path = os.path.join(root_path, "streams")
    videos_path = os.path.join(root_path, "videos")
    if(os.path.isdir(streams_path) is False):
        os.makedirs(streams_path)
    if(os.path.isdir(videos_path) is False):
        os.makedirs(videos_path)
    session = Livestreamer()
    headers = {}
    headers['Client-ID']='jzkbprff40iqj646a697cyrvl0zt2m6'
    session.set_option('http-headers',headers)
    data_filename = 'streams/' + attrs['title'].replace(" ", "") + ".dat"
    video_filename = 'videos/' + attrs['title'].replace(" ", "") + ".mp4"
    streams = session.streams(attrs['url'])
    stream = streams[list(streams.keys())[0]]
    if 'source' in streams.keys():
        stream = streams['source']
    elif 'best' in stream.keys():
        stream = streams['best']
    else:
        stream = streams['worst']

    empty = True
    t_end = time.time() + 60 * 10
    with stream.open() as fd:
        fd.timeout = 60.0
        with open(data_filename, "wb") as f:
            while get_status(attrs['id']) and time.time() < t_end:
                try:
                    data = fd.read(65536)
                    f.write(data)
                    empty = False
                except StreamError:
                    break
    if empty:
        return ""

    subprocess.call(['ffmpeg', '-err_detect', 'ignore_err', '-i', data_filename, '-c', 'copy', video_filename])
    os.remove(data_filename)
    attrs['file'] = video_filename
    video_id = upload.upload_video(attrs)
    if video_id  == "":
        print("Video {vid} failed to upload.".format(vid=video_filename))
    else:
        notify_tournament(attrs, video_id)
        os.remove(video_filename)



def start_recording(title, description, tournament_name, stream, return_url):
    attrs['id'] = make_random_key()
    attrs['title'] = title
    attrs['description'] = description
    attrs['tag'] = tournament_name
    attrs['url'] = stream
    attrs['return_url'] = return_url
    executor.submit(record, attrs)
    return attrs['id']

def stop_recording(id):
    set_status(id, False)
    return "success"

@app.route('/start', methods=["POST"])
def start():
    json_dict = request.get_json()
    proc_id = start_recording(
        json_dict['title'],
        json_dict['description'],
        json_dict['tournament_name'],
        json_dict['stream'],
        json_dict['return_url']
    )
    return jsonify({'key': proc_id})


@app.route('/stop', methods=["POST"])
def stop():
    json_dict = request.get_json()
    stop_recording(json_dict['id'])
    return "success"

if __name__ == "__main__":
    upload.authenticate()
    app.run(host='0.0.0.0', port=3000)
