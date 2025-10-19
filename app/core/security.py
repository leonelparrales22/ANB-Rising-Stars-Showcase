from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from shared.config.settings import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')


def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_email: str = payload.get('sub')
        if user_email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail={'message': 'Credenciales de autenticación inválidas.'},
                                headers={'WWW-Authenticate': 'Bearer'})
        return user_email
    except JWTError as ex:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={'message': 'Credenciales de autenticación inválidas.'},
                            headers={'WWW-Authenticate': 'Bearer'})
