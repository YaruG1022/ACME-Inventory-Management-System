from functools import wraps

from flask import jsonify, request


def json_object():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object.")
    return data


def validation_errors(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except ValueError as error:
            return jsonify(message=str(error)), 400

    return wrapped
