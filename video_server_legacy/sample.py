from livestreamer import Livestreamer
import os
import time
import upload

session = Livestreamer()
headers = {}
headers['Client-ID']='jzkbprff40iqj646a697cyrvl0zt2m6'
session.set_option('http-headers',headers)
data_filename = "video.dat"
video_filename = "video.mp4"
streams = session.streams('http://twitch.tv/touchyourtoes_')
stream = streams['best']
empty = True
t_end = time.time() + 60
with stream.open() as fd:
    print(fd.timeout)
    fd.timeout = 15.0
    with open(data_filename, "wb") as f:
        while True and time.time() < t_end:
            data = fd.read(65536)
            f.write(data)
            empty = False

if empty:
    return ""

subprocess.call(['ffmpeg', '-err_detect', 'ignore_err', '-i', data_filename, '-c', 'copy', video_filename])





