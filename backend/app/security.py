from datetime import datetime, timedelta
import os

from jose import jwt, JWTError


# Read secret from .env
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "change-this-secret"
)


ALGORITHM = "HS256"


ACCESS_TOKEN_EXPIRE_MINUTES = 60



def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })


    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )



def decode_token(token: str):

    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

    except JWTError:
        return None