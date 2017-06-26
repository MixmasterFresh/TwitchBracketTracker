import os
import upload

attrs = {}
attrs['title'] = "Testing"
attrs['description'] = "Some random description\nwith newlines"
attrs['file'] = "video.mp4"
attrs['tag'] = "Test Tournament"

video_id = upload.upload_video(attrs)
if video_id  == "":
    print("Video failed to upload.")
else:
    print("Video '{vid}' uploaded successfully.".format(vid=video_id))
