from datetime import date


def required_text(value, label, max_length=255):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required.")
    value = value.strip()
    if len(value) > max_length:
        raise ValueError(f"{label} must be at most {max_length} characters.")
    return value


def integer(value, label, minimum=1):
    if isinstance(value, bool) or not str(value).isascii() or not str(value).isdigit():
        raise ValueError(f"{label} must be a whole number of at least {minimum}.")
    result = int(value)
    if result < minimum:
        raise ValueError(f"{label} must be at least {minimum}.")
    return result


def parse_date(value, label):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a valid date.") from None
