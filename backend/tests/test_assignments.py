"""
Part 5 tests (5.10 and 5.18): reviewer assignment and accept / decline.

Run:  docker compose exec api python -m pytest tests/test_assignments.py -v
"""
import os
from datetime import date, datetime, timedelta

import bcrypt
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models

# Same pattern as tests/test_conferences.py: talk to the TEST database directly.
_engine = create_engine(os.getenv("TEST_DATABASE_URL"))
_Session = sessionmaker(bind=_engine, autoflush=False)

PASSWORD = "Passw0rd!"


def make_user(role, email, name=None):
    """Insert a verified user and return the id."""
    db = _Session()
    try:
        user = models.User(
            name=name or email.split("@")[0],
            email=email,
            password_hash=bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode(),
            role=role,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id
    finally:
        db.close()


def make_conference(chair_id, name="Conf A", status="open"):
    db = _Session()
    try:
        conf = models.Conference(
            name=name,
            description="test conference",
            start_date=date.today() + timedelta(days=60),
            end_date=date.today() + timedelta(days=62),
            submission_deadline=datetime.now() + timedelta(days=30),
            status=status,
            chairperson_id=chair_id,
        )
        db.add(conf)
        db.commit()
        db.refresh(conf)
        return conf.id
    finally:
        db.close()


def make_paper(conference_id, author_id, title="Paper One"):
    db = _Session()
    try:
        paper = models.Paper(
            conference_id=conference_id,
            author_id=author_id,
            title=title,
            abstract="An abstract.",
            keywords="a, b",
            file_path="uploads/test.pdf",
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)
        return paper.id
    finally:
        db.close()


def login(client, email):
    """Log in through the real route and return the auth header."""
    res = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def sent(monkeypatch):
    """Capture emails so no test sends real mail."""
    box = {"assigned": [], "response": []}
    monkeypatch.setattr(
        "app.routers.assignments.send_reviewer_assigned_email",
        lambda *args: box["assigned"].append(args),
    )
    monkeypatch.setattr(
        "app.routers.assignments.send_chair_response_email",
        lambda *args: box["response"].append(args),
    )
    return box


@pytest.fixture
def world():
    """One conference with a chairperson, an author, one paper and four reviewers."""
    chair = make_user("chairperson", "chair@test.com")
    author = make_user("author", "author@test.com")
    reviewers = [make_user("reviewer", f"rev{i}@test.com", name=f"Reviewer {i}") for i in range(1, 5)]
    conf = make_conference(chair)
    paper = make_paper(conf, author)
    return {"chair": chair, "author": author, "reviewers": reviewers, "conf": conf, "paper": paper}


def assign(client, paper_id, reviewer_id, who="chair@test.com"):
    return client.post(
        f"/papers/{paper_id}/assign", json={"reviewer_id": reviewer_id}, headers=login(client, who)
    )


# ---------------------------------------------------------------------------
# 5.4 / 5.5 / 5.10  chairperson assigns
# ---------------------------------------------------------------------------
def test_chair_can_assign_reviewer_and_reviewer_is_emailed(client, world, sent):
    res = assign(client, world["paper"], world["reviewers"][0])
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "assigned"
    assert body["reviewer_id"] == world["reviewers"][0]
    assert len(sent["assigned"]) == 1
    assert sent["assigned"][0][0] == "rev1@test.com"


def test_assignment_still_works_if_email_fails(client, world, monkeypatch):
    def boom(*args):
        raise RuntimeError("smtp down")

    monkeypatch.setattr("app.routers.assignments.send_reviewer_assigned_email", boom)
    assert assign(client, world["paper"], world["reviewers"][0]).status_code == 201


def test_assigning_in_another_conference_is_blocked(client, world):
    other_chair = make_user("chairperson", "chair2@test.com")
    make_conference(other_chair, name="Conf B")
    res = assign(client, world["paper"], world["reviewers"][0], who="chair2@test.com")
    assert res.status_code == 403


def test_duplicate_assignment_is_rejected(client, world):
    assert assign(client, world["paper"], world["reviewers"][0]).status_code == 201
    res = assign(client, world["paper"], world["reviewers"][0])
    assert res.status_code == 400


def test_author_cannot_be_their_own_reviewer(client, world):
    reviewer_author = make_user("reviewer", "both@test.com", name="Both")
    paper = make_paper(world["conf"], reviewer_author, title="Written by a reviewer")
    res = assign(client, paper, reviewer_author)
    assert res.status_code == 400


def test_maximum_three_reviewers_per_paper(client, world):
    for rid in world["reviewers"][:3]:
        assert assign(client, world["paper"], rid).status_code == 201
    res = assign(client, world["paper"], world["reviewers"][3])
    assert res.status_code == 400


def test_user_who_is_not_a_reviewer_cannot_be_assigned(client, world):
    res = assign(client, world["paper"], world["author"])
    assert res.status_code == 400


def test_unknown_paper_returns_404(client, world):
    assert assign(client, 9999, world["reviewers"][0]).status_code == 404


@pytest.mark.parametrize("who", ["author@test.com", "rev1@test.com"])
def test_only_a_chairperson_can_assign(client, world, who):
    assert assign(client, world["paper"], world["reviewers"][1], who=who).status_code == 403


# ---------------------------------------------------------------------------
# 5.2 / 5.3 lists
# ---------------------------------------------------------------------------
def test_chair_sees_only_own_conference_papers(client, world):
    headers = login(client, "chair@test.com")
    res = client.get(f"/conferences/{world['conf']}/papers", headers=headers)
    assert res.status_code == 200
    papers = res.json()
    assert [p["id"] for p in papers] == [world["paper"]]
    assert papers[0]["author_name"] == "author"
    assert papers[0]["active_reviewers"] == 0

    other_chair = make_user("chairperson", "chair2@test.com")
    other_conf = make_conference(other_chair, name="Conf B")
    res = client.get(f"/conferences/{other_conf}/papers", headers=headers)
    assert res.status_code == 403


def test_papers_list_shows_reviewers_and_status(client, world):
    assign(client, world["paper"], world["reviewers"][0])
    headers = login(client, "chair@test.com")
    paper = client.get(f"/conferences/{world['conf']}/papers", headers=headers).json()[0]
    assert paper["active_reviewers"] == 1
    assert paper["assignments"][0]["reviewer_name"] == "Reviewer 1"
    assert paper["assignments"][0]["status"] == "assigned"


def test_author_cannot_use_the_chair_paper_list(client, world):
    res = client.get(
        f"/conferences/{world['conf']}/papers", headers=login(client, "author@test.com")
    )
    assert res.status_code == 403


def test_reviewers_list_contains_only_reviewers(client, world):
    res = client.get("/reviewers", headers=login(client, "chair@test.com"))
    assert res.status_code == 200
    emails = {r["email"] for r in res.json()}
    assert emails == {f"rev{i}@test.com" for i in range(1, 5)}
    assert client.get("/reviewers", headers=login(client, "author@test.com")).status_code == 403


def test_chair_conferences_lists_only_mine(client, world):
    other_chair = make_user("chairperson", "chair2@test.com")
    make_conference(other_chair, name="Conf B")
    res = client.get("/chair/conferences", headers=login(client, "chair@test.com"))
    assert [c["id"] for c in res.json()] == [world["conf"]]


# ---------------------------------------------------------------------------
# 5.7 unassign
# ---------------------------------------------------------------------------
def test_chair_can_unassign_but_not_other_chair_and_not_declined(client, world):
    a_id = assign(client, world["paper"], world["reviewers"][0]).json()["id"]
    make_user("chairperson", "chair2@test.com")
    assert client.delete(f"/assignments/{a_id}", headers=login(client, "chair2@test.com")).status_code == 403
    assert client.delete(f"/assignments/{a_id}", headers=login(client, "chair@test.com")).status_code == 200

    b_id = assign(client, world["paper"], world["reviewers"][1]).json()["id"]
    client.post(f"/assignments/{b_id}/decline", headers=login(client, "rev2@test.com"))
    assert client.delete(f"/assignments/{b_id}", headers=login(client, "chair@test.com")).status_code == 400


# ---------------------------------------------------------------------------
# 5.12 / 5.13 / 5.14 / 5.18  reviewer responds
# ---------------------------------------------------------------------------
def test_my_assignments_lists_only_my_own(client, world):
    assign(client, world["paper"], world["reviewers"][0])
    assign(client, world["paper"], world["reviewers"][1])
    res = client.get("/assignments/mine", headers=login(client, "rev1@test.com"))
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) == 1
    assert rows[0]["paper_title"] == "Paper One"
    assert rows[0]["conference_name"] == "Conf A"
    assert rows[0]["status"] == "assigned"
    assert "file_path" not in rows[0]
    assert client.get("/assignments/mine", headers=login(client, "author@test.com")).status_code == 403


