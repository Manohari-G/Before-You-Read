from pathlib import Path
from typing import List

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .embeddings import GeminiEmbeddings


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

# Store ChromaDB outside OneDrive.
# This avoids Windows permission/sync issues with OneDrive.
CHROMA_DIR = Path.home() / "before-you-read-chroma"

COLLECTION_NAME = "before-you-read-books"


# ---------------------------------------------------------
# BOOK FORMATTING
# ---------------------------------------------------------

def format_book(book: dict) -> str:
    """
    Convert one book record into text that can be embedded
    and retrieved by the RAG system.
    """

    return f"""Title: {book['title']}
Author: {book['author']}
Genre: {book['genre']}
Sub-genre: {book['sub_genre']}
Approximate pages: {book['pages']}
Writing difficulty: {book['writing_difficulty']}
Pacing: {book['pacing']}
Twist level: {book['twist_level']}/5
Emotional intensity: {book['emotional_intensity']}/5
Themes: {', '.join(book['themes'])}
Mood/atmosphere: {book['mood']}
Reader type: {book['reader_type']}
Spoiler-free description: {book['spoiler_free_description']}
Similar books: {', '.join(book['similar_books'])}
Why readers may like it: {book['why_readers_like_it']}
Detailed information: {book['detailed_info']}"""


# ---------------------------------------------------------
# VECTOR STORE
# ---------------------------------------------------------

def get_vectorstore() -> Chroma:
    """
    Connect to the existing ChromaDB collection.
    """

    embeddings = GeminiEmbeddings()

    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
    )


# ---------------------------------------------------------
# DOCUMENT CREATION
# ---------------------------------------------------------

def build_documents(books: List[dict]) -> List[Document]:
    """
    Convert book records into LangChain documents
    and split them into smaller chunks for retrieval.
    """

    documents = []

    for book in books:
        documents.append(
            Document(
                page_content=format_book(book),
                metadata={
                    "title": book["title"],
                    "author": book["author"],
                    "genre": book["genre"],
                },
            )
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=120,
    )

    return splitter.split_documents(documents)


# ---------------------------------------------------------
# RETRIEVAL
# ---------------------------------------------------------

def retrieve(query: str, k: int = 8) -> List[Document]:
    """
    Retrieve the most relevant book chunks from ChromaDB.
    """

    vectorstore = get_vectorstore()

    return vectorstore.similarity_search(
        query,
        k=k,
    )


# ---------------------------------------------------------
# CONTEXT CREATION
# ---------------------------------------------------------

def context_from_documents(documents: List[Document]) -> str:
    """
    Combine retrieved documents into a context string
    that will be passed to Gemini.
    """

    if not documents:
        return "No relevant books were retrieved from the current collection."

    blocks = []
    seen = set()

    for doc in documents:

        title = doc.metadata.get(
            "title",
            "Unknown title",
        )

        key = (
            title,
            doc.page_content[:100],
        )

        if key in seen:
            continue

        seen.add(key)

        blocks.append(doc.page_content)

    return "\n\n--- BOOK RECORD ---\n\n".join(blocks)