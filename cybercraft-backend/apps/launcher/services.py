import hashlib


def sha256_file(file):
    h = hashlib.sha256()
    for chunk in file.chunks():
        h.update(chunk)
    return h.hexdigest()
