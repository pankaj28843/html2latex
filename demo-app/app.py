"""HTML2LaTeX Demo App - Flask application with Redis caching."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

import redis
from flask import Blueprint, Flask, current_app, jsonify, render_template, request

from html2latex import html2latex

if TYPE_CHECKING:
    from flask import Response
    from werkzeug.exceptions import HTTPException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Blueprint for API routes
api = Blueprint("api", __name__)


def create_app(config: dict | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config: Optional configuration dictionary to override defaults.

    Returns:
        Configured Flask application instance.
    """
    base_dir = Path(__file__).resolve().parent
    app = Flask(__name__, template_folder=str(base_dir / "templates"))

    # Load configuration
    app.config.update(
        ENV=os.environ.get("ENV", "production").lower().strip(),
        REDIS_HOST=os.environ.get("REDIS_HOST", "localhost"),
        REDIS_PORT=int(os.environ.get("REDIS_PORT", "6379")),
        REDIS_DB=int(os.environ.get("REDIS_DB", "0")),
        CACHE_ENABLED=os.environ.get("CACHE_ENABLED", "False").lower().strip() == "true",
        CACHE_KEY_SECRET=os.environ.get("CACHE_KEY_SECRET", "html2latex-demo"),
    )
    app.config["DEBUG"] = app.config["ENV"] != "production"

    # Apply custom configuration
    if config:
        app.config.update(config)

    # Initialize Redis
    app.redis = redis.Redis(
        host=app.config["REDIS_HOST"],
        port=app.config["REDIS_PORT"],
        db=app.config["REDIS_DB"],
        decode_responses=True,
    )

    # Register blueprints
    app.register_blueprint(api)

    # Register error handlers
    _register_error_handlers(app)

    return app


def _register_error_handlers(app: Flask) -> None:
    """Register error handlers for the application."""

    @app.errorhandler(400)
    def bad_request(error: HTTPException) -> tuple[Response, int]:
        return jsonify({"error": "Bad request", "message": str(error.description)}), 400

    @app.errorhandler(404)
    def not_found(error: HTTPException) -> tuple[Response, int]:
        return jsonify({"error": "Not found", "message": str(error.description)}), 404

    @app.errorhandler(500)
    def internal_error(error: HTTPException) -> tuple[Response, int]:
        logger.exception("Internal server error")
        return jsonify({"error": "Internal server error"}), 500


def _cache_key_for_html(html_string: str, secret: str) -> str:
    """Generate a cache key for the given HTML string."""
    digest = hmac.new(
        secret.encode("utf-8"),
        html_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"demo_app:{digest}"


@api.route("/", methods=["GET"])
def index() -> str:
    """Serve the main HTML page with the rich text editor.

    Returns:
        Rendered index.html template.
    """
    return render_template("index.html")


@api.route("/convert", methods=["POST"])
def convert_html() -> tuple[Response, int] | Response:
    """Convert HTML to LaTeX.

    Request body:
        {"html_string": "<p>some HTML</p>..."}

    Returns:
        JSON response with converted LaTeX or error message.
    """
    data = request.get_json(silent=True)
    if not data or "html_string" not in data:
        return jsonify({"error": "Missing html_string field"}), 400

    html_string = data["html_string"]

    if not current_app.config["CACHE_ENABLED"]:
        try:
            latex_result = html2latex(html_string)
        except Exception:
            logger.exception("Error converting HTML to LaTeX")
            return jsonify({"error": "Error converting HTML to LaTeX"}), 500
        return jsonify({"latex": latex_result})

    # Check cache first
    key = _cache_key_for_html(html_string, current_app.config["CACHE_KEY_SECRET"])
    try:
        cached_data = current_app.redis.get(key)
        if cached_data is not None:
            return jsonify({"latex": cached_data})
    except redis.RedisError:
        logger.warning("Redis cache read failed, proceeding without cache")

    # Convert HTML to LaTeX
    try:
        latex_result = html2latex(html_string)
    except Exception:
        logger.exception("Error converting HTML to LaTeX")
        return jsonify({"error": "Error converting HTML to LaTeX"}), 500

    # Store in cache (best effort)
    try:
        current_app.redis.set(key, latex_result)
    except redis.RedisError:
        logger.warning("Redis cache write failed")

    return jsonify({"latex": latex_result})


# Create the application instance for direct execution
app = create_app()

if __name__ == "__main__":
    # Binding to 0.0.0.0 is intentional for Docker container access
    app.run(host="0.0.0.0", port=15005, debug=app.config["DEBUG"])  # noqa: S104
