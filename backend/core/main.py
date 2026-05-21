import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from order_extraction import extract_order_from_pdf_file

# Dossier fixtures
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'tests', 'fixtures')

# Récupère tous les PDFs du dossier
pdfs = [f for f in os.listdir(FIXTURES_DIR) if f.endswith('.pdf')]

if not pdfs:
    print("Aucun PDF trouvé dans tests/fixtures/")
else:
    for filename in pdfs:
        path = os.path.join(FIXTURES_DIR, filename)
        print(f"\n{'='*50}")
        print(f"📄 Fichier : {filename}")
        print('='*50)
        order = extract_order_from_pdf_file(path)
        print(order.to_summary())