from __future__ import annotations

from dotenv import load_dotenv
from flask import Flask

from app.api import routes
from app.config.config import config

load_dotenv()


def create_app():
    flask_app = Flask(__name__)

    # Import and register API routes
    routes.register_routes(flask_app)

    return flask_app


if __name__ == "__main__":
    app = create_app()
    port = config.port
    print(f"Starting app on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=config.debug)
