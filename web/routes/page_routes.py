"""Page manipulation routes — rotate, delete, reorder, merge."""

from flask import Blueprint, request, jsonify, abort

from web.services import pdf_service

page_bp = Blueprint("pages", __name__, url_prefix="/api")


@page_bp.route("/documents/<doc_id>/rotate", methods=["POST"])
def rotate(doc_id):
    data = request.get_json(silent=True) or {}
    page = data.get("page")
    angle = data.get("angle", 90)

    if page is None:
        return jsonify(error="'page' is required"), 400

    try:
        pages = pdf_service.do_rotate(doc_id, int(page), int(angle))
        return jsonify(ok=True, pages=pages)
    except KeyError:
        abort(404)
    except IndexError:
        return jsonify(error="Page number out of range"), 400


@page_bp.route("/documents/<doc_id>/delete-pages", methods=["POST"])
def delete_pages_route(doc_id):
    data = request.get_json(silent=True) or {}
    page_nums = data.get("pages")

    if not page_nums or not isinstance(page_nums, list):
        return jsonify(error="'pages' array is required"), 400

    try:
        pages = pdf_service.do_delete(doc_id, [int(p) for p in page_nums])
        return jsonify(ok=True, pages=pages)
    except KeyError:
        abort(404)
    except IndexError:
        return jsonify(error="Page number out of range"), 400


@page_bp.route("/documents/<doc_id>/reorder", methods=["POST"])
def reorder(doc_id):
    data = request.get_json(silent=True) or {}
    order = data.get("order")

    if not order or not isinstance(order, list):
        return jsonify(error="'order' array is required"), 400

    try:
        pages = pdf_service.do_reorder(doc_id, [int(p) for p in order])
        return jsonify(ok=True, pages=pages)
    except KeyError:
        abort(404)


@page_bp.route("/merge", methods=["POST"])
def merge():
    data = request.get_json(silent=True) or {}
    doc_ids = data.get("doc_ids")

    if not doc_ids or not isinstance(doc_ids, list) or len(doc_ids) < 2:
        return jsonify(error="'doc_ids' array with at least 2 IDs required"), 400

    try:
        info = pdf_service.do_merge(doc_ids)
        return jsonify(info), 201
    except KeyError as e:
        return jsonify(error=str(e)), 404
