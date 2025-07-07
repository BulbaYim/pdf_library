import PyPDF2
from pathlib import Path
from typing import Optional

def extract_text_from_pdf(pdf_path: Path, max_pages: int = 5) -> Optional[str]:
    """
    Extract text from the first N pages of a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        max_pages: Maximum number of pages to extract (default: 5)
    
    Returns:
        Extracted text as string, or None if extraction fails
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page_num in range(min(len(pdf_reader.pages), max_pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            
            return text.strip()
            
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return None

def first_n_pages_to_text(pdf_path: Path, n: int = 5) -> str:
    result = extract_text_from_pdf(pdf_path, max_pages=n)
    return result if result else "" 