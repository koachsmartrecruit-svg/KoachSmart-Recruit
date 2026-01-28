ALLOWED_FILE_TYPES = {"pdf", "jpg", "jpeg", "png"}


def is_allowed_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False

    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_FILE_TYPES
