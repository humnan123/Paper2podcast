from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Conference, User
from app.dependencies import require_role

router = APIRouter(prefix="/conferences", tags=["conferences"])


class ConferenceCreate(BaseModel):
    name: str
    description: str | None = None
    start_date: date
    end_date: date
    submission_deadline: date
    chairperson_email: str   # admin types the chair's email


@router.post("", status_code=201)
def create_conference(
    data: ConferenceCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    # 3.2 validation
    if db.query(Conference).filter(Conference.name == data.name).first():
        raise HTTPException(409, "A conference with this name already exists")
    if data.submission_deadline >= data.start_date:
        raise HTTPException(400, "Submission deadline must be before the start date")
    if data.end_date < data.start_date:
        raise HTTPException(400, "End date cannot be before the start date")

    # 3.3 chairperson assignment
    chair = db.query(User).filter(User.email == data.chairperson_email).first()
    if not chair:
        raise HTTPException(404, "No user with that email")
    if chair.role == "admin":
        raise HTTPException(400, "An admin cannot be made chairperson")

    chair.role = "chairperson"
    conf = Conference(
        name=data.name,
        description=data.description,
        start_date=data.start_date,
        end_date=data.end_date,
        submission_deadline=data.submission_deadline,
        status="open",
        chairperson_id=chair.id,
    )
    db.add(conf)
    db.commit()          # conference and role change save together
    db.refresh(conf)
    return conf


# 3.4 read endpoints
@router.get("")
def list_conferences(db: Session = Depends(get_db)):
    return db.query(Conference).order_by(Conference.start_date).all()


@router.get("/{conference_id}")
def get_conference(conference_id: int, db: Session = Depends(get_db)):
    conf = db.get(Conference, conference_id)
    if not conf:
        raise HTTPException(404, "Conference not found")
    return conf