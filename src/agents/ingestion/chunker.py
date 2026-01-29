"""
Text chunking for RAG (Retrieval-Augmented Generation).
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class TextChunker:
    """Chunks text into smaller pieces for vector storage."""

    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text:
            return []

        # Clean text
        text = self._clean_text(text)

        # Split into chunks
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                end = self._find_sentence_boundary(text, end)

            chunk_text = text[start:end]
            chunk_metadata = {
                **(metadata or {}),
                "chunk_index": len(chunks),
                "char_start": start,
                "char_end": end,
            }

            chunks.append({
                "text": chunk_text,
                "metadata": chunk_metadata,
            })

            # Move start position with overlap
            start = end - self.chunk_overlap

        return chunks

    def chunk_by_paragraphs(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Chunk text by paragraphs with size limit.

        Args:
            text: Text to chunk
            metadata: Optional metadata

        Returns:
            List of chunk dictionaries
        """
        if not text:
            return []

        # Split by paragraph
        paragraphs = re.split(r"\n\s*\n", text)
        chunks = []
        current_chunk = []
        current_size = 0

        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue

            para_size = len(para)

            # If single paragraph exceeds chunk size, split it
            if para_size > self.chunk_size:
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))
                    current_chunk = []
                    current_size = 0

                # Split large paragraph
                sub_chunks = self.chunk_text(para, {**(metadata or {}), "paragraph_index": i})
                chunks.extend(sub_chunks)
                continue

            # Check if adding this paragraph would exceed limit
            if current_size + para_size > self.chunk_size and current_chunk:
                chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size + 2  # +2 for newline

        # Add remaining chunk
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))

        return chunks

    def chunk_by_headings(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Chunk text using headings as boundaries.

        Args:
            text: Text to chunk
            metadata: Optional metadata

        Returns:
            List of chunk dictionaries
        """
        if not text:
            return []

        # Find all headings (lines that look like headings)
        heading_pattern = r"^(#{1,6}\s+.+|[A-Z][^\.]+:\s*$|\n[A-Z][^\.]+:\s*$)"
        matches = list(re.finditer(heading_pattern, text, re.MULTILINE))

        if not matches:
            # No headings found, fall back to paragraph chunking
            return self.chunk_by_paragraphs(text, metadata)

        chunks = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            section_text = text[start:end].strip()
            if section_text:
                chunk_metadata = {
                    **(metadata or {}),
                    "chunk_index": i,
                    "heading": match.group().strip(),
                }
                chunks.append({
                    "text": section_text,
                    "metadata": chunk_metadata,
                })

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Replace multiple whitespace with single space
        text = re.sub(r"\s+", " ", text)
        # Remove control characters
        text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)
        return text.strip()

    def _find_sentence_boundary(self, text: str, position: int) -> int:
        """Find the nearest sentence boundary after position."""
        # Look for sentence endings
        sentence_ends = re.finditer(r"[.!?]\s+", text[position:])
        try:
            match = next(sentence_ends)
            return position + match.end()
        except StopIteration:
            return position

    def _create_chunk(
        self,
        text_parts: List[str],
        metadata: Optional[Dict[str, Any]],
        index: int,
    ) -> Dict[str, Any]:
        """Create a chunk from text parts."""
        text = "\n\n".join(text_parts)
        return {
            "text": text,
            "metadata": {
                **(metadata or {}),
                "chunk_index": index,
            },
        }


def chunk_for_rag(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    strategy: str = "auto",
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function for RAG chunking.

    Args:
        text: Text to chunk
        chunk_size: Maximum chunk size
        chunk_overlap: Overlap between chunks
        strategy: Chunking strategy ("auto", "paragraphs", "headings")
        metadata: Optional metadata

    Returns:
        List of chunks
    """
    chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    if strategy == "headings":
        return chunker.chunk_by_headings(text, metadata)
    elif strategy == "paragraphs":
        return chunker.chunk_by_paragraphs(text, metadata)
    else:
        # Auto - detect best strategy
        if re.search(r"^#{1,6}\s+", text, re.MULTILINE):
            return chunker.chunk_by_headings(text, metadata)
        elif re.search(r"\n\s*\n", text):
            return chunker.chunk_by_paragraphs(text, metadata)
        else:
            return chunker.chunk_text(text, metadata)
