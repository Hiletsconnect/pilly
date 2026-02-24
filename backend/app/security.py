# app/security.py
from passlib.context import CryptContext

# PBKDF2-SHA256: seguro, estable en deploys, sin límite de 72 bytes.
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)

def hash_password(password: str) -> str:
    if password is None:
        raise ValueError("Password is None")
    password = password.strip()
    if len(password) < 4:
        raise ValueError("Password demasiado corto (mínimo 4)")
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    if plain_password is None or password_hash is None:
        return False
    return pwd_context.verify(plain_password.strip(), password_hash)