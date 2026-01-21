import hashlib
import hmac
import os

import redis
from flask import Flask, request, jsonify, render_template

from html2latex.html2latex import html2latex

app = Flask(__name__)

redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = int(os.environ.get("REDIS_PORT", 6379))
redis_db = int(os.environ.get("REDIS_DB", 0))

cache = redis.Redis(
    host=redis_host,
    port=redis_port,
    db=redis_db,
    decode_responses=True,
)

capfirst_enabled = os.environ.get("CAPFIRST_ENABLED", "False").lower().strip() == "true"
cache_enabled = os.environ.get("CACHE_ENABLED", "False").lower().strip() == "true"

ENV = os.environ.get("ENV", "production").lower().strip()
DEBUG = ENV != "production"

CACHE_KEY_SECRET = os.environ.get("CACHE_KEY_SECRET", "html2latex-demo")


def cache_key_for_html(html_string):
    """Generate a cache key for the given HTML string."""
    key_source = f"{html_string}__capfirst_{capfirst_enabled}"
    digest = hmac.new(
        CACHE_KEY_SECRET.encode("utf-8"),
        key_source.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"demo_app:{digest}"


@app.route("/", methods=["GET"])
def index():
    """
    Serve a simple HTML page with a basic "rich" text area,
    math input, and a place to display the returned LaTeX
    using syntax highlighting.
    """

    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert_html():
    """
    POST endpoint that takes JSON:
      {
        "html_string": "<p>some HTML</p>..."
      }
    Returns a JSON response:
      {
        "latex": "converted latex string"
      }
    """
    data = request.get_json(silent=True)
    if not data or "html_string" not in data:
        return jsonify({"error": "Missing html_string field"}), 400

    html_string = data["html_string"]

    if not cache_enabled:
        try:
            latex_result = html2latex(html_string, CAPFIRST_ENABLED=capfirst_enabled)
        except Exception:
            return jsonify({"error": "Error converting HTML to LaTeX"}), 500
        return jsonify({"latex": latex_result})

    # First, check the cache
    key = cache_key_for_html(html_string)
    cached_data = cache.get(key)
    if cached_data:
        return jsonify({"latex": cached_data})

    # If not in cache, call the library (which no longer does its own caching)
    # Pass any env-based config (e.g. CAPFIRST_ENABLED) if relevant
    try:
        latex_result = html2latex(html_string, CAPFIRST_ENABLED=capfirst_enabled)
    except Exception:
        return jsonify({"error": "Error converting HTML to LaTeX"}), 500

    # Store in cache
    cache.set(key, latex_result)

    return jsonify({"latex": latex_result})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=15005, debug=DEBUG)
