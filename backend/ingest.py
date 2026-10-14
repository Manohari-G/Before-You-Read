import json
import shutil
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma

from rag.embeddings import GeminiEmbeddings
from rag.retriever import CHROMA_DIR, COLLECTION_NAME, build_documents


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "books.json"


def main() -> None:
    # Load environment variables from backend/.env
    load_dotenv(BASE_DIR / ".env")

    # Load book knowledge base
    with DATA_FILE.open("r", encoding="utf-8") as f:
        books = json.load(f)

    print(f"Found {len(books)} books in knowledge base.")

    # Remove old ChromaDB if it exists
    if CHROMA_DIR.exists():
        print(f"Removing old ChromaDB: {CHROMA_DIR}")
        shutil.rmtree(CHROMA_DIR)

    # Convert books into LangChain documents/chunks
    documents = build_documents(books)

    print(
        f"Loaded {len(books)} books and created "
        f"{len(documents)} chunks."
    )

    # Create new ChromaDB
    print("Creating ChromaDB and generating embeddings...")
    print("This may take a little while.")

    Chroma.from_documents(
        documents=documents,
        embedding=GeminiEmbeddings(),
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
    )

    print()
    print("=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"Books      : {len(books)}")
    print(f"Chunks     : {len(documents)}")
    print(f"Collection : {COLLECTION_NAME}")
    print(f"ChromaDB   : {CHROMA_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()