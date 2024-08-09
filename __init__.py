"""
Main entry point into the application.
"""
import os
import argparse
import logging

from src.app import App
from src.config import Config

from src.worker.redirect import HttpsRedirectWorker

logging.basicConfig(level=logging.INFO)

def parse_args():
    """
    Parses the command line arguments
    """
    parser = argparse.ArgumentParser(description="Kiosk Web Service")
    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()

    config = Config()
    app = App(config)

    if os.environ.get('WERKZEUG_RUN_MAIN') is None:
        redirect_worker = HttpsRedirectWorker()
        redirect_worker.run()

    app.run()
