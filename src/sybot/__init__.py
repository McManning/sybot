
from flask import Flask, render_template
from sybot.mumble.routes import mumble as mumble_blueprint

# Setup instance of a Flask app
app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

# Register blueprint routes
app.register_blueprint(mumble_blueprint)

# Setup instance of a Mumble Ice interface
# Late import is necessary to use app in MumbleInterface context
from sybot.mumble.interfaces import MumbleInterface
mumble = MumbleInterface()
