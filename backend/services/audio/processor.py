from pathlib import Path
from groq import Groq
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import json

class LigneCommande(BaseModel):
    code_article: str
    produit: str
    quantite: float
    unite: str

class CommandeExtraite(BaseModel):
    nom_client: str
    entreprise: Optional[str] = None
    telephone: Optional[str] = None
    code_client: Optional[str] = None
    date_livraison: Optional[str] = None
    adresse_livraison: Optional[str] = None
    lignes_commande: List[LigneCommande]
    remarques: Optional[str] = None
    score_confiance: float = 0.0

class AudioProcessor:
    def __init__(self):
        load_dotenv()                    # Charge le .env
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            raise ValueError("❌ GROQ_API_KEY non trouvée dans le fichier .env")
            
        self.groq = Groq(api_key=api_key)   # Plus explicite et plus sûr

    def transcribe_audio(self, audio_path: Path) -> str:
        """Transcription avec Whisper via Groq"""
        print(f"🎙️ Transcription de : {audio_path.name}")
        with open(audio_path, "rb") as file:
            transcription = self.groq.audio.transcriptions.create(
                file=file,
                model="whisper-large-v3-turbo",
                language="fr",
                response_format="verbose_json"
            )
        print(f"✅ Transcription terminée ({len(transcription.text)} caractères)")
        return transcription.text

    def extract_commande(self, transcription: str) -> CommandeExtraite:
        """Extraction structurée avec LLM (Llama-3.3)"""
        print("🤖 Extraction des informations avec LLM...")

        prompt = f"""
Tu es un expert en prise de commande chez GUSTOMIO.

Transcription du message vocal :
\"\"\"
{transcription}
\"\"\"

Extraire les informations **de manière précise** et répondre **uniquement** avec du JSON valide :

{{
  "nom_client": "Nom de la personne qui appelle (obligatoire)",
  "entreprise": "Nom du restaurant ou entreprise",
  "telephone": null,
  "code_client": null,
  "date_livraison": null,
  "adresse_livraison": null,
  "lignes_commande": [
    {{"code_article": "INCONNU ou code si mentionné", "produit": "nom exact du produit", "quantite": nombre, "unite": "kg|boîte|paquet|pièce|..."}}
  ],
  "remarques": "Informations supplémentaires",
  "score_confiance": 0.85
}}

Règles importantes :
- Toujours mettre un "nom_client" même si c'est approximatif.
- Pour code_article : mettre "INCONNU" si pas de code.
- Quantité doit être un nombre (ex: 5.0, 400.0).
- Ne jamais laisser de champ vide dans "lignes_commande".
- Réponds UNIQUEMENT avec le JSON, rien d'autre.
"""

        completion = self.groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=800
        )

        response_text = completion.choices[0].message.content.strip()

        # Nettoyage JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1]

        try:
            data = json.loads(response_text)
            commande = CommandeExtraite(**data)
            print(f"✅ Extraction réussie (confiance: {commande.score_confiance:.2f})")
            return commande
        except Exception as e:
            print(f"❌ Erreur de parsing JSON: {e}")
            return CommandeExtraite(
                nom_client="ERREUR_EXTRACTION",
                lignes_commande=[],
                score_confiance=0.0,
                remarques=response_text[:200]
            )