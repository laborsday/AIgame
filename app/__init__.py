"""Gomoku web application factory."""
import os
import secrets

from flask import Flask


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Generate a random secret key for session signing
    app.secret_key = secrets.token_hex(32)

    # Register routes
    from app.routes import bp

    app.register_blueprint(bp)

    return app
