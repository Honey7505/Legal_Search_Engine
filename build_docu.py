import os
import json

BASE_DIR = "laws"

docs = []

for root, _, files in os.walk(BASE_DIR):
    for file in files:
        if file.endswith(".pdf"):
            path = os.path.join(root, file)

            # detect state from folder
            parts = path.split(os.sep)

            state = "Unknown"
            if len(parts) > 1:
                state = parts[1]

            docs.append({
                "file": file,
                "path": path,
                "state": state,
                "type": "pdf"
            })

with open("documents.json", "w") as f:
    json.dump(docs, f, indent=2)

print("Document index created")
