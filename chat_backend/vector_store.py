import json
import logging
import hashlib
from pathlib import Path
from typing import List, Optional

import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

logger = logging.getLogger("ChatBackend")

CONTEXT_DIR = Path(__file__).parent / "context"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


class SimpleHashEmbeddings(Embeddings):
    """
    Lightweight embedding using a simple bag-of-words with hashing trick.
    No PyTorch / sentence-transformers needed.
    Dimensionality is fixed at 256 floats.
    """
    DIM = 256

    def _embed(self, text: str) -> List[float]:
        vec = np.zeros(self.DIM, dtype=np.float32)
        words = text.lower().split()
        for word in words:
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = h % self.DIM
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

def _json_to_text(data, prefix: str = "") -> str:
    lines = []
    if isinstance(data, dict):
        for k, v in data.items():
            label = f"{prefix}{k}" if prefix else k
            if isinstance(v, (dict, list)):
                lines.append(_json_to_text(v, prefix=f"{label} - "))
            else:
                lines.append(f"{label}: {v}")
    elif isinstance(data, list):
        for i, item in enumerate(data, 1):
            if isinstance(item, (dict, list)):
                lines.append(_json_to_text(item, prefix=f"{prefix}{i}. "))
            else:
                lines.append(f"{prefix}{i}. {item}")
    else:
        lines.append(f"{prefix}{data}")
    return "\n".join(lines)

class VectorStoreService:
    def __init__(self):
        logger.info("Initializing lightweight hash-based embeddings (no PyTorch needed)")
        self.embeddings = SimpleHashEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        self.vector_store: Optional[FAISS] = None

    def load_data(self) -> List[Document]:
        documents = []
        if not CONTEXT_DIR.exists():
            logger.warning(f"Context directory not found at {CONTEXT_DIR}")
            return documents

        for file_path in sorted(CONTEXT_DIR.iterdir()):
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()

            if suffix in [".txt", ".md"]:
                try:
                    content = file_path.read_text(encoding="utf-8").strip()
                    if content:
                        # Boost identity file so it's always retrieved
                        repeat = 3 if "identity" in file_path.name.lower() else 1
                        for _ in range(repeat):
                            documents.append(Document(
                                page_content=content,
                                metadata={"source": file_path.name, "type": "txt"}
                            ))
                        logger.info(f"Loaded TXT/MD context: {file_path.name}")
                except Exception as e:
                    logger.warning(f"Could not load {file_path.name}: {e}")

            elif suffix == ".json":
                try:
                    data = json.loads(file_path.read_text(encoding="utf-8"))
                    text = _json_to_text(data)
                    if not text.strip():
                        continue

                    documents.append(Document(
                        page_content=text,
                        metadata={"source": file_path.name, "type": "json"}
                    ))
                    logger.info(f"Loaded JSON context: {file_path.name}")
                except Exception as e:
                    logger.warning(f"Could not load {file_path.name}: {e}")

        return documents

    def create_vector_store(self) -> FAISS:
        docs = self.load_data()
        
        if not docs:
            logger.warning("No documents found. Creating placeholder vector store.")
            self.vector_store = FAISS.from_texts(
                ["NeuroScan AI Assistant. No additional data available."],
                self.embeddings
            )
        else:
            chunks = self.text_splitter.split_documents(docs)
            logger.info(f"Building vector store from {len(chunks)} chunks...")
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)

        return self.vector_store

    def get_retriever(self, k: int = 5):
        if not self.vector_store:
            raise RuntimeError("Vector store not initialized.")
        return self.vector_store.as_retriever(search_kwargs={"k": k})
