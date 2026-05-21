# import io
# import pdfplumber
# import pytesseract
# from PIL import Image
# import pytesseract
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# def extract_from_pdf_bytes(pdf_bytes: bytes) -> tuple[str, bool]:
#     """
#     Extrait le texte d'un PDF depuis des bytes.
#     - PDF numérique  → pdfplumber (direct)
#     - PDF scanné     → OCR via Tesseract (fallback automatique)
#     Retourne (texte, used_ocr)
#     """
#     text_chunks = []
#     used_ocr = False

#     with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
#         for i, page in enumerate(pdf.pages):
#             page_text = page.extract_text()

#             if page_text and page_text.strip():
#                 # PDF numérique → texte direct
#                 text_chunks.append(page_text.strip())
#             else:
#                 # PDF scanné → OCR
#                 img = page.to_image(resolution=200).original
#                 ocr_text = pytesseract.image_to_string(img, lang="fra+ita+eng")
#                 if ocr_text.strip():
#                     text_chunks.append(f"[OCR page {i+1}]\n{ocr_text.strip()}")
#                     used_ocr = True

#     return "\n\n".join(text_chunks), used_ocr


# def extract_from_pdf_file(filepath: str) -> tuple[str, bool]:
#     """
#     Extrait le texte d'un fichier PDF local (chemin absolu ou relatif).
#     Retourne (texte, used_ocr)
#     """
#     with open(filepath, "rb") as f:
#         return extract_from_pdf_bytes(f.read())

import io
import pdfplumber
import pytesseract
from PIL import Image

# ⚠️ Doit être défini avant tout appel OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_from_pdf_bytes(pdf_bytes: bytes) -> tuple[str, bool]:
    text_chunks = []
    used_ocr = False

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()

            if page_text and page_text.strip():
                text_chunks.append(page_text.strip())
            else:
                img = page.to_image(resolution=200).original
                ocr_text = pytesseract.image_to_string(img, lang="fra+ita+eng")
                if ocr_text.strip():
                    text_chunks.append(f"[OCR page {i+1}]\n{ocr_text.strip()}")
                    used_ocr = True

    return "\n\n".join(text_chunks), used_ocr

def extract_from_pdf_file(filepath: str) -> tuple[str, bool]:
    with open(filepath, "rb") as f:
        return extract_from_pdf_bytes(f.read())