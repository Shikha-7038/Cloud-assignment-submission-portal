"""
Central error handling: every route can just `raise BadRequest(...)` etc, and
this turns it into a consistent JSON body with the right HTTP status code.
Unexpected exceptions (bugs, a down database, a storage outage) are caught
too, logged with full detail server-side, and returned to the client as a
generic 500 - so internal errors/stack traces are never leaked to the browser.
"""
import logging

from flask import jsonify

from backend.utils.errors import AppError

logger = logging.getLogger("portal.errors")


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err: AppError):
        body = {"error": {"code": err.code, "message": err.message}}
        if err.details is not None:
            body["error"]["details"] = err.details
        return jsonify(body), err.status_code

    @app.errorhandler(404)
    def handle_404(_err):
        return jsonify({"error": {"code": "NOT_FOUND", "message": "This endpoint does not exist."}}), 404

    @app.errorhandler(405)
    def handle_405(_err):
        return jsonify({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed on this endpoint."}}), 405

    @app.errorhandler(Exception)
    def handle_unexpected(err: Exception):
        # This is exactly where a "database is temporarily unavailable" or
        # "storage service failed" exception lands if a lower layer couldn't
        # already turn it into a friendlier AppError.
        logger.exception("Unhandled server error")
        return jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Something went wrong on our end. Please try again shortly.",
            }
        }), 500
