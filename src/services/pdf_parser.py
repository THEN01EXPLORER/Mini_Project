"""
PDF parsing service with magic byte validation.

Why pdfplumber instead of PyPDF2?
1. PyPDF2 chokes on multi-column layouts (very common in modern resumes)
2. pdfplumber preserves reading order better
3. Better handling of tables (experience sections often use tables)
4. PyPDF2's text extraction is notoriously unreliable

Security note: We validate PDF magic bytes, not just file extension.
A renamed .exe or .html file won't pass validation.
"""

import io
import re
from typing import BinaryIO

import pdfplumber

from src.core.exceptions import InvalidFileError, PDFParsingError
from src.core.logging import logger


# PDF magic bytes - all PDFs start with this signature
# Fun fact: this translates to "%PDF" in ASCII
PDF_MAGIC_BYTES = b"%PDF"

# Max file size we'll process (10MB) - larger files are usually scanned images
# that won't parse well anyway
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def validate_pdf_magic_bytes(file_content: bytes) -> bool:
    """
    Check if file starts with PDF magic bytes.
    
    This catches the classic "rename malware.exe to resume.pdf" attack.
    Most tutorials skip this, which is why AI-generated code often has this hole.
    
    Args:
        file_content: Raw bytes of the uploaded file
        
    Returns:
        True if valid PDF signature, False otherwise
    """
    if len(file_content) < 4:
        return False
    
    return file_content[:4] == PDF_MAGIC_BYTES


def clean_extracted_text(raw_text: str) -> str:
    """
    Clean and normalize extracted PDF text.
    
    PDFs have all kinds of weird whitespace artifacts.
    This function normalizes them for better LLM processing.
    """
    if not raw_text:
        return ""
    
    # Replace multiple spaces/tabs with single space
    text = re.sub(r"[ \t]+", " ", raw_text)
    
    # Replace 3+ newlines with double newline (preserve paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    
    # Remove any null bytes (sometimes appear in corrupted PDFs)
    text = text.replace("\x00", "")
    
    # Final trim
    text = text.strip()
    
    return text


def parse_pdf(file_content: bytes, filename: str = "resume.pdf") -> str:
    """
    Parse PDF and extract cleaned text content.
    
    Args:
        file_content: Raw PDF bytes
        filename: Original filename (for error messages)
        
    Returns:
        Cleaned text content from PDF
        
    Raises:
        InvalidFileError: If file is not a valid PDF
        PDFParsingError: If PDF cannot be parsed
    """
    logger.info(f"Parsing PDF: {filename} ({len(file_content)} bytes)")
    
    # === Validation Layer ===
    
    # Check file size first (fast check)
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise InvalidFileError(
            f"File too large: {len(file_content)} bytes. Max allowed: {MAX_FILE_SIZE_BYTES} bytes.",
            details={"filename": filename, "size": len(file_content)}
        )
    
    # Check magic bytes (security check)
    if not validate_pdf_magic_bytes(file_content):
        raise InvalidFileError(
            "File is not a valid PDF. Magic bytes mismatch.",
            details={
                "filename": filename,
                "expected_magic": PDF_MAGIC_BYTES.hex(),
                "actual_magic": file_content[:4].hex() if len(file_content) >= 4 else "too short"
            }
        )
    
    # === Extraction Layer ===
    
    try:
        # Wrap bytes in file-like object for pdfplumber
        pdf_file = io.BytesIO(file_content)
        
        all_text_parts: list[str] = []
        
        with pdfplumber.open(pdf_file) as pdf:
            logger.debug(f"PDF has {len(pdf.pages)} pages")
            
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                
                if page_text:
                    all_text_parts.append(page_text)
                    logger.debug(f"Page {page_num}: extracted {len(page_text)} chars")
                else:
                    # Scanned page with no text layer - common issue
                    logger.warning(f"Page {page_num}: no text extracted (possibly scanned image)")
        
        if not all_text_parts:
            raise PDFParsingError(
                "No text could be extracted from PDF. It may be a scanned image without OCR.",
                details={"filename": filename}
            )
        
        # Join pages with double newline
        raw_text = "\n\n".join(all_text_parts)
        cleaned_text = clean_extracted_text(raw_text)
        
        logger.info(f"Successfully extracted {len(cleaned_text)} chars from {filename}")
        
        return cleaned_text
        
    except InvalidFileError:
        raise  # Re-raise our own exceptions
    except PDFParsingError:
        raise
    except Exception as e:
        # Catch pdfplumber errors and wrap them
        logger.error(f"PDF parsing failed for {filename}: {e}")
        raise PDFParsingError(
            f"Failed to parse PDF: {str(e)}",
            details={"filename": filename, "error_type": type(e).__name__}
        )
