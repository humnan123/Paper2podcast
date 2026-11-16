from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta

from app.security import create_access_token
from app.db import get_db
from app.models import User, Otp
from app.utils import generate_otp, hash_otp
from app.email_service import send_email


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ---------- Schemas ----------

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "author"


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    code: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str



# ---------- Register (2.1 + 2.2) ----------

@router.post("/register")
def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):

    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )


    role = user_data.role.lower().strip()

    if role not in ["author", "reviewer"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )


    hashed_password = pwd_context.hash(
        user_data.password
    )


    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_password,
        role=role,
        is_verified=False
    )


    db.add(new_user)
    db.commit()
    db.refresh(new_user)


    otp = generate_otp()

    otp_record = Otp(
        user_id=new_user.id,
        code_hash=hash_otp(otp),
        purpose="verify",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )


    db.add(otp_record)
    db.commit()


    send_email(
        new_user.email,
        "Verify your Paper CMS account",
        f"Your verification code is {otp}"
    )


    return {
        "message": "Registration successful. Verify your email.",
        "user_id": new_user.id,
        "email": new_user.email
    }



# ---------- Verify OTP (2.3) ----------

@router.post("/verify-otp")
def verify_otp(
    data: VerifyOtpRequest,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )


    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid email"
        )


    otp_record = (
        db.query(Otp)
        .filter(
            Otp.user_id == user.id,
            Otp.purpose == "verify",
            Otp.used == False
        )
        .order_by(Otp.created_at.desc())
        .first()
    )


    if not otp_record:
        raise HTTPException(
            status_code=400,
            detail="OTP not found"
        )


    if otp_record.attempts >= 5:
        raise HTTPException(
            status_code=400,
            detail="Too many attempts"
        )


    if otp_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="OTP expired"
        )


    if hash_otp(data.code) != otp_record.code_hash:

        otp_record.attempts += 1
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )


    otp_record.used = True
    user.is_verified = True

    db.commit()


    return {
        "message": "Email verified successfully"
    }



# ---------- Login (2.4) ----------

@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )


    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )


    if not pwd_context.verify(
        data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )


    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Email not verified"
        )


    token = create_access_token(
        {
            "id": user.id,
            "role": user.role
        }
    )


    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role
    }



# ---------- Forgot Password (2.5) ----------

@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )


    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    otp = generate_otp()


    otp_record = Otp(
        user_id=user.id,
        code_hash=hash_otp(otp),
        purpose="reset",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )


    db.add(otp_record)
    db.commit()


    send_email(
        user.email,
        "Reset your Paper CMS password",
        f"Your password reset code is {otp}"
    )


    return {
        "message": "Password reset OTP sent"
    }



# ---------- Reset Password (2.6) ----------

@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )


    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    otp_record = (
        db.query(Otp)
        .filter(
            Otp.user_id == user.id,
            Otp.purpose == "reset",
            Otp.used == False
        )
        .order_by(Otp.created_at.desc())
        .first()
    )


    if not otp_record:
        raise HTTPException(
            status_code=400,
            detail="OTP not found"
        )


    if otp_record.attempts >= 5:
        raise HTTPException(
            status_code=400,
            detail="Too many attempts"
        )


    if otp_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="OTP expired"
        )


    if hash_otp(data.code) != otp_record.code_hash:

        otp_record.attempts += 1
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )


    user.password_hash = pwd_context.hash(
        data.new_password
    )

    otp_record.used = True

    db.commit()


    return {
        "message": "Password reset successful"
    }