def test_reviewer_can_accept_and_chair_is_emailed(client, world, sent):
    a_id = assign(client, world["paper"], world["reviewers"][0]).json()["id"]
    res = client.post(f"/assignments/{a_id}/accept", headers=login(client, "rev1@test.com"))
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "accepted"
    assert body["responded_at"] is not None
    assert len(sent["response"]) == 1
    assert sent["response"][0][0] == "chair@test.com"
    assert sent["response"][0][3] == "accepted"


def test_reviewer_can_decline_with_a_reason(client, world, sent):
    a_id = assign(client, world["paper"], world["reviewers"][0]).json()["id"]
    res = client.post(
        f"/assignments/{a_id}/decline",
        json={"reason": "  Conflict of interest  "},
        headers=login(client, "rev1@test.com"),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "declined"
    assert res.json()["decline_reason"] == "Conflict of interest"
    assert sent["response"][0][4] == "Conflict of interest"


def test_decline_works_without_a_reason_or_body(client, world):
    a_id = assign(client, world["paper"], world["reviewers"][0]).json()["id"]
    res = client.post(f"/assignments/{a_id}/decline", headers=login(client, "rev1@test.com"))
    assert res.status_code == 200
    assert res.json()["decline_reason"] is None


def test_only_the_assigned_reviewer_can_respond(client, world):
    a_id = assign(client, world["paper"], world["reviewers"][0]).json()["id"]
    assert client.post(f"/assignments/{a_id}/accept", headers=login(client, "rev2@test.com")).status_code == 403
    assert client.post(f"/assignments/{a_id}/decline", headers=login(client, "rev2@test.com")).status_code == 403
    assert client.post(f"/assignments/{a_id}/accept", headers=login(client, "chair@test.com")).status_code == 403
    assert client.post("/assignments/9999/accept", headers=login(client, "rev1@test.com")).status_code == 404


def test_response_cannot_be_changed_after_accepting(client, world):
    a_id = assign(client, world["paper"], world["reviewers"][0]).json()["id"]
    headers = login(client, "rev1@test.com")
    assert client.post(f"/assignments/{a_id}/accept", headers=headers).status_code == 200
    assert client.post(f"/assignments/{a_id}/decline", headers=headers).status_code == 400
    assert client.post(f"/assignments/{a_id}/accept", headers=headers).status_code == 400
    row = client.get("/assignments/mine", headers=headers).json()[0]
    assert row["status"] == "accepted"


def test_response_cannot_be_changed_after_declining(client, world):
    a_id = assign(client, world["paper"], world["reviewers"][0]).json()["id"]
    headers = login(client, "rev1@test.com")
    assert client.post(f"/assignments/{a_id}/decline", json={"reason": "busy"}, headers=headers).status_code == 200
    assert client.post(f"/assignments/{a_id}/accept", headers=headers).status_code == 400
    row = client.get("/assignments/mine", headers=headers).json()[0]
    assert row["status"] == "declined"
    assert row["decline_reason"] == "busy"


# ---------------------------------------------------------------------------
# 5.15  declined reviewers do not count toward the limit
# ---------------------------------------------------------------------------
def test_declined_reviewer_does_not_count_toward_the_limit(client, world):
    ids = [assign(client, world["paper"], rid).json()["id"] for rid in world["reviewers"][:3]]
    assert assign(client, world["paper"], world["reviewers"][3]).status_code == 400  # full

    client.post(f"/assignments/{ids[0]}/decline", headers=login(client, "rev1@test.com"))

    assert assign(client, world["paper"], world["reviewers"][3]).status_code == 201  # slot freed
    assert assign(client, world["paper"], world["reviewers"][1]).status_code == 400  # still a duplicate

    headers = login(client, "chair@test.com")
    paper = client.get(f"/conferences/{world['conf']}/papers", headers=headers).json()[0]
    assert paper["active_reviewers"] == 3
    assert len(paper["assignments"]) == 4


def test_declined_reviewer_cannot_simply_be_assigned_again(client, world):
    a_id = assign(client, world["paper"], world["reviewers"][0]).json()["id"]
    client.post(f"/assignments/{a_id}/decline", headers=login(client, "rev1@test.com"))
    assert assign(client, world["paper"], world["reviewers"][0]).status_code == 400
    assert assign(client, world["paper"], world["reviewers"][1]).status_code == 201
