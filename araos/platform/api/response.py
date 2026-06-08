"""Standardized API response helpers — Week 11D."""
from flask import jsonify
from datetime import datetime, timezone
from uuid import uuid4


def success_response(data=None, meta=None, status=200):
    envelope = {
        "success": True,
        "data": data,
        "error": None,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": str(uuid4()),
            **(meta or {}),
        },
    }
    return jsonify(envelope), status


def error_response(code, message, status=400, details=None):
    envelope = {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": str(uuid4()),
        },
    }
    return jsonify(envelope), status
