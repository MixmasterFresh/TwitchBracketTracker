gunicorn --bind 0.0.0.0:8080 start:app --capture-output --log-file log/gunicorn.log -p tournament.pid -D
