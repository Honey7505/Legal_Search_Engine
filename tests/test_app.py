def test_home_page(client):

    response = client.get("/")

    assert response.status_code == 200


def test_all_pdfs(client):

    response = client.get("/all_pdfs")

    assert response.status_code == 200

    data = response.get_json()

    assert "results" in data


def test_state_pdfs(client):

    response = client.get(
        "/state_pdfs?state=Maharastra"
    )

    assert response.status_code == 200


def test_ut_pdfs(client):

    response = client.get(
        "/ut_pdfs?ut=Delhi"
    )

    assert response.status_code == 200
