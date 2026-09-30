"""Application errors. Every AppError becomes a clean JSON response:
{"error": {"code": "...", "message": "...", "details": ...}}"""


class AppError(Exception):
    status_code = 400
    code = "BAD_REQUEST"

    def __init__(self, message: str, code: str | None = None, details=None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.details = details


class BadRequest(AppError):
    status_code = 400


class Unauthorized(AppError):
    status_code = 401
    code = "UNAUTHORIZED"


class Forbidden(AppError):
    status_code = 403
    code = "FORBIDDEN"


class NotFound(AppError):
    status_code = 404
    code = "NOT_FOUND"


class Conflict(AppError):
    status_code = 409
    code = "CONFLICT"


class PayloadTooLarge(AppError):
    status_code = 413
    code = "FILE_TOO_LARGE"


class UnsupportedMedia(AppError):
    status_code = 415
    code = "INVALID_FILE_TYPE"


class TooManyRequests(AppError):
    status_code = 429
    code = "RATE_LIMITED"
