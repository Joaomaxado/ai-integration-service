import hashlib
import math
import re
from dataclasses import dataclass

from app.domain.schemas import Chunk


@dataclass(frozen=True)
class IndexedDocument:
    document_id: str
    office_id: str
    title: str
    source_url: str | None
    chunks: tuple[Chunk, ...]


class RAGService:

    def __init__(self) -> None:
        self.documents: dict[str, IndexedDocument] = {}

    def create_chunks(self, text: str, *, size: int = 1000, overlap: int = 100) -> list[str]:
        if size <= 0 or overlap < 0 or overlap >= size:
            raise ValueError("size deve ser positivo e overlap deve ser menor que size")
        return [text[start:start + size] for start in range(0, len(text), size - overlap)]

    def _embedding(self, text: str) -> list[float]:
        vector = [0.0] * 32
        for token in re.findall(r"\w+", text.casefold()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            vector[digest[0] % len(vector)] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [round(value / norm, 6) for value in vector]

    def ingest(self, *, document_id: str, office_id: str, title: str, text: str,
               source_url: str | None = None) -> IndexedDocument:
        chunks = tuple(
            Chunk(chunk_id=f"{document_id}:{position}", document_id=document_id,
                  office_id=office_id, text=chunk_text, position=position,
                  embedding=self._embedding(chunk_text))
            for position, chunk_text in enumerate(self.create_chunks(text))
        )
        document = IndexedDocument(document_id, office_id, title, source_url, chunks)
        self.documents[document_id] = document
        return document

    async def get_context(self, question: str, office_id: str, document_ids: list[str] | None = None,
                          limit: int = 5) -> list[Chunk]:
        query = self._embedding(question)
        allowed = set(document_ids or self.documents)
        candidates = [chunk for document in self.documents.values()
                      if document.office_id == office_id and document.document_id in allowed
                      for chunk in document.chunks]
        return sorted(candidates, key=lambda chunk: sum(a * b for a, b in zip(query, chunk.embedding)),
                      reverse=True)[:limit]
    