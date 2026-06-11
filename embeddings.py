'''import json
import numpy as np
import re
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize

model = SentenceTransformer(
    "BAAI/bge-small-en-v1.5"
)

def clean_text(text):
    text = text.replace("\u0000", " ")
    text = text.replace("�", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

with open(
    "law_chunks.json",
    "r",
    encoding="utf-8"
) as f:
    chunks = json.load(f)

texts = []

for chunk in chunks:

    search_text = f"""
    {chunk['act_name']}
    Section {chunk['section']}
    {chunk['title']}

    {chunk['chunk_text']}
    """

    search_text = clean_text(search_text)

    if len(search_text) < 20:
        continue

    texts.append(search_text)

embeddings = model.encode(
    texts,
    batch_size=32,
    show_progress_bar=True,
    convert_to_numpy=True
)

embeddings = normalize(
    embeddings,
    axis=1
)

np.save(
    "embeddings.npy",
    embeddings
)

print(f"Indexed {len(texts)} chunks")
print(f"Embedding shape: {embeddings.shape}")
print(len(texts))'''






'''import json
import numpy as np
import re

from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize

# ==========================================
# Load Model
# ==========================================

model = SentenceTransformer(
    "BAAI/bge-small-en-v1.5"
)

# ==========================================
# Clean Text
# ==========================================

def clean_text(text):

    text = text.replace(
        "\u0000",
        " "
    )

    text = text.replace(
        "�",
        " "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ==========================================
# Load Chunks
# ==========================================

with open(
    "law_chunks.json",
    "r",
    encoding="utf-8"
) as f:

    chunks = json.load(f)

# ==========================================
# Build Embedding Text
# ==========================================

texts = []

for chunk in chunks:

    # Use search_text if available
    text = chunk.get(
        "search_text",
        ""
    )

    text = clean_text(text)

    if len(text) < 20:
        continue

    texts.append(
        "passage: " + text
    )

# ==========================================
# Create Embeddings
# ==========================================

embeddings = model.encode(
    texts,
    batch_size=32,
    show_progress_bar=True,
    convert_to_numpy=True
)

# ==========================================
# Normalize
# ==========================================

embeddings = normalize(
    embeddings,
    axis=1
)

# ==========================================
# Save
# ==========================================

np.save(
    "embeddings.npy",
    embeddings
)

print("\n=================================")
print(f"Indexed Chunks : {len(texts)}")
print(f"Embedding Shape: {embeddings.shape}")
print("Saved: embeddings.npy")
print("=================================")'''





import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict


# =========================================================
# CONFIG
# =========================================================

MODEL_NAME = "BAAI/bge-small-en-v1.5"
INPUT_FILE = "law_chunks.json"

EMBEDDING_FILE = "embeddings.npy"
INDEX_FILE = "faiss.index"
MAPPING_FILE = "chunk_mapping.json"


# =========================================================
# LOAD MODEL
# =========================================================

model = SentenceTransformer(MODEL_NAME)


# =========================================================
# BUILD EMBEDDING TEXT (VERY IMPORTANT)
# =========================================================

def build_embedding_text(chunk: Dict) -> str:

    return f"""
passage:

ACT: {chunk.get('act_name', '')}

LAW TYPE: {chunk.get('law_type', '')}

JURISDICTION: {chunk.get('jurisdiction', '')}

CHAPTER: {chunk.get('chapter', '')}

CHAPTER NAME: {chunk.get('chapter_name', '')}

SECTION: {chunk.get('section', '')}

SUBSECTION: {chunk.get('subsection', '')}

TITLE: {chunk.get('title', '')}

OFFENCE: {chunk.get('offence', '')}

PENALTY: {chunk.get('penalty', '')}

CONTENT:
{chunk.get('chunk_text', '')}
""".strip()


# =========================================================
# LOAD DATA
# =========================================================

def load_chunks(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# CREATE EMBEDDINGS
# =========================================================

def create_embeddings(chunks: List[Dict]):
    texts = []

    for chunk in chunks:

        text = build_embedding_text(chunk)

        words = text.split()

        if len(words) > 500:
            text = " ".join(words[:500])

        texts.append(text)

    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True   # IMPORTANT FIX
    )

    embeddings = np.array(embeddings).astype("float32")

    return embeddings


# =========================================================
# BUILD FAISS INDEX
# =========================================================

def build_faiss_index(embeddings: np.ndarray):
    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)  # cosine similarity (with normalized vectors)
    index.add(embeddings)

    return index


# =========================================================
# SAVE ARTIFACTS
# =========================================================

def save_all(chunks, embeddings, index):

    # embeddings
    np.save(EMBEDDING_FILE, embeddings)

    # faiss index
    faiss.write_index(index, INDEX_FILE)

    # mapping
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        for chunk in chunks:
            chunk["embedding_text"] = build_embedding_text(chunk)
        json.dump(chunks, f, ensure_ascii=False, indent=2)


# =========================================================
# MAIN PIPELINE
# =========================================================

def main():

    print("Loading chunks...")
    chunks = load_chunks(INPUT_FILE)

    print(f"Total chunks: {len(chunks)}")

    print("Creating embeddings...")
    embeddings = create_embeddings(chunks)

    print("Building FAISS index...")
    index = build_faiss_index(embeddings)

    print("Saving files...")
    save_all(chunks, embeddings, index)

    print("\n================================")
    print("Embedding pipeline completed")
    print(f"Chunks: {len(chunks)}")
    print(f"Index dim: {embeddings.shape}")
    print("Saved: embeddings.npy, faiss.index, chunk_mapping.json")
    print("================================")


if __name__ == "__main__":
    main()





