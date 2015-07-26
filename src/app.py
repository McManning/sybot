
from sybot import app, mumble

if __name__ == '__main__':
    mumble.connect()
    app.run(use_reloader=False)
