#!/usr/bin/env python3
"""Download the embedding model from HuggingFace Hub into ./models/.

Must be run before building the production Docker image so the model
is available to COPY into the image (no internet access at build time).

    # with uv (recommended):
    uv run python scripts/download_model.py

    # or via make:
    make download-model

The destination directory is ./models/ (relative to the project root).
HF_HOME is overridden so the model lands there and not in ~/.cache/.
The directory is excluded from git (.gitignore) but included in the
production Docker build context (.dockerignore / Dockerfile.prod.dockerignore).
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"
)

# Point HuggingFace cache to our local models/ directory
os.environ["HF_HOME"] = str(MODELS_DIR)

print(f"Downloading model  : {MODEL_NAME}")
print(f"Destination        : {MODELS_DIR}")

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print(
        "ERROR: sentence-transformers is not installed.\n"
        "Run: uv sync  (or: pip install sentence-transformers)",
        file=sys.stderr,
    )
    sys.exit(1)

MODELS_DIR.mkdir(parents=True, exist_ok=True)

model = SentenceTransformer(MODEL_NAME)
print(f"Done. Vector size  : {model.get_sentence_embedding_dimension()}")
print(f"Files written to   : {MODELS_DIR}")
