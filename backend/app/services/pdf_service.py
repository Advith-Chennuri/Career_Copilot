import io
import logging
import pypdf

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts text from PDF file bytes.
    
    Args:
        file_bytes (bytes): The binary content of the uploaded PDF file.
        
    Returns:
        str: The extracted and cleaned text from the PDF.
        
    Raises:
        ValueError: If extraction fails or if the PDF yields no extractable text.
    """
    try:
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        extracted_text = []
        
        for idx, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text:
                # Clean up any potential double carriage returns or trailing spaces
                cleaned = "\n".join([line.strip() for line in page_text.splitlines() if line.strip()])
                if cleaned:
                    extracted_text.append(cleaned)
                    
        full_text = "\n\n".join(extracted_text)
        if not full_text.strip():
            raise ValueError("No text could be extracted. The PDF may be empty, image-only (scanned), or encrypted.")
            
        return full_text
    except Exception as e:
        logger.exception("Error extracting text from PDF")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")
