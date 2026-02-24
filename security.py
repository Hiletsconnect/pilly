# security.py
import bcrypt

def hash_password(plain: str) -> str:
    if not plain or len(plain) < 8:
        raise ValueError("Password muy corta (min 8).")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False