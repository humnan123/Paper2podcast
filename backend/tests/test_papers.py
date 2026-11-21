import os
from datetime import datetime, timedelta

import bcrypt
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.routers import papers as papers_router

_engine = create_engine(os.getenv("TEST_DATABASE_URL"))
_Session = sessionmaker(bind=_engine, autoflush=False)

PASSWORD = "Passw0rd!"
PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF"


@pytest.fixture(autouse=True)
def upload_to_tmp(tmp_path, monkeypatch):
    # tests must not write into the real uploads folder
    monkeypatch.setattr(papers_router, "UPLOAD_DIR", tmp_path)


def make_user(role, email):
    db = _Session()
    hashed = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()
    db.add(models.User(name=role, email=email, password_hash=hashed,
                       role=role, is_verified=True))
    db.commit()
    db.close()


def make_conference(name="Conf", status="open", days_to_deadline=30):
    db = _Session()
    conf = models.Conference(
        name=name,
        start_date=(datetime.utcnow() + timedelta(days=60)).date(),
        end_date=(datetime.utcnow() + timedelta(days=62)).date(),
        submission_deadline=datetime.utcnow() + timedelta(days=days_to_deadline),
        status=status,
    )
    db.add(conf)
    db.commit()
    conf_id = conf.id
    db.close()
    return conf_id


def auth(client, email):
    res = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def submit(client, headers, conference_id, file=("paper.pdf", PDF, "application/pdf"),
           terms="true", title="My paper"):
    return client.post(
        "/papers",
        data={
            "conference_id": str(conference_id),
            "title": title,
            "abstract": "An abstract",
            "keywords": "ai, nlp",
            "terms_accepted": terms,
        },
        files={"file": file},
        headers=headers,
    )


def test_author_can_submit_pdf(client):
    make_user("author", "a@test.com")
    conf = make_conference()
    res = submit(client, auth(client, "a@test.com"), conf)
    assert res.status_code == 201, res.text
    assert res.json()["status"] == "submitted"


def test_non_pdf_is_rejected(client):
    make_user("author", "a@test.com")
    conf = make_conference()
    res = submit(client, auth(client, "a@test.com"), conf,
                 file=("fake.pdf", b"just some text", "application/pdf"))
    assert res.status_code == 400


def test_missing_terms_is_rejected(client):
    make_user("author", "a@test.com")
    conf = make_conference()
    res = submit(client, auth(client, "a@test.com"), conf, terms="false")
    assert res.status_code == 400


def test_closed_conference_is_rejected(client):
    make_user("author", "a@test.com")
    conf = make_conference(status="closed")
    res = submit(client, auth(client, "a@test.com"), conf)
    assert res.status_code == 400


def test_deadline_passed_is_rejected(client):
    make_user("author", "a@test.com")
    conf = make_conference(days_to_deadline=-1)
    res = submit(client, auth(client, "a@test.com"), conf)
    assert res.status_code == 400


def test_reviewer_cannot_submit(client):
    make_user("reviewer", "r@test.com")
    conf = make_conference()
    res = submit(client, auth(client, "r@test.com"), conf)
    assert res.status_code == 403


def test_author_sees_only_own_papers(client):
    make_user("author", "a1@test.com")
    make_user("author", "a2@test.com")
    conf = make_conference()
    h1 = auth(client, "a1@test.com")
    h2 = auth(client, "a2@test.com")
    assert submit(client, h1, conf, title="Paper of A1").status_code == 201

    mine1 = client.get("/papers/mine", headers=h1).json()
    mine2 = client.get("/papers/mine", headers=h2).json()
    assert [p["title"] for p in mine1] == ["Paper of A1"]
    assert mine2 == []
