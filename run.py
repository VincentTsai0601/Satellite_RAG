"""Interactive local launcher. Close this console or press Ctrl+C to stop."""
import json
import socket
import threading
import time
import urllib.error
import urllib.request
import webbrowser

import uvicorn

URL = 'http://127.0.0.1:8765'


def already_running():
    try:
        with urllib.request.urlopen(URL + '/api/status', timeout=2) as response:
            return json.load(response).get('title') == 'MSS Reference Architecture'
    except (OSError, ValueError):
        return False


def open_when_ready():
    for _ in range(30):
        if already_running():
            webbrowser.open(URL)
            return
        time.sleep(.5)
    print('Browser did not open automatically. Visit ' + URL)


if __name__ == '__main__':
    if already_running():
        print('Orbit is already running. Opening your browser.')
        webbrowser.open(URL)
    else:
        print('Orbit - Satellite Learning\nOpen ' + URL + '\nKeep this window open. Press Ctrl+C to stop.')
        threading.Thread(target=open_when_ready, daemon=True).start()
        uvicorn.run('satellite.app:create_app', factory=True, host='127.0.0.1', port=8765)
