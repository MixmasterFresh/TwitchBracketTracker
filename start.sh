gunicorn --bind 127.0.0.1:8080 start:app --capture-output --log-file log/gunicorn.log -p tournament.pid -D
