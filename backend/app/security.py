# app/security.py
import secrets
from passlib.context import CryptContext

# ✅ Seguro + estable en deploys + sin límite 72 bytes
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

def new_token(nbytes: int = 32) -> str:
    """
    Genera un token seguro para API keys, sesiones, dispositivos, etc.
    nbytes=32 -> token largo y seguro.
    """
    return secrets.token_urlsafe(nbytes)