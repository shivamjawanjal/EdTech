import hashlib
import bcrypt


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt with standard work factor."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def hash_token(token: str) -> str:
    """
    Hash a high-entropy secret token (such as a refresh token or session token)
    using SHA-256 before persisting it to the database.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
