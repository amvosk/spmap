# Usage

1. Install nginx and run it
2. Copy "eloq.conf" config to the .../etc/nginx/servers location.
```shell
$ make copy-nginx-config
$ make nginx-test
$ make nginx-reload
```
3. Prepare python environment
```shell
$ python -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```
4. Set ELOQ_TOKEN env variable for the synchronization with the ELoQ app. (or hardcode it in the "settings.py" file)
```shell
$ export ELOQ_TOKEN=YOUR_SECRET_HERE
```
5. Start python server
```shell
$ make run-debug
uvicorn server:app
INFO:     Started server process [19023]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```


# Communication

Server <-websocket-> Client 


Message
action: str
data: str (json encoded) OR null


There are different commands for different examination types.