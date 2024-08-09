"""
Flask application which redirects http traffic to https.
"""

import threading

from flask import Flask, redirect, request

class HttpsRedirectWorker:
    """
    A worker thread which redirects all http traffic to https.
    """

    def __init__(self):
        self.__worker = None

    def redirect(self):
        """
        Called by flask whenever a http request arrives
        """
        print(f"Got request from {request.host}{request.path}")

        # Redirect to HTTPS
        return redirect(f"https://{request.host}{request.path}", code=301)

    def run(self):
        """
        Runs the helper thread which redirects http requests to https
        """
        if self.__worker and self.__worker.is_alive():
            raise RuntimeError("Another thread is already running the application.")

        app = Flask(__name__)
        app.add_url_rule('/', view_func=self.redirect)
        app.add_url_rule('/<path:path>', view_func=self.redirect)

        self.__worker = threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 80})
        self.__worker.daemon = True
        self.__worker.start()
