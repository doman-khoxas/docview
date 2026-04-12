"""DocView Web — Flask application factory."""

import os
import sys

# Add project root to path so `app.core.*` imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, redirect, url_for
from flask_cors import CORS

from web.config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH
from web.routes.pdf_routes import pdf_bp
from web.routes.page_routes import page_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    CORS(app)

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    app.register_blueprint(pdf_bp)
    app.register_blueprint(page_bp)

    # Viewer routes (serve HTML templates)
    from flask import render_template

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/viewer/<doc_id>")
    def viewer(doc_id):
        return render_template("viewer.html", doc_id=doc_id)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="127.0.0.1", port=5000)
