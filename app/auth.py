from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .models import User
import os

# Argon2id zgodnie z OWASP: m=65536 (64 MiB), t=3, p=4 lub minimalne m=19456, t=2, p=1
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=4,
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, username: str, email: str, password: str) -> User:
    hashed = hash_password(password)
    user = User(username=username, email=email, password_hash=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Prosta lista popularnych haseł (do rozszerzenia)
COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123", "password123",
    "admin", "letmein", "welcome", "monkey", "dragon", "master", "login",
    "grzyb", "grzyby", "haslo", "hasło"
}

def is_common_password(password: str) -> bool:
    return password.lower() in COMMON_PASSWORDS or len(password) < 8
