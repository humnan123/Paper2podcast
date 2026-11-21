"""
Part 5: chairperson assigns reviewers, reviewers accept or decline.
Tasks 5.2 to 5.7 and 5.12 to 5.15.

Routes in this file
  GET    /chair/conferences              conferences where I am the chairperson
  GET    /conferences/{id}/papers        5.2  papers of my conference, with their reviewers
  GET    /reviewers                      5.3  users with the reviewer role
  POST   /papers/{id}/assign             5.4, 5.5, 5.6, 5.15
  DELETE /assignments/{id}               5.7  unassign (optional task)
  GET    /assignments/mine               5.12 reviewer's own assignments
  POST   /assignments/{id}/accept        5.13, 5.14
  POST   /assignments/{id}/decline       5.13, 5.14

Note: get_current_user / require_role return the JWT payload (a dict with "id" and "role"),
not a User row, so the user is read as user["id"].
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.db import get_db
from app.dependencies import require_role
from app.email_service import send_chair_response_email, send_reviewer_assigned_email

log = logging.getLogger(__name__)

# main.py includes this router without a prefix, so the full paths are written here.
router = APIRouter(tags=["assignments"])

MAX_REVIEWERS = 3
ACTIVE_STATUSES = ("assigned", "accepted")  # a declined reviewer does not count (5.15)


# ----------------------------------------------------------------- helpers
def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _iso(value) -> Optional[str]:
    return value.isoformat() if value is not None else None


def _own_conference(db: Session, conference_id: int, user_id: int) -> "models.Conference":
    conference = db.get(models.Conference, conference_id)
    if conference is None:
        raise HTTPException(status_code=404, detail="Conference not found")
    if conference.chairperson_id != user_id:
        raise HTTPException(status_code=403, detail="This is not your conference")
    return conference


def _active_count(db: Session, paper_id: int) -> int:
    return (
        db.query(models.ReviewAssignment)
        .filter(
            models.ReviewAssignment.paper_id == paper_id,
            models.ReviewAssignment.status.in_(ACTIVE_STATUSES),
        )
        .count()
    )


def _assignment_dict(a, reviewer=None) -> dict:
    return {
        "id": a.id,
        "paper_id": a.paper_id,
        "reviewer_id": a.reviewer_id,
        "reviewer_name": reviewer.name if reviewer else None,
        "reviewer_email": reviewer.email if reviewer else None,
        "status": a.status,
        "assigned_at": _iso(a.assigned_at),
        "responded_at": _iso(a.responded_at),
        "decline_reason": a.decline_reason,
    }


class AssignBody(BaseModel):
    reviewer_id: int


class DeclineBody(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=500)


# ------------------------------------------------------------ chairperson
@router.get("/chair/conferences")
def my_conferences(db: Session = Depends(get_db), user=Depends(require_role("chairperson"))):
    """Conferences where I am the chairperson (the page needs to know which one to load)."""
    rows = (
        db.query(models.Conference)
        .filter(models.Conference.chairperson_id == user["id"])
        .order_by(models.Conference.id)
        .all()
    )
    return [{"id": c.id, "name": c.name, "status": c.status} for c in rows]


@router.get("/conferences/{conference_id}/papers")
def conference_papers(
    conference_id: int, db: Session = Depends(get_db), user=Depends(require_role("chairperson"))
):
    """5.2: papers of my own conference, each with its reviewers and their status."""
    _own_conference(db, conference_id, user["id"])

    papers = (
        db.query(models.Paper)
        .filter(models.Paper.conference_id == conference_id)
        .order_by(models.Paper.id)
        .all()
    )
    paper_ids = [p.id for p in papers]

    assignments = []
    if paper_ids:
        assignments = (
            db.query(models.ReviewAssignment)
            .filter(models.ReviewAssignment.paper_id.in_(paper_ids))
            .order_by(models.ReviewAssignment.id)
            .all()
        )
    user_ids = {p.author_id for p in papers} | {a.reviewer_id for a in assignments}
    users = {}
    if user_ids:
        users = {u.id: u for u in db.query(models.User).filter(models.User.id.in_(user_ids)).all()}

    by_paper = {}
    for a in assignments:
        by_paper.setdefault(a.paper_id, []).append(a)

    result = []
    for p in papers:
        mine = by_paper.get(p.id, [])
        author = users.get(p.author_id)
        result.append(
            {
                "id": p.id,
                "title": p.title,
                "abstract": p.abstract,
                "keywords": p.keywords,
                "status": p.status,
                "submitted_at": _iso(p.submitted_at),
                "author_id": p.author_id,
                "author_name": author.name if author else None,
                "active_reviewers": sum(1 for a in mine if a.status in ACTIVE_STATUSES),
                "max_reviewers": MAX_REVIEWERS,
                "assignments": [_assignment_dict(a, users.get(a.reviewer_id)) for a in mine],
            }
        )
    return result


@router.get("/reviewers")
def list_reviewers(db: Session = Depends(get_db), user=Depends(require_role("chairperson"))):
    """5.3: users with the reviewer role (verified accounts only, they must be able to log in)."""
    rows = (
        db.query(models.User)
        .filter(models.User.role == "reviewer", models.User.is_verified == True)  # noqa: E712
        .order_by(models.User.name)
        .all()
    )
    return [{"id": u.id, "name": u.name, "email": u.email} for u in rows]


@router.post("/papers/{paper_id}/assign", status_code=201)
def assign_reviewer(
    paper_id: int,
    body: AssignBody,
    db: Session = Depends(get_db),
    user=Depends(require_role("chairperson")),
):
    """5.4 + 5.5 + 5.15: assign a reviewer to a paper in my own conference."""
    paper = db.get(models.Paper, paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    conference = _own_conference(db, paper.conference_id, user["id"])

    reviewer = db.get(models.User, body.reviewer_id)
    if reviewer is None or reviewer.role != "reviewer":
        raise HTTPException(status_code=400, detail="The selected user is not a reviewer")

    if reviewer.id == paper.author_id:
        raise HTTPException(status_code=400, detail="An author cannot review their own paper")

    # Any earlier row counts here, including a declined one: the decision is final.
    # To replace a reviewer who declined, assign someone else.
    already = (
        db.query(models.ReviewAssignment)
        .filter(
            models.ReviewAssignment.paper_id == paper.id,
            models.ReviewAssignment.reviewer_id == reviewer.id,
        )
        .first()
    )
    if already is not None:
        raise HTTPException(
            status_code=400,
            detail=f"This reviewer was already assigned to this paper (status: {already.status})",
        )

    if _active_count(db, paper.id) >= MAX_REVIEWERS:
        raise HTTPException(
            status_code=400,
            detail=f"This paper already has {MAX_REVIEWERS} reviewers (declined reviewers do not count)",
        )

    assignment = models.ReviewAssignment(
        paper_id=paper.id,
        reviewer_id=reviewer.id,
        assigned_by=user["id"],
        status="assigned",
    )
    db.add(assignment)
    try:
        db.commit()
    except IntegrityError:  # two clicks at once hit the unique (paper, reviewer) rule
        db.rollback()
        raise HTTPException(status_code=400, detail="This reviewer was already assigned to this paper")
    db.refresh(assignment)

    try:  # 5.6: an email problem must not undo the assignment
        send_reviewer_assigned_email(reviewer.email, reviewer.name, paper.title, conference.name)
    except Exception:
        log.exception("Could not send the assignment email to %s", reviewer.email)

    return _assignment_dict(assignment, reviewer)


@router.delete("/assignments/{assignment_id}")
def unassign_reviewer(
    assignment_id: int, db: Session = Depends(get_db), user=Depends(require_role("chairperson"))
):
    """5.7 (optional): remove a reviewer who has not declined."""
    assignment = db.get(models.ReviewAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    paper = db.get(models.Paper, assignment.paper_id)
    _own_conference(db, paper.conference_id, user["id"])
    if assignment.status == "declined":
        raise HTTPException(status_code=400, detail="A declined assignment is kept as a record")
    db.delete(assignment)
    db.commit()
    return {"detail": "Reviewer unassigned"}


# --------------------------------------------------------------- reviewer
@router.get("/assignments/mine")
def my_assignments(db: Session = Depends(get_db), user=Depends(require_role("reviewer"))):
    """5.12: the logged-in reviewer's assignments. The PDF path is never returned here."""
    rows = (
        db.query(models.ReviewAssignment, models.Paper, models.Conference)
        .join(models.Paper, models.Paper.id == models.ReviewAssignment.paper_id)
        .join(models.Conference, models.Conference.id == models.Paper.conference_id)
        .filter(models.ReviewAssignment.reviewer_id == user["id"])
        .order_by(models.ReviewAssignment.id.desc())
        .all()
    )
    return [
        {
            "id": a.id,
            "status": a.status,
            "assigned_at": _iso(a.assigned_at),
            "responded_at": _iso(a.responded_at),
            "decline_reason": a.decline_reason,
            "paper_id": p.id,
            "paper_title": p.title,
            "paper_abstract": p.abstract,
            "paper_keywords": p.keywords,
            "conference_id": c.id,
            "conference_name": c.name,
            "deadline": _iso(c.submission_deadline),
        }
        for a, p, c in rows
    ]


