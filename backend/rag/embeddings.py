import os
from typing import List

from google import genai
from google.genai import types
from langchain_core.embeddings import Embeddings


class GeminiEmbeddings(Embeddings):
    """Small LangChain adapter around Google's current GenAI embedding API."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is missing. Add it to backend/.env")
        self.client = genai.Client(api_key=self.api_key)

    def _embed(self, text: str, task: str) -> List[float]:
        prepared = f"task: {task} | query: {text}"
        result = self.client.models.embed_content(
            model=self.model,
            contents=prepared,
            config=types.EmbedContentConfig(output_dimensionality=768),
        )
        if not result.embeddings or not result.embeddings[0].values:
            raise RuntimeError("Gemini returned an empty embedding.")
        return list(result.embeddings[0].values)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        prepared = [f"title: none | text: {text}" for text in texts]
        result = self.client.models.embed_content(
            model=self.model,
            contents=prepared,
            config=types.EmbedContentConfig(output_dimensionality=768),
        )
        embeddings = [list(item.values or []) for item in result.embeddings]
        if len(embeddings) != len(texts) or any(not item for item in embeddings):
            raise RuntimeError("Gemini returned incomplete document embeddings.")
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text, "search result")
