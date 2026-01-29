"""
PDF and image parser for the ingestion agent.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import fitz  # PyMuPDF
from PIL import Image
import io

from src.agents.state import DocumentType

logger = logging.getLogger(__name__)


class DocumentParser:
    """Parses PDF and image documents to extract text, tables, and images."""

    def __init__(self):
        self.supported_image_types = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}

    def parse(self, file_path: str, file_bytes: bytes) -> Dict[str, Any]:
        """
        Parse a document and extract content.

        Args:
            file_path: Path to the file
            file_bytes: Raw file bytes

        Returns:
            Dictionary with extracted content
        """
        file_ext = self._get_extension(file_path)

        if file_ext == ".pdf":
            return self._parse_pdf(file_bytes)
        elif file_ext in self.supported_image_types:
            return self._parse_image(file_bytes, file_ext)
        else:
            # Try as text file
            return self._parse_text(file_bytes)

    def _parse_pdf(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        Parse PDF document.

        Args:
            file_bytes: PDF file bytes

        Returns:
            Extracted content
        """
        result = {
            "text": "",
            "tables": [],
            "images": [],
            "metadata": {},
            "page_count": 0,
        }

        try:
            pdf_doc = fitz.open(stream=file_bytes, doc_type="pdf")
            result["page_count"] = len(pdf_doc)
            result["metadata"] = dict(pdf_doc.metadata)

            for page_num, page in enumerate(pdf_doc):
                # Extract text
                text = page.get_text("text")
                result["text"] += text + "\n\n"

                # Extract tables (basic implementation)
                tables = self._extract_tables_from_page(page)
                result["tables"].extend(tables)

                # Extract images
                images = self._extract_images_from_page(page, page_num)
                result["images"].extend(images)

            pdf_doc.close()

        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            result["error"] = str(e)

        return result

    def _extract_tables_from_page(self, page) -> List[Dict[str, Any]]:
        """
        Extract tables from a PDF page.

        Args:
            page: PyMuPDF page object

        Returns:
            List of table dictionaries
        """
        tables = []

        try:
            # Get tables using PyMuPDF's table finder
            table_finder = page.find_tables()
            for table in table_finder.tables:
                table_data = table.extract()
                if table_data:
                    tables.append({
                        "rows": table_data,
                        "bbox": table.bbox,
                    })
        except Exception as e:
            logger.debug(f"Table extraction error: {e}")

        return tables

    def _extract_images_from_page(
        self,
        page,
        page_num: int,
    ) -> List[Dict[str, Any]]:
        """
        Extract images from a PDF page.

        Args:
            page: PyMuPDF page object
            page_num: Page number

        Returns:
            List of image dictionaries
        """
        images = []

        try:
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = page.parent.extract_image(xref)

                images.append({
                    "page": page_num,
                    "index": img_index,
                    "width": base_image["width"],
                    "height": base_image["height"],
                    "colorspace": base_image["colorspace"],
                    "bpc": base_image["bpc"],
                    "ext": base_image["ext"],
                    "size": len(base_image["image"]),
                })
        except Exception as e:
            logger.debug(f"Image extraction error: {e}")

        return images

    def _parse_image(self, file_bytes: bytes, file_ext: str) -> Dict[str, Any]:
        """
        Parse image document.

        Args:
            file_bytes: Image file bytes
            file_ext: File extension

        Returns:
            Extracted content
        """
        result = {
            "text": "",
            "tables": [],
            "images": [],
            "metadata": {},
        }

        try:
            image = Image.open(io.BytesIO(file_bytes))
            result["metadata"] = {
                "format": image.format,
                "mode": image.mode,
                "width": image.width,
                "height": image.height,
            }
            # Store image bytes for OCR/vision processing
            result["images"].append({
                "width": image.width,
                "height": image.height,
                "format": image.format,
            })

        except Exception as e:
            logger.error(f"Error parsing image: {e}")
            result["error"] = str(e)

        return result

    def _parse_text(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        Parse text document.

        Args:
            file_bytes: Text file bytes

        Returns:
            Extracted content
        """
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1")

        return {
            "text": text,
            "tables": [],
            "images": [],
            "metadata": {"type": "text"},
        }

    def _get_extension(self, file_path: str) -> str:
        """Get file extension from path."""
        import os
        _, ext = os.path.splitext(file_path)
        return ext.lower()


def extract_text_from_file(file_path: str, file_bytes: bytes) -> str:
    """
    Convenience function to extract text from a file.

    Args:
        file_path: Path to the file
        file_bytes: File bytes

    Returns:
        Extracted text
    """
    parser = DocumentParser()
    result = parser.parse(file_path, file_bytes)
    return result.get("text", "")
