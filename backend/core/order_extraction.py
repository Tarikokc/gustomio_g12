import re
import json
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from groq import Groq
import os
import sys  # ← ajoute
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from text_extractor import extract_from_pdf_file, extract_from_pdf_bytes

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# ── Schéma de sortie ──────────────────────────────────────────────────────────

UNIT_ALIASES = {
    "pièce": "piece", "pièces": "piece", "pc": "piece", "pcs": "piece",
    "unité": "piece", "unités": "piece",
    "kilo": "kg", "kilogramme": "kg",
    "litre": "l", "litres": "l",
    "gramme": "g", "grammes": "g",
    "boîte": "boite", "bouteilles": "bouteille",
}

class OrderLine(BaseModel):
    produit: str
    # quantite: float = Field(..., gt=0)
    quantite: Optional[float] = Field(default=None, gt=0)
    unite: str = Field(default="piece")

    @field_validator("unite", mode="before")
    @classmethod
    def normalize_unit(cls, v):
        v = str(v).lower().strip()
        return UNIT_ALIASES.get(v, v)

class ExtractedOrder(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    delivery_date: Optional[str] = None
    notes: Optional[str] = None
    lines: List[OrderLine] = []

    def to_summary(self):
        lines_str = "\n".join(
            f"  - {l.produit} : {l.quantite} {l.unite}" for l in self.lines
        )
        return (
            f"Client       : {self.customer_name or 'Inconnu'}\n"
            f"Livraison    : {self.delivery_date or 'Non précisée'}\n"
            f"Nb lignes    : {len(self.lines)}\n"
            f"{lines_str}"
        )

# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
Tu extrais des commandes fournisseurs depuis du texte brut (PDF épicerie fine italienne).
Retourne UNIQUEMENT du JSON valide, sans markdown, sans explication.
Ne jamais inventer de produit ou de quantité absent du texte.
""".strip()

EXTRACTION_PROMPT = """
Extrait la commande depuis ce texte PDF.

JSON attendu (STRICT, sans ```json) :
{{
  "customer_name": "nom ou null",
  "customer_email": "email ou null",
  "delivery_date": "date ou null",
  "notes": "remarques ou null",
  "lines": [
    {{
      "produit": "nom produit",
      "quantite": nombre,
      "unite": "kg | g | l | ml | piece | carton | boite | bouteille"
    }}
  ]
}}

TEXTE PDF :
\"\"\"
{text}
\"\"\"
""".strip()

# ── Extraction ────────────────────────────────────────────────────────────────

def _clean_json(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        return raw[start:end+1]
    return raw

def extract_order_from_text(text: str) -> ExtractedOrder:
    """Envoie le texte brut à l'IA et retourne l'order structuré."""
    if not text.strip():
        return ExtractedOrder()

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": EXTRACTION_PROMPT.format(text=text[:6000])}
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content
    data = json.loads(_clean_json(raw))
    return ExtractedOrder.model_validate(data)

# ── Points d'entrée ───────────────────────────────────────────────────────────

def extract_order_from_pdf_file(filepath: str) -> ExtractedOrder:
    """Fichier PDF local → commande structurée."""
    text, used_ocr = extract_from_pdf_file(filepath)
    print(f"[PDF] OCR utilisé : {used_ocr} | {len(text)} caractères extraits")
    return extract_order_from_text(text)


def extract_order_from_pdf_bytes(pdf_bytes: bytes) -> ExtractedOrder:
    """PDF bytes (upload appli) → commande structurée."""
    text, used_ocr = extract_from_pdf_bytes(pdf_bytes)
    print(f"[PDF] OCR utilisé : {used_ocr} | {len(text)} caractères extraits")
    return extract_order_from_text(text)