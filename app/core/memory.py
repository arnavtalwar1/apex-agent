"""
RAG-ready episodic memory and semantic reflection recall.
Enables agents to retrieve prior solutions, avoid past errors, and adapt strategies.
"""

import math
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MemoryEntry:
    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    score: float = 0.0


def _tokenize(text: str) -> set[str]:
    """Extracts normalized alphabetic words for token similarity matching."""
    return set(re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower()))


def _compute_similarity(query_tokens: set[str], doc_tokens: set[str]) -> float:
    """Computes Jaccard/Overlap coefficient between query and document tokens."""
    if not query_tokens or not doc_tokens:
        return 0.0
    intersection = len(query_tokens.intersection(doc_tokens))
    union = len(query_tokens.union(doc_tokens))
    return intersection / union if union > 0 else 0.0


class InMemoryVectorStore:
    """
    High-performance in-memory semantic memory store.
    Features text similarity scoring with zero external dependencies,
    designed with standard vector interfaces for pluggable drop-in Chroma/pgvector backing.
    """

    def __init__(self):
        self._entries: list[MemoryEntry] = []

    def add(self, content: str, metadata: Optional[dict[str, Any]] = None) -> str:
        """Stores a new memory item."""
        if not content.strip():
            return ""
        entry_id = str(uuid.uuid4())
        entry = MemoryEntry(
            id=entry_id,
            content=content.strip(),
            metadata=metadata or {},
        )
        self._entries.append(entry)
        return entry_id

    def search(self, query: str, limit: int = 3, filter_type: Optional[str] = None) -> list[MemoryEntry]:
        """
        Retrieves the top-k most semantically relevant memories for a given query.
        """
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scored_entries: list[tuple[float, MemoryEntry]] = []
        for entry in self._entries:
            if filter_type and entry.metadata.get("type") != filter_type:
                continue

            doc_tokens = _tokenize(entry.content)
            score = _compute_similarity(query_tokens, doc_tokens)
            if score > 0.05:  # Relevance threshold
                scored_entries.append((score, entry))

        # Sort descending by relevance score
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, entry in scored_entries[:limit]:
            entry.score = round(score, 3)
            results.append(entry)
        return results

    def recall_reflection_insights(self, goal: str, limit: int = 2) -> list[str]:
        """
        Recalls prior verbal critiques and failure resolutions related to the current goal.
        """
        matches = self.search(goal, limit=limit, filter_type="reflection")
        return [entry.content for entry in matches]

    def clear(self) -> None:
        self._entries.clear()


# Global memory instance
agent_memory = InMemoryVectorStore()
