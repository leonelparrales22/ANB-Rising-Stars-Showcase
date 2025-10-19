from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import timedelta

from shared.config.settings import settings
from shared.db.models.user import User
from shared.db.config import get_db

from ..schemas.auth_schemas import UserCreate, UserLogin
from ..core.security import get_password_hash, verify_password, create_access_token

import uuid

router = APIRouter()


@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    if user.password1 != user.password2:
        raise HTTPException(
            status_code=400,
            detail={"message": "Error de validación (email duplicado, contraseñas no coinciden)."},
        )
    # Verificar si el email ya existe
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail={"message": "Error de validación (email duplicado, contraseñas no coinciden)."},
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
    return JSONResponse(
        status_code=201, content={"message": "Usuario creado exitosamente."}
    )


@router.post("/login", response_model=dict)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail={"message": "Credenciales inválidas."})
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": int(access_token_expires.total_seconds()),
    }
