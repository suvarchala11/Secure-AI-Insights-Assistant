"""
Loads all CSVs into pandas DataFrames and all text documents
into a FAISS vector store at startup — once, not per request.
"""
import logging
from pathlib import Path
from functools import lru_cache

import pandas as pd
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from backend.config import settings

log = logging.getLogger(__name__)


# ── CSV DataFrames ────────────────────────────────────────────────────────────

class DataStore:
    """Holds all CSV data in memory as DataFrames."""

    def __init__(self):
        self.movies: pd.DataFrame = pd.DataFrame()
        self.viewers: pd.DataFrame = pd.DataFrame()
        self.watch_activity: pd.DataFrame = pd.DataFrame()
        self.reviews: pd.DataFrame = pd.DataFrame()
        self.marketing: pd.DataFrame = pd.DataFrame()
        self.regional: pd.DataFrame = pd.DataFrame()

    def load(self):
        d = settings.data_dir
        self.movies         = pd.read_csv(d / "movies.csv")
        self.viewers        = pd.read_csv(d / "viewers.csv")
        self.watch_activity = pd.read_csv(d / "watch_activity.csv")
        self.reviews        = pd.read_csv(d / "reviews.csv")
        self.marketing      = pd.read_csv(d / "marketing_spend.csv")
        self.regional       = pd.read_csv(d / "regional_performance.csv")
        log.info("✓ All CSVs loaded into DataStore")


# Singleton — imported by tools
store = DataStore()


# ── FAISS Vector Store ────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_vector_store() -> FAISS:
    """
    Builds (or returns cached) FAISS index from docs directory.
    Uses a local HuggingFace embedding model — no API key required.
    """
    log.info("Building FAISS vector store from docs...")

    loader = DirectoryLoader(
        str(settings.docs_dir),
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=False,
    )
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(docs)

    # all-MiniLM-L6-v2: tiny (80MB), fast on CPU, good quality
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )

    vs = FAISS.from_documents(chunks, embeddings)
    log.info(f"✓ FAISS index built — {len(chunks)} chunks from {len(docs)} documents")
    return vs
