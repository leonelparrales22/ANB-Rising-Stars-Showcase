from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..models.user import User
from ..core.security import get_password_hash, verify_password, create_access_token
from ..core.config import settings
from ..core.database import get_db
import uuid
from datetime import timedelta

router = APIRouter()


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password1: str
    password2: str
    city: str
    country: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    if user.password1 != user.password2:
        raise HTTPException(
            status_code=400,
            detail="Error de validación (email duplicado, contraseñas no coinciden).",
        )
    # Verificar si el email ya existe
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Error de validación (email duplicado, contraseñas no coinciden).",
        )
    hashed_password = get_password_hash(user.password1)
    new_user = User(
        id=str(uuid.uuid4()),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        city=user.city,
        country=user.country,
        password_hash=hashed_password,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return Response(
        status_code=201, content={"message": "Usuario creado exitosamente."}
    )


@router.post("/login", response_model=dict)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": int(access_token_expires.total_seconds()),
    }
