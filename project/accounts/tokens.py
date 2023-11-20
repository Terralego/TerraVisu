import secrets


def generate_token():
    return secrets.token_urlsafe(32)
