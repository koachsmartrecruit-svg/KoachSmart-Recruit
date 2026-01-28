def is_non_empty(value) -> bool:
    return bool(value and str(value).strip())


def is_positive_number(value) -> bool:
    try:
        return float(value) > 0
    except Exception:
        return False
