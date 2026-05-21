import sys
from pathlib import Path

# Ajoute le dossier racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.audio.processor import AudioProcessor

def main():
    processor = AudioProcessor()
    
    audio_dir = Path("tests/test_data/audios")
    
    if not audio_dir.exists():
        print(f"❌ Dossier non trouvé : {audio_dir}")
        return
    
    for audio_file in sorted(audio_dir.glob("*.m4a")):
        print("\n" + "="*80)
        print(f"TEST FICHIER : {audio_file.name}")
        print("="*80)
        
        try:
            # 1. Transcription
            texte = processor.transcribe_audio(audio_file)
            
            # 2. Extraction avec LLM
            commande = processor.extract_commande(texte)
            
            # 3. Affichage
            print("\n📋 RÉSULTAT EXTRAIT :")
            print(f"Client          : {commande.nom_client}")
            print(f"Entreprise      : {commande.entreprise or 'Non mentionné'}")
            print(f"Date livraison  : {commande.date_livraison or 'Non mentionné'}")
            print(f"Score confiance : {commande.score_confiance:.2f}")
            
            print("\n🛒 Commande :")
            for ligne in commande.lignes_commande:
                print(f"   • {ligne.quantite} {ligne.unite} de {ligne.produit} ({ligne.code_article})")
                
            if commande.remarques:
                print(f"\n💬 Remarques : {commande.remarques}")
                
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {audio_file.name} : {e}")

if __name__ == "__main__":
    main()