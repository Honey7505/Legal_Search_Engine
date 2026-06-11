import json


def load_chunks():

    with open(
        "law_chunks.json",
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def test_law_type():

    chunks = load_chunks()

    valid = {
        "Central Law",
        "State Law",
        "Union Territory Law",
        "Unknown"
    }

    for c in chunks[:100]:
        assert c["law_type"] in valid


def test_jurisdiction():

    chunks = load_chunks()

    for c in chunks[:100]:
        assert c["jurisdiction"] != ""
