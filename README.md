# 🧠 Gustomio — Traitement Automatisé des Commandes par IA

> Plateforme intelligente de traitement des commandes multi-canal (voix, e-mail, PDF) avec extraction LLM, validation humaine et intégration Odoo.

---

## 📋 Vue d'ensemble

**Gustomio** automatise la réception et le traitement des commandes clients quel que soit le canal d'entrée. L'IA extrait, structure et propose chaque commande à la validation humaine avant de la pousser dans Odoo.

```
Canal entrant (Voix / Email / PDF)
        │
        ▼
┌───────────────────┐
│  Ingestion Layer  │  ← FastAPI workers + Celery
│  Whisper / OCR    │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│   LLM Extraction  │  ← Groq (Llama-3.1 70B) / GPT-4o
│   (JSON structuré)│  ← client, articles, quantités, date
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Interface Review │  ← Streamlit Dashboard
│  Score confiance  │  ← 🟢 ≥90% / 🟠 75-90% / 🔴 <75%
│  Actions rapides  │  ← Valider / Modifier / Rejeter
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│   Odoo XML-RPC    │  ← Push commande validée
└───────────────────┘
```

---

## 🗂️ Structure du projet (actuelle)

```bash
gustomio_g12/
├── backend/
│   ├── api/
│   │   └── routes/               # Endpoints FastAPI
│   ├── core/                     # Configuration, settings
│   ├── integrations/             # Clients externes (Groq, Odoo, etc.)
│   ├── models/                   # Pydantic schemas
│   ├── services/
│   │   ├── audio/                # Transcription + extraction voix (ta partie)
│   │   ├── email/
│   │   ├── pdf/
│   │   └── common/               # Utils partagés (LLM, Odoo, etc.)
│   ├── utils/
│   └── workers/                  # Tâches asynchrones
├── tests/
│   └── test_data/
│       ├── audios/               # Tes enregistrements vocaux
│       ├── email/
│       └── pdf/
├── frontend/                     # Streamlit (à venir)
├── docs/
├── scripts/
├── requirements.txt
├── .env.example
└── README.md

---

## ⚙️ Stack Technique

| Couche | Technologie | Pourquoi |
|--------|-------------|----------|
| **Langage** | Python 3.11+ | Unique langage → productivité maximale |
| **Backend / API** | FastAPI + Pydantic v2 | Async, validation auto, OpenAPI intégré |
| **Interface** | Streamlit | Ultra-rapide à prototyper, dashboard interne |
| **Transcription voix** | Whisper large-v3 (via Groq) | Meilleur en français, rapide et précis |
| **Extraction PDF / OCR** | LlamaParse + PyMuPDF | Très bons sur tableaux variables |
| **LLM / NLP** | Groq (Llama-3.1 70B) / GPT-4o | Vitesse + coût + qualité d'extraction |
| **Intégration Odoo** | XML-RPC (`odoo-xmlrpc`) | Fiable et bien documenté |
| **Base de données** | PostgreSQL | Compatible Odoo |
| **File / Queue** | Redis + Celery | Tâches asynchrones (ingestion, notifs) |
| **Auth & Sécurité** | API Keys + OAuth2 | Confidentialité clients |
| **Hébergement** | Railway / Render / Fly.io | Déploiement en 5 min |

---

## 🚀 Démarrage rapide

### Prérequis

- Python 3.11+
- Docker & Docker Compose
- Compte Groq API (ou OpenAI)
- Instance Odoo accessible

### Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/Tarikokc/gustomio_g12.git
cd gustomio_g12

# 2. Copier et remplir les variables d'environnement
cp .env.example .env

# 3. Démarrer les services (PostgreSQL + Redis + API + Worker)
docker-compose up -d

# 4. Lancer l'interface Streamlit
streamlit run frontend/app.py
```

### Mode développement (sans Docker)

```bash
pip install -e ".[dev]"
uvicorn backend.api.main:app --reload --port 8000
celery -A backend.workers.celery_app worker --loglevel=info
streamlit run frontend/app.py
```

---

## 🎯 Fonctionnalités principales

### Tableau de bord
- Vue d'ensemble : commandes du jour / en attente / validées / rejetées
- Gains de temps estimés (KPI automatisation)

### Flux des commandes
- Liste chronologique filtrée par canal (voix, email, PDF), statut, client

### Détail commande
- Transcription ou texte original
- Extraction structurée : client, date, articles, quantités
- **Score de confiance par champ** (🟢 vert ≥90% / 🟠 orange 75-90% / 🔴 rouge <75%)
- Aperçu PDF ou lecteur audio intégré

### Actions rapides
- ✅ **Valider** → push direct dans Odoo
- ✏️ **Modifier** → édition inline des champs
- ❌ **Rejeter** → notification client automatique
- 📩 **Demander compléments** → SMS/e-mail auto

### Supervision
- Filtre "à risque" (score global <75%) + alertes temps réel

### Historique & Stats
- Recherche, export CSV/Excel
- KPIs : taux d'automatisation, temps gagné, erreurs évitées

### Administration
- Gestion des modèles LLM (prompt, température, modèle)
- Référentiel produits (correspondance nom → SKU Odoo)
- Règles métier (seuils de confiance, canaux actifs)

---

## 🔌 API Endpoints (FastAPI)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/v1/orders/ingest` | Soumettre une commande (audio/PDF/texte) |
| `GET` | `/api/v1/orders/` | Lister les commandes (filtrages) |
| `GET` | `/api/v1/orders/{id}` | Détail d'une commande |
| `PATCH` | `/api/v1/orders/{id}` | Modifier les champs extraits |
| `POST` | `/api/v1/orders/{id}/validate` | Valider → push Odoo |
| `POST` | `/api/v1/orders/{id}/reject` | Rejeter + notifier |
| `POST` | `/api/v1/orders/{id}/request-info` | Demander compléments |
| `GET` | `/api/v1/stats/` | KPIs globaux |

Documentation interactive : `http://localhost:8000/docs`

---

## 🤝 Contribution (équipe G12)

1. `git checkout -b feature/ma-fonctionnalite`
2. Commiter vos changements
3. Ouvrir une Pull Request vers `main`

---

## 📄 Licence

MIT