def _respond(db: Session, assignment_id: int, user: dict, new_status: str, reason: Optional[str]) -> dict:
    assignment = db.get(models.ReviewAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if assignment.reviewer_id != user["id"]:
        raise HTTPException(status_code=403, detail="This assignment is not yours")

    # One atomic update, so a double click or two tabs cannot respond twice.
    changed = (
        db.query(models.ReviewAssignment)
        .filter(models.ReviewAssignment.id == assignment_id, models.ReviewAssignment.status == "assigned")
        .update(
            {"status": new_status, "responded_at": _utcnow(), "decline_reason": reason},
            synchronize_session=False,
        )
    )
    db.commit()
    if changed == 0:
        raise HTTPException(status_code=400, detail="You have already responded to this assignment")
    db.refresh(assignment)

    reviewer = db.get(models.User, user["id"])
    paper = db.get(models.Paper, assignment.paper_id)
    conference = db.get(models.Conference, paper.conference_id)
    chair = db.get(models.User, conference.chairperson_id) if conference.chairperson_id else None
    if chair is not None:
        try:  # 5.14
            send_chair_response_email(chair.email, reviewer.name, paper.title, new_status, reason)
        except Exception:
            log.exception("Could not send the response email to %s", chair.email)

    return _assignment_dict(assignment, reviewer)


@router.post("/assignments/{assignment_id}/accept")
def accept_assignment(
    assignment_id: int, db: Session = Depends(get_db), user=Depends(require_role("reviewer"))
):
    return _respond(db, assignment_id, user, "accepted", None)


@router.post("/assignments/{assignment_id}/decline")
def decline_assignment(
    assignment_id: int,
    body: Optional[DeclineBody] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role("reviewer")),
):
    reason = (body.reason or "").strip() if body else ""
    return _respond(db, assignment_id, user, "declined", reason or None)
