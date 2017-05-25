# Tournament Bracket Manager

This tool allows you to have a live updated tournament bracket that can also record and show videos from a twitch stream.

## Setting up

Make sure you are running with python3. This project was built without any plans to support anything less than python 3, and will not be adapted to do so in the future.

Start by running `pip install -r piplist.txt` to ensure that you have all of the relevant dependencies. Make sure to update the relevant settings in config.py to values that you would like them to be. Then you should be able to run the start and stop scripts in order to start and stop the server.

For video server, it should give you some instructions on how to obtain a client_secrets.json file in order to facilitate the youtube upload. Follow the instructions that it gives you.

## Running in Development

For development settings you can run the servers without the start and stop scripts by using `python tournament.py` or `python video_server.py`.
