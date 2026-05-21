from fastapi import APIRouter, Request, HTTPException
from pathlib import Path
import tempfile
import shutil

from backend.services.audio.processor import AudioProcessor

router = APIRouter(prefix="/webhook", tags=["voicemail"])

processor = AudioProcessor()

@router.post("/voicemail")
async def handle_voicemail(request: Request):
    """Endpoint appelé par Twilio quand un message vocal est laissé"""
    try:
        form = await request.form()
        
        # Récupération des infos Twilio
        from_number = form.get("From")
        recording_url = form.get("RecordingUrl")
        transcription_text = form.get("TranscriptionText", "")  # si Twilio fait la transcription

        print(f"📞 Nouveau message vocal de : {from_number}")

        # Téléchargement de l'audio
        if recording_url:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(recording_url)
                response.raise_for_status()
                
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tmp.write(response.content)
                    tmp_path = Path(tmp.name)

            print(f"✅ Audio téléchargé : {tmp_path}")

            # 1. Transcription + Extraction
            texte = processor.transcribe_audio(tmp_path)
            commande = processor.extract_commande(texte)

            # 2. Affichage des résultats
            print("\n" + "="*60)
            print("🎯 COMMANDE EXTRAITE")
            print("="*60)
            print(f"Client      : {commande.nom_client}")
            print(f"Entreprise  : {commande.entreprise}")
            print(f"Score       : {commande.score_confiance:.2f}")
            for ligne in commande.lignes_commande:
                print(f"   • {ligne.quantite} {ligne.unite} {ligne.produit}")
            print("="*60)

            # TODO : plus tard on pushera dans Odoo ici

            # Nettoyage
            tmp_path.unlink(missing_ok=True)

            return {"status": "success", "commande": commande.model_dump()}

        return {"status": "no_recording"}

    except Exception as e:
        print(f"❌ Erreur webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))