import sys
import os
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'core'))

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from order_extraction import extract_order_from_pdf_file, extract_order_from_text

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')
os.makedirs(FIXTURES_DIR, exist_ok=True)

# ── Générateurs de PDFs ───────────────────────────────────────────────────────

def make_pdf(filename, lignes, titre="BON DE COMMANDE - Gustomio"):
    path = os.path.join(FIXTURES_DIR, filename)
    c = canvas.Canvas(path, pagesize=A4)
    _, h = A4
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, h - 50, titre)
    c.setFont("Helvetica", 11)
    y = h - 90
    for ligne in lignes:
        if y < 60:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = h - 50
        c.drawString(50, y, ligne)
        y -= 20
    c.save()
    return path

# ── Cas 1 : Données manquantes (pas de client, pas de date) ──────────────────

def test_donnees_manquantes():
    print("\n=== CAS 1 : Données manquantes ===")
    path = make_pdf("manquant.pdf", [
        "- Huile d'olive : 3 litres",
        "- Parmesan : 1 kg",
    ])
    order = extract_order_from_pdf_file(path)
    print(order.to_summary())
    assert order.customer_name is None, "Devrait être None"
    assert order.delivery_date is None, "Devrait être None"
    assert len(order.lines) > 0, "Des lignes doivent être extraites"
    print("✅ OK")

# ── Cas 2 : Unités inhabituelles ─────────────────────────────────────────────

def test_unites_inhabituelles():
    print("\n=== CAS 2 : Unités inhabituelles ===")
    path = make_pdf("unites.pdf", [
        "Client : Luigi Bianchi",
        "Livraison : 15/06/2026",
        "",
        "- Café arabica        : 3 cartons",
        "- Tomates séchées     : 500 grammes",
        "- Eau minérale        : 12 bouteilles",
        "- Farine 00           : 2 kilogrammes",
        "- Vinaigre balsamique : 4 pièces",
    ])
    order = extract_order_from_pdf_file(path)
    print(order.to_summary())
    unites = [l.unite for l in order.lines]
    print(f"Unités extraites : {unites}")
    assert len(order.lines) >= 4, "Au moins 4 lignes attendues"
    # Vérifie normalisation : grammes → g, kilogrammes → kg
    assert any(l.unite == "g" for l in order.lines), "grammes → g attendu"
    assert any(l.unite == "kg" for l in order.lines), "kilogrammes → kg attendu"
    print("✅ OK")

# ── Cas 3 : PDF multi-pages ──────────────────────────────────────────────────

def test_multi_pages():
    print("\n=== CAS 3 : Multi-pages ===")
    lignes = [
        "Client : Gustomio Paris",
        "Email : commandes@gustomio.fr",
        "Livraison : 01/07/2026",
        "",
        "PAGE 1 - PRODUITS SECS :",
    ] + [f"- Produit sec {i}     : {i} kg" for i in range(1, 16)] + [
        "",
        "PAGE 2 - PRODUITS FRAIS :",
    ] + [f"- Produit frais {i}   : {i*2} pieces" for i in range(1, 11)]

    path = make_pdf("multi_pages.pdf", lignes)
    order = extract_order_from_pdf_file(path)
    print(order.to_summary())
    assert order.customer_name is not None, "Nom client manquant"
    assert len(order.lines) >= 10, f"Au moins 10 lignes attendues, got {len(order.lines)}"
    print(f"✅ OK — {len(order.lines)} lignes extraites sur plusieurs pages")

# ── Cas 4 : PDF vide ─────────────────────────────────────────────────────────

def test_pdf_vide():
    print("\n=== CAS 4 : Texte vide ===")
    order = extract_order_from_text("")
    print(order.to_summary())
    assert order.lines == [], "Aucune ligne attendue"
    assert order.customer_name is None
    print("✅ OK")

# ── Cas 5 : Notes spéciales ──────────────────────────────────────────────────

def test_notes_speciales():
    print("\n=== CAS 5 : Notes spéciales ===")
    path = make_pdf("notes.pdf", [
        "Client : Francesca Marino",
        "Email : f.marino@epicerie.it",
        "Livraison : 20/06/2026",
        "Notes : Livraison urgente, appeler avant, laisser en cave si absent",
        "",
        "- Truffe blanche : 100 g",
        "- Mortadelle      : 2 kg",
    ])
    order = extract_order_from_pdf_file(path)
    print(order.to_summary())
    print(f"Notes : {order.notes}")
    assert order.notes is not None, "Notes attendues"
    assert order.customer_email is not None, "Email attendu"
    print("✅ OK")

# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_donnees_manquantes,
        test_unites_inhabituelles,
        test_multi_pages,
        test_pdf_vide,
        test_notes_speciales,
    ]
    resultats = []
    for t in tests:
        try:
            t()
            resultats.append((t.__name__, "✅ PASS"))
        except Exception as e:
            resultats.append((t.__name__, f"❌ FAIL — {e}"))

    print("\n" + "="*50)
    print("RÉSUMÉ DES TESTS")
    print("="*50)
    for nom, res in resultats:
        print(f"  {res}  {nom}")