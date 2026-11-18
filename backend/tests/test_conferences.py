def test_list_conferences_returns_200(client):
    response = client.get("/conferences")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_missing_conference_returns_404(client):
    response = client.get("/conferences/999")
    assert response.status_code == 404