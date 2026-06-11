import json


def test_chunk_file_exists():

    with open(
        "law_chunks.json",
        "r",
        encoding="utf-8"
    ) as f:

        chunks = json.load(f)

    assert len(chunks) > 0


def test_chunk_has_required_fields():

    with open(
        "law_chunks.json",
        "r",
        encoding="utf-8"
    ) as f:

        chunks = json.load(f)

    sample = chunks[0]

    required = [
        "chunk_id",
        "act_name",
        "section",
        "title",
        "chunk_text"
    ]

    for field in required:
        assert field in sample
