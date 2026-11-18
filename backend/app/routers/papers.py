import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_role
from app.models import Conference, Paper

router = APIRouter(prefix="/papers", tags=["papers"])

# Folder where PDFs are saved (inside the api container: /app/uploads).
# NOTE: on Render the disk is wiped on every redeploy. Fine for a demo.
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


def paper_to_dict(paper, conference_name=None):
    return {
        "id": paper.id,
        "conference_id": paper.conference_id,
        "conference_name": conference_name,
        "title": paper.title,
        "abstract": paper.abstract,
        "keywords": paper.keywords,
        "status": paper.status,
        "submitted_at": paper.submitted_at,
    }


# 4.2 + 4.3 + 4.4  Submit a paper
@router.post("", status_code=201)
async def submit_paper(
    conference_id: int = Form(...),
    title: str = Form(...),
    abstract: str = Form(...),
    keywords: str = Form(""),
    terms_accepted: bool = Form(False),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    author=Depends(require_role("author")),
):
    # 4.4 terms checkbox, checked on the server too
    if not terms_accepted:
        raise HTTPException(400, "You must accept the terms to submit")

    if not title.strip():
        raise HTTPException(400, "Title is required")
    if not abstract.strip():
        raise HTTPException(400, "Abstract is required")

    # 4.2 conference must exist, be open, and not past its deadline
    conf = db.get(Conference, conference_id)
    if not conf:
        raise HTTPException(404, "Conference not found")
    if conf.status != "open":
        raise HTTPException(400, "This conference is closed for submissions")
    if datetime.utcnow() > conf.submission_deadline:
        raise HTTPException(400, "The submission deadline has passed")

    # 4.3 file checks: PDF header, size limit
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, "The file is empty")
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(400, "File is too large (max 10 MB)")
    if not content.startswith(b"%PDF"):
        raise HTTPException(400, "Only PDF files are allowed")

    # unique stored filename (never use the name the user sent)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}.pdf"
    (UPLOAD_DIR / stored_name).write_bytes(content)

    paper = Paper(
        conference_id=conf.id,
        author_id=author["id"],
        title=title.strip(),
        abstract=abstract.strip(),
        keywords=keywords.strip() or None,
        file_path=str(UPLOAD_DIR / stored_name),
        status="submitted",
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
    return paper_to_dict(paper, conf.name)


# 4.5  Only the logged-in author's papers
@router.get("/mine")
def my_papers(
    db: Session = Depends(get_db),
    author=Depends(require_role("author")),
):
    rows = (
        db.query(Paper, Conference.name)
        .join(Conference, Conference.id == Paper.conference_id)
        .filter(Paper.author_id == author["id"])
        .order_by(Paper.submitted_at.desc())
        .all()
    )
    return [paper_to_dict(p, name) for p, name in rows]
