import sys
import os
import time
import json

from imapclient import IMAPClient
import pyzmail
from groq import Groq

sys.path.insert(0, os.path.dirname(__file__))
from order_extraction import extract_order_from_pdf_file, extract_order_from_pdf_bytes
from odoo_sender import send_order_to_odoo
from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────

GMAIL             = "gustomio.g12@gmail.com"
GMAIL_APP_PASSWORD = "bxls xqra arwa tljs"
load_dotenv()                    # Charge le .env
GROQ_API_KEY       = os.getenv("GROQ_API_KEY")
FIXTURES_DIR       = os.path.join(os.path.dirname(__file__), "..", "..", "tests", "fixtures")

client_ai = Groq(api_key=GROQ_API_KEY)

# ── Helpers email (collègue) ──────────────────────────────────────────────────

def pastille(score):
    if score >= 90:
        return "🟢"
    elif score >= 75:
        return "🟠"
    return "🔴"

def nettoyer_json(reponse):
    reponse = reponse.strip()
    if "```json" in reponse:
        reponse = reponse.split("```json")[1].split("```")[0].strip()
    elif "```" in reponse:
        reponse = reponse.split("```")[1].split("```")[0].strip()
    debut = reponse.find("{")
    fin   = reponse.rfind("}")
    if debut != -1 and fin != -1:
        return reponse[debut:fin + 1]
    return reponse

def analyser_email(email_text: str) -> str:
    prompt = f"""
Tu es un système d'analyse de commandes pour GUSTOMIO.
Analyse cet email et retourne uniquement un JSON valide avec cette structure :

{{
  "texte_original": "",
  "client": {{"code_client": "", "nom_client": "", "score_confiance": 0}},
  "adresse_livraison": {{"valeur": "", "score_confiance": 0}},
  "date_livraison": {{"valeur": "", "score_confiance": 0}},
  "articles": [
    {{"code_article": "", "designation": "", "quantite": 0, "unite": "", "score_confiance": 0}}
  ],
  "champs_manquants": [],
  "score_global": 0,
  "statut": ""
}}

Règles :
- Si une donnée manque, mets null.
- score entre 0 et 100.
- statut = validee_auto si score_global >= 90.
- statut = a_valider si score_global >= 75 et < 90.
- statut = rejetee si score_global < 75.
- Ne retourne AUCUN texte hors du JSON.

Email :
{email_text}
"""
    response = client_ai.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

def afficher_resultat(json_commande: str):
    json_commande = nettoyer_json(json_commande)
    data = json.loads(json_commande)

    print("\n📩 TEXTE ORIGINAL\n")
    print(data.get("texte_original"))

    client  = data.get("client", {})
    adresse = data.get("adresse_livraison", {})
    date    = data.get("date_livraison", {})

    print("\n📦 EXTRACTION STRUCTURÉE\n")
    print(f"{pastille(client.get('score_confiance', 0))} CLIENT : {client.get('nom_client')} | CODE : {client.get('code_client')} | CONFIANCE : {client.get('score_confiance')}%")
    print(f"{pastille(date.get('score_confiance', 0))} DATE : {date.get('valeur')} | CONFIANCE : {date.get('score_confiance')}%")
    print(f"{pastille(adresse.get('score_confiance', 0))} ADRESSE : {adresse.get('valeur')} | CONFIANCE : {adresse.get('score_confiance')}%")

    print("\nARTICLES :\n")
    for article in data.get("articles", []):
        score = article.get("score_confiance", 0)
        print(
            f"{pastille(score)} {article.get('designation')} | "
            f"CODE : {article.get('code_article')} | "
            f"QTÉ : {article.get('quantite')} {article.get('unite')} | "
            f"CONFIANCE : {score}%"
        )

    print("\n📊 SCORE GLOBAL\n")
    print(f"{pastille(data.get('score_global', 0))} SCORE GLOBAL : {data.get('score_global')}%")
    print(f"STATUT : {data.get('statut')}")
    print(f"CHAMPS MANQUANTS : {data.get('champs_manquants')}")

def traiter_piece_jointe_pdf(part):
    """Traite une pièce jointe PDF : extraction + envoi Odoo."""
    filename = part.filename
    if not filename or not filename.lower().endswith(".pdf"):
        return

    print(f"\n📄 PDF DÉTECTÉ : {filename}")
    pdf_bytes = part.get_payload()

    order = extract_order_from_pdf_bytes(pdf_bytes)
    print("\n📄 COMMANDE EXTRAITE DU PDF\n")
    print(order.to_summary())

    send_order_to_odoo(order)

# ── Lecture mails (collègue) ──────────────────────────────────────────────────

def lire_mails():
    with IMAPClient("imap.gmail.com", ssl=True) as server:
        server.login(GMAIL, GMAIL_APP_PASSWORD)
        server.select_folder("INBOX")

        messages = server.search(["UNSEEN"])
        if not messages:
            print("Aucun nouveau mail.")
            return

        for email_id in messages:
            raw_message = server.fetch([email_id], ["BODY[]"])
            message = pyzmail.PyzMessage.factory(raw_message[email_id][b"BODY[]"])

            if message.text_part:
                email_text = message.text_part.get_payload().decode(message.text_part.charset)
            elif message.html_part:
                email_text = message.html_part.get_payload().decode(message.html_part.charset)
            else:
                email_text = ""

            print("\n================ EMAIL REÇU ================\n")
            print(email_text)

            if email_text.strip():
                json_commande = analyser_email(email_text)
                print("\n================ JSON EMAIL ================\n")
                print(json_commande)
                afficher_resultat(json_commande)

            print("\n================ PIÈCES JOINTES ================\n")
            for part in message.mailparts:
                traiter_piece_jointe_pdf(part)

            server.add_flags(email_id, ["\\Seen"])

# ── Traitement PDF locaux (fixtures) ─────────────────────────────────────────

def traiter_pdfs_locaux():
    if not os.path.isdir(FIXTURES_DIR):
        print(f"Dossier fixtures introuvable : {FIXTURES_DIR}")
        return

    pdfs = [f for f in os.listdir(FIXTURES_DIR) if f.endswith(".pdf")]
    if not pdfs:
        print("Aucun PDF trouvé dans tests/fixtures/")
        return

    for filename in pdfs:
        path = os.path.join(FIXTURES_DIR, filename)
        print(f"\n{'='*50}\n📄 {filename}\n{'='*50}")
        order = extract_order_from_pdf_file(path)
        print(order.to_summary())
        send_order_to_odoo(order)

# ── Point d'entrée ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Traite d'abord les PDFs locaux
    traiter_pdfs_locaux()

    # Puis boucle sur les mails entrants
    while True:
        lire_mails()
        print("\n⏳ Vérification dans 30 secondes...\n")
        time.sleep(30)