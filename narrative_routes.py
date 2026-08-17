"""
narrative_routes.py

Serves the scrollytelling narrative on the same Flask server as the Dash
app, instead of it being a separate site. The narrative itself is still
plain HTML/D3/Scrollama (not rewritten as Dash components - that would
be a much bigger, riskier rebuild of something that already works), but
now it's served from the same process and the same domain, so the whole
thing is genuinely one platform rather than a dashboard plus a link to
somewhere else.
"""

import os
from flask import send_from_directory
from app_instance import server

NARRATIVE_DIR = os.path.join(os.path.dirname(__file__), "narrative")


@server.route("/story")
def serve_narrative():
    return send_from_directory(NARRATIVE_DIR, "narrative.html")


@server.route("/story/<path:filename>")
def serve_narrative_assets(filename):
    # covers narrative_data.json, vendor/d3.min.js, vendor/scrollama.min.js
    # and the two screenshot images, all in the same narrative/ folder
    return send_from_directory(NARRATIVE_DIR, filename)
