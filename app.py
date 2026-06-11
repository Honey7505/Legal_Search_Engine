from flask import Flask, render_template, request, jsonify, send_file
import json
import re
import faiss
import numpy as np
from rapidfuzz import process
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

app = Flask(__name__)

with open("documents.json", "r") as f:
    documents = json.load(f)


def filter_by_state(state):
    return [d for d in documents if d.get("jurisdiction") == state]
# ==============================
# LOAD MODEL
# ==============================
model = SentenceTransformer("BAAI/bge-small-en-v1.5")

# ==============================
# LOAD FAISS
# ==============================
index = faiss.read_index("faiss.index")

# ==============================
# LOAD CHUNKS
# ==============================
with open("law_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

pdf_documents = []

seen = set()

for i, c in enumerate(chunks):

    pdf = c.get("pdf_path", "")

    if pdf and pdf not in seen:

        seen.add(pdf)

        pdf_documents.append({
            "id": len(pdf_documents),
            "law_name": c["act_name"],
            "law_type": c.get("law_type", ""),
            "jurisdiction": c.get("jurisdiction", ""),
            "pdf_path": pdf
        })
# ==============================
# BM25 SETUP
# ==============================
tokenized_docs = [
    chunk["search_text"].lower().split()
    for chunk in chunks
]

bm25 = BM25Okapi(tokenized_docs)

# ==============================
# VOCAB + SUGGESTIONS
# ==============================
vocabulary = set()
suggestions = set()

for c in chunks:
    text = f"{c.get('act_name','')} {c.get('offence','')} {c.get('chunk_text','')}"
    vocabulary.update(re.findall(r"\b\w+\b", text.lower()))

    suggestions.add(c.get("act_name", ""))
    suggestions.add(c.get("offence", ""))
    suggestions.add(f"Section {c.get('section','')}")

vocabulary = list(vocabulary)
suggestions = list(suggestions)


# ==============================
# AUTOCOMPLETE
# ==============================
def get_suggestions(query, limit=5):
    if len(query) < 3:
        return []
    return [x[0] for x in process.extract(query, suggestions, limit=limit)]


# ==============================
# SPELL CORRECTION
# ==============================
def spell_correct(query):
    corrected = []
    for w in query.split():
        if len(w) <= 3:
            corrected.append(w)
            continue

        match = process.extractOne(w.lower(), vocabulary, score_cutoff=90)
        corrected.append(match[0] if match else w)

    return " ".join(corrected)


# ==============================
# SEARCH ENGINE (WITH FILTER)
# ==============================
def search_engine(query, state_filter=None):

    corrected_query = spell_correct(query)
    suggestions_found = get_suggestions(query)

    # ==========================
    # FILTER BY STATE FIRST
    # ==========================
    filtered_chunks = chunks

    if state_filter:
        filtered_chunks = [
            c for c in chunks
            if c.get("jurisdiction") == state_filter
        ]

    # ==========================
    # SECTION SEARCH
    # ==========================
    section_match = re.search(r'section\s+(\d+[A-Z]?)', corrected_query, re.IGNORECASE)

    if section_match:
        sec = section_match.group(1).upper()

        results = [
            {
                "chunk_id": c["chunk_id"],
                "law_name": c["act_name"],
                "law_type": c.get("law_type", ""),
                "jurisdiction": c.get("jurisdiction", ""),
                "chapter": c.get("chapter", ""),
                "chapter_name": c.get("chapter_name", ""),
                "section": c.get("section", ""),
                "title": c.get("title", "N/A"),
                "offence": c.get("offence", ""),
                "penalty": c.get("penalty", "Not Found"),
                "context": c.get("chunk_text", "")[:1000],
                "full_text": c.get("chunk_text", ""),
                "score": 1.0
            }
            for c in filtered_chunks
            if c.get("section", "").upper() == sec
        ]

        return {
            "results": results[:10],
            "suggestions": suggestions_found,
            "corrected_query": corrected_query
        }
    bm25_scores = bm25.get_scores(
        corrected_query.lower().split()
    )
    # ==========================
    # EMBEDDING SEARCH (FAISS)
    # ==========================
    query_embedding = model.encode(
        [f"query: {corrected_query}"],
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype("float32")

    D, I = index.search(query_embedding, 50)

    results = []
    seen = set()

    for score, idx in zip(D[0], I[0]):

        if idx == -1:
            continue

        c = chunks[idx]

        # apply state filter
        if state_filter and c.get("jurisdiction") != state_filter:
            continue

        key = (
                c.get("jurisdiction"),
                c.get("section"),
                c.get("title")
        )
        if key in seen:
            continue
        seen.add(key)

        context = " ".join(
            c["chunk_text"].split()[:120]
        )

        for word in corrected_query.split():

            context = re.sub(
                rf"({re.escape(word)})",
                r"<mark>\1</mark>",
                context,
                flags=re.IGNORECASE
            )

        results.append({
            "chunk_id": c["chunk_id"],
            "law_name": c["act_name"],
            "law_type": c.get("law_type", ""),
            "jurisdiction": c.get("jurisdiction", ""),
            "chapter": c.get("chapter", ""),
            "chapter_name": c.get("chapter_name", ""),
            "section": c.get("section", ""),
            "title": c.get("title", "N/A"),
            "offence": c.get("offence", ""),
            "penalty": c.get("penalty", "Not Found"),
            "context": context + "...",
            "full_text": c["chunk_text"],
            "score": float(score),
            "pdf_path": c.get("pdf_path", "")
        })

        if len(results) == 10:
            break

    return {
        "results": results,
        "suggestions": suggestions_found,
        "corrected_query": corrected_query
    }


# ==============================
# SIDEBAR DATA
# ==============================
all_laws = sorted(
    [
        {
            "name": c["act_name"],
            "jurisdiction": c.get("jurisdiction", "")
        }
        for c in chunks
    ],
    key=lambda x: x["name"]
)

total_laws = len(
    set(
        c["act_name"]
        for c in chunks
    )
)

central_laws = len(
    set(
        c["act_name"]
        for c in chunks
        if c["law_type"] == "Central Law"
    )
)

state_laws = len(
    set(
        c["act_name"]
        for c in chunks
        if c["law_type"] == "State Law"
    )
)

ut_laws = len(
    set(
        c["act_name"]
        for c in chunks
        if c["law_type"] == "Union Territory Law"
    )
)

states = sorted(list(set(
    c.get("jurisdiction", "")
    for c in chunks
    if c.get("law_type") == "State Law"
)))

uts = sorted(
    list(
        set(
            c.get("jurisdiction", "")
            for c in chunks
            if c.get("law_type") == "Union Territory Law"
        )
    )
)

# states = sorted(list(set(d["jurisdiction"] for d in documents)))


# ==============================
# ROUTE
# ==============================
@app.route("/", methods=["GET", "POST"])
def home():

    data = None

    state = request.form.get("state")
    ut = request.form.get("ut")
    query = request.form.get("query")

    state_filter = state or ut

    # ==========================
    # CASE 1: SEARCH
    # ==========================
    if query:
        data = search_engine(query, state_filter)

    # ==========================
    # CASE 2: ONLY STATE SELECTED (NO SEARCH)
    # ==========================
    elif state_filter:
        filtered = [
            c for c in chunks
            if c.get("jurisdiction") == state_filter
        ]

        data = {
            "results": [
                {
                    "law_name": c["act_name"],
                    "law_type": c.get("law_type", ""),
                    "jurisdiction": c.get("jurisdiction", ""),
                    "chapter": c.get("chapter", ""),
                    "chapter_name": c.get("chapter_name", ""),
                    "section": c.get("section", ""),
                    "title": c.get("title", "N/A"),
                    "offence": c.get("offence", ""),
                    "penalty": c.get("penalty", "Not Found"),
                    "context": " ".join(c["chunk_text"].split()[:120]) + "...", 
                    "full_text": c["chunk_text"],
                    "score": 1.0
                }
                for c in filtered[:20]
            ],
            "suggestions": [],
            "corrected_query": ""
        }

    return render_template(
        "index2.html",
        data=data,
        all_laws=all_laws,
        states=states,
        uts=uts,
        pdf_documents = pdf_documents,
        total_laws = total_laws,
        central_laws = central_laws,
        state_laws = state_laws,
        ut_laws = ut_laws,
        query = query or ""
        
    )

@app.route("/open/<path:filename>")
def open_document(filename):

    for doc in documents:
        if doc["file"] == filename:
            return send_file(doc["path"])

    return "File not found", 404

@app.route("/all_laws")
def all_laws_api():

    results = []

    for c in chunks:
        results.append({
            "law_name": c.get("act_name", ""),
            "jurisdiction": c.get("jurisdiction", ""),
            "section": c.get("section", ""),
            "title": c.get("title", "N/A"),
            "offence": c.get("offence", "N/A"),
            "penalty": c.get("penalty", "Not Found"),
            "context": c.get("chunk_text", "")[:300]
        })

    return jsonify({"results": results})

@app.route("/filter_state")
def filter_state():

    state = request.args.get("state")

    results = []

    for c in chunks:

        if state and state.lower() in c.get("jurisdiction","").lower():

            results.append({
                "law_name": c.get("act_name", ""),
                "jurisdiction": c.get("jurisdiction", ""),
                "section": c.get("section", ""),
                "title": c.get("title", "N/A"),
                "offence": c.get("offence", "N/A"),
                "penalty": c.get("penalty", "Not Found"),
                "context": c.get("chunk_text", "")[:1000]
            })

    return jsonify({"results": results})

@app.route("/view_pdf")
def see_pdf():

    pdf_path = request.args.get("pdf")

    return send_file(pdf_path)

@app.route("/all_pdfs")
def all_pdfs():

    return jsonify({
        "results": pdf_documents
    })

'''@app.route("/state_pdfs")
def state_pdfs():

    state = request.args.get("state")

    seen = set()
    results = []

    for c in chunks:

        if c.get("jurisdiction") == state:

            pdf = c.get("pdf_path", "")

            if pdf not in seen:

                seen.add(pdf)

                results.append({
                    "law_name": c["act_name"],
                    "pdf_path": pdf
                })

    return jsonify({
        "results": results
    })'''

'''@app.route("/ut_pdfs")
def ut_pdfs():

    ut = request.args.get("ut")

    seen = set()
    results = []

    for c in chunks:

        if c.get("jurisdiction") == ut:

            pdf = c.get("pdf_path", "")

            if pdf not in seen:

                seen.add(pdf)

                results.append({
                    "law_name": c["act_name"],
                    "pdf_path": pdf
                })

    return jsonify({
        "results": results
    })'''

@app.route("/ut_pdfs")
def ut_pdfs():

    ut = request.args.get("ut")

    results = []

    for pdf in pdf_documents:

        if pdf["jurisdiction"].lower() == ut.lower():

            results.append(pdf)

    return jsonify({
        "results": results
    })

@app.route("/view_pdf/<int:chunk_id>")
def view_pdf(chunk_id):

    chunk = next(
        c for c in chunks
        if c["chunk_id"] == chunk_id
    )

    section = request.args.get("section")

    return render_template(
        # chunk["pdf_path"],
        # mimetype="application/pdf"
        "pdf_viewer.html",
        pdf_path=chunk["pdf_path"],
        section=section
    )

@app.route("/pdf/<int:index>")
def open_pdf(index):

    pdf = pdf_documents[index]

    return send_file(
        pdf["pdf_path"],
        mimetype="application/pdf"
    )

@app.route("/state_pdfs")
def state0_pdfs():

    state = request.args.get("state")

    results = []

    for pdf in pdf_documents:

        if pdf["jurisdiction"].lower() == state.lower():

            results.append(pdf)

    return jsonify({"results": results})

@app.route("/suggest")
def suggest():

    q = request.args.get("q","")

    return jsonify(
        get_suggestions(q)
    )

@app.route("/debug_states")
def debug_states():
    return jsonify(states)

@app.route("/debug_uts")
def debug_uts():
    return jsonify(uts)

@app.route("/debug_law_types")
def debug_law_types():

    types = set()

    for c in chunks:
        types.add(c.get("law_type"))

    return jsonify(list(types))

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run(debug=True)






