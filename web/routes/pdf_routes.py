"""PDF document routes — upload, render, text, download."""

import io
import os
from flask import Blueprint, request, jsonify, send_file, send_from_directory, abort

from web.config import ALLOWED_EXTENSIONS
from web.services import pdf_service

pdf_bp = Blueprint("pdf", __name__, url_prefix="/api")


@pdf_bp.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify(error="No file provided"), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify(error="Empty filename"), 400

    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify(error=f"Unsupported file type: {ext}"), 400

    try:
        info = pdf_service.upload_pdf(f)
        return jsonify(info), 201
    except Exception as e:
        return jsonify(error=str(e)), 500


@pdf_bp.route("/documents", methods=["GET"])
def list_documents():
    return jsonify(pdf_service.list_documents())


@pdf_bp.route("/documents/<doc_id>", methods=["GET"])
def document_info(doc_id):
    try:
        return jsonify(pdf_service.get_info(doc_id))
    except KeyError:
        abort(404)


@pdf_bp.route("/documents/<doc_id>/page/<int:page_num>", methods=["GET"])
def render_page(doc_id, page_num):
    zoom = request.args.get("zoom", 1.0, type=float)
    try:
        jpeg_bytes = pdf_service.render_page_jpeg(doc_id, page_num, zoom)
        return send_file(
            io.BytesIO(jpeg_bytes),
            mimetype="image/jpeg",
            download_name=f"page_{page_num}.jpg",
        )
    except KeyError:
        abort(404)
    except IndexError:
        return jsonify(error="Page number out of range"), 400


@pdf_bp.route("/documents/<doc_id>/text/<int:page_num>", methods=["GET"])
def page_text(doc_id, page_num):
    try:
        text = pdf_service.extract_text(doc_id, page_num)
        return jsonify(page=page_num, text=text)
    except KeyError:
        abort(404)
    except IndexError:
        return jsonify(error="Page number out of range"), 400


@pdf_bp.route("/documents/<doc_id>/text", methods=["GET"])
def all_text(doc_id):
    try:
        text = pdf_service.extract_all_text(doc_id)
        return jsonify(text=text)
    except KeyError:
        abort(404)


@pdf_bp.route("/documents/<doc_id>/download", methods=["GET"])
def download(doc_id):
    try:
        filepath, filename = pdf_service.get_download_path(doc_id)
        return send_file(filepath, as_attachment=True, download_name=filename)
    except KeyError:
        abort(404)


@pdf_bp.route("/documents/<doc_id>/ocr", methods=["POST"])
def ocr_document(doc_id):
    data = request.get_json(silent=True) or {}
    language = data.get("language", "eng")
    try:
        info = pdf_service.do_ocr(doc_id, language)
        return jsonify(info)
    except KeyError:
        abort(404)
    except RuntimeError as e:
        return jsonify(error=str(e)), 500


@pdf_bp.route("/ocr", methods=["POST"])
def ocr_oneshot():
    """Upload a PDF, OCR it, return the OCR'd file directly.

    Designed for the browser extension: POST the captured PDF,
    get back a searchable PDF. No document registry state.
    """
    if "file" not in request.files:
        return jsonify(error="No file provided"), 400

    f = request.files["file"]
    language = request.form.get("language", "eng")

    try:
        ocr_path, ocr_filename = pdf_service.ocr_oneshot(f, language)
        response = send_file(
            ocr_path, as_attachment=True, download_name=ocr_filename
        )
        # Clean up temp file after send
        @response.call_on_close
        def _cleanup():
            if os.path.exists(ocr_path):
                os.unlink(ocr_path)
        return response
    except RuntimeError as e:
        return jsonify(error=str(e)), 500


@pdf_bp.route("/documents/<doc_id>", methods=["DELETE"])
def close_doc(doc_id):
    pdf_service.close_document(doc_id)
    return jsonify(ok=True)
