from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def create_order_pdf(filepath: str):
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "BON DE COMMANDE - Gustomio")

    c.setFont("Helvetica", 11)
    lines = [
        "Client : Mario Rossi",
        "Email : mario.rossi@gustomio.it",
        "Date de livraison : 30/05/2026",
        "Notes : Livraison avant 10h, fragile",
        "",
        "PRODUITS :",
        "- Huile d'olive extra vierge : 5 litres",
        "- Parmesan 24 mois         : 2 kg",
        "- Pâtes Barilla spaghetti  : 10 pièces",
        "- Truffe noire             : 200 g",
        "- Vin Chianti              : 6 bouteilles",
    ]
    y = height - 100
    for line in lines:
        c.drawString(50, y, line)
        y -= 20

    c.save()
    print(f"PDF créé : {filepath}")

if __name__ == "__main__":
    import os
    os.makedirs("tests/fixtures", exist_ok=True)
    create_order_pdf("tests/fixtures/commande_fictive.pdf")