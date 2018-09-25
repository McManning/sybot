
import os
import logging
import sys
from distutils.util import strtobool

# Import isn't used here, but it needs to happen before zeroc-ice
# is every imported, otherwise we get segfaults on https requests.
# (Still unsolved as to why - may need to open a ticket with zeroc-ice)
import requests

from flask import Flask
from app.api import api
from app.murmur import murmur_connect

def main(args=None):
    app = Flask(__name__)

    debug = strtobool(os.environ.get('DEBUG', '0'))
    log_level = logging.DEBUG if debug else logging.INFO

    # Configure application logging
    file_formatter = logging.Formatter("%(asctime)s | %(pathname)s:%(lineno)d | %(funcName)s | %(levelname)s | %(message)s ")
    file_handler = logging.FileHandler('output.log')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)

    stdout_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_handler.setFormatter(stdout_formatter)

    app.logger.setLevel(log_level)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(stdout_handler)

    # Add Werkzeug log messages as well
    werkz_log = logging.getLogger('werkzeug')
    werkz_log.setLevel(log_level)
    werkz_log.addHandler(file_handler)
    werkz_log.addHandler(stdout_handler)

    # Register routes
    app.register_blueprint(api)

    # Open an Ice channel to Murmur
    logger = logging.getLogger('murmur')
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

    murmur_connect(logger)

    # Start web service
    app.run(host='::', debug=debug)

if __name__ == '__main__':
    main()
