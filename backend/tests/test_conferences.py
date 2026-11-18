import os
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import models

_engine = create_engine(os.getenv("TEST_DATABASE_URL"))
_Session = sessionmaker(bind=_engine, autoflush=False)

PASSWORD = "Passw0rd!"


def make_user(role, email):
    db = _Session()
    hashed = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()
    db.add(models.User(
        name=role,
        email=email,
        password_hash=hashed,
        role=role,
        is_verified=True,
    ))
    db.commit()
    db.close()


def get_token(client, email):
    res = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def valid_payload(name="Test Conf", chair_email="chair@test.com"):
    return {
        "name": name,
        "description": "Test",
        "start_date": "2027-03-01",
        "end_date": "2027-03-03",
        "submission_deadline": "2027-02-01",
        "chairperson_email": chair_email,
    }


# ---- GET tests ----

def test_list_conferences_returns_200(client):
    response = client.get("/conferences")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_missing_conference_returns_404(client):
    response = client.get("/conferences/999")
    assert response.status_code == 404


# ---- POST tests ----

def test_author_cannot_create_conference(client):
    make_user("author", "author@test.com")
    token = get_token(client, "author@test.com")
    res = client.post("/conferences", json=valid_payload(), headers=auth_header(token))
    assert res.status_code == 403


def test_deadline_after_start_is_rejected(client):
    make_user("admin", "admin@test.com")
    make_user("author", "chair@test.com")
    token = get_token(client, "admin@test.com")
    payload = valid_payload()
    payload["submission_deadline"] = "2027-03-05"
    res = client.post("/conferences", json=payload, headers=auth_header(token))
    assert res.status_code == 400


def test_duplicate_name_is_rejected(client):
    make_user("admin", "admin@test.com")
    make_user("author", "chair@test.com")
    token = get_token(client, "admin@test.com")
    first = client.post("/conferences", json=valid_payload(), headers=auth_header(token))
    assert first.status_code == 201
    second = client.post("/conferences", json=valid_payload(), headers=auth_header(token))
    assert second.status_code == 409