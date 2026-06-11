from app import search_engine


def test_search_theft():

    result = search_engine("theft")

    assert len(result["results"]) > 0


def test_search_section():

    result = search_engine(
        "section 66C"
    )

    assert "results" in result


def test_state_filter():

    result = search_engine(
        "theft",
        "Maharastra"
    )

    assert "results" in result
