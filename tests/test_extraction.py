import sys
import os
from dotenv import load_dotenv
load_dotenv()

# Pointe explicitement vers backend/core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'core'))

from order_extraction import extract_order_from_pdf_file
from text_extractor import extract_from_pdf_file, extract_from_pdf_bytes 
def test_basic_order():
    PDF_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'commande_fictive.pdf')
    order = extract_order_from_pdf_file(PDF_PATH)
    print(order.to_summary())

    # Assertions basiques
    assert order.customer_name is not None, "Nom client manquant"
    assert len(order.lines) > 0, "Aucune ligne de commande extraite"
    assert any(l.produit.lower().find("truffe") != -1 for l in order.lines), "Truffe non trouvée"

    print("✅ Test OK")

if __name__ == "__main__":
    test_basic_order()