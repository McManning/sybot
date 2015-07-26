# Import flask dependencies
from flask import Blueprint, request, render_template

# Define the blueprint: 'mumble', set its url prefix: app.url/mumble
mumble = Blueprint('mumble', __name__, url_prefix='/mumble')

@mumble.route('/', methods=['GET'])
def index():
    return render_template(
        'mumble/index.html'
    )

