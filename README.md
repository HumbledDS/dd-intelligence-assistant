# DD Intelligence Assistant

> Plateforme de due diligence automatisée pour cabinets de conseil — GCP Lean (~€15-20/mois)

---

## Vue d'ensemble

Automatise la collecte, l'analyse et la synthèse de données sur des **entreprises françaises** pour produire des rapports de due diligence professionnels.

- **Cache miss (1ère analyse)** : < 30 minutes
- **Cache hit** : < 3 minutes
- **Infra** : ~€15-20/mois

---

## Stack GCP Lean

```
Cloud Run (Next.js)  →  Cloud Run (FastAPI)
                              │
         ┌────────────────────┼──────────────────┐
         ▼                    ▼                  ▼
  Cloud SQL            Cloud Storage       Gemini API
  PostgreSQL 15        dd-raw-data/        Flash (rapports)
  ├── pgvector         dd-processed/       text-embedding-004
  ├── cache_entries
  └── métier
```

| Service | Rôle | Coût |
|---|---|---|
| Cloud Run (x2) | Backend FastAPI + Frontend Next.js | €0 |
| Cloud SQL `db-f1-micro` | PostgreSQL 15 + pgvector + cache table | ~€9/mois |
| Cloud Storage | Fichiers bruts + rapports PDF | ~€0.5/mois |
| Gemini API | Flash (rapports) + text-embedding-004 | ~€5-10/100 rapports |
| Secret Manager + Cloud Build | Secrets + CI/CD | €0 |

**Pas de Memorystore** (€40 économisés) : cache géré par `cachetools` (RAM) + table PostgreSQL.
**Pas de Pub/Sub** : `FastAPI BackgroundTasks` pour les jobs de collecte longue.

---

## Flux d'utilisation

### 1 — Quick Scan (screening)
```
Recherche par nom ou SIREN
    └── Fiche identité < 5s  (DINUM API, gratuite, 400 req/min)

Vue préliminaire (gratuite)
    └── Données légales, dirigeants, secteur, alertes BODACC

Rapport standard
    └── Sections livrées progressivement via SSE (streaming)
    └── Red Flags automatiques générés par Gemini Flash
    └── 1ère analyse : 5-30 min │ Cache disponible : < 3 min

Chat IA post-rapport
    └── Questions sur les données sourcées (RAG + pgvector)

Export PDF
```

### 2 — Analyse récurrente (cache)
```
Entreprise déjà vue → cache vérifié (L1 RAM + L2 PostgreSQL)
    └── Fraîcheur OK  → rapport complet < 3 min
    └── Données stale → delta uniquement (news + BODACC récents)
    └── Indicateur de fraîcheur affiché par section
```

### 3 — Due Diligence complète (M&A)
```
Quick Scan   < 15 min  (identification + alertes)
Standard DD  < 30 min  (financier + légal + réputation)
Full DD      1-2h       (exhaustif + validation humaine obligatoire)
```

---

## Architecture technique

### Pipeline de rapport (Cache Miss)

```
POST /report/generate
    ├── L1 cachetools (RAM) HIT → < 10ms
    ├── L2 PostgreSQL cache HIT → < 200ms
    └── MISS → BackgroundTask
               ├─ Phase 1 : DINUM API          → SSE section Identité
               ├─ Phase 2 : Infogreffe + BODACC → SSE section Légal
               ├─ Phase 3 : NewsAPI             → SSE section Réputation
               └─ Phase 4 : Gemini Flash        → SSE Synthèse + Red Flags
                            └── Stocker GCS + Cloud SQL + cache L2
```

### Sources de données françaises

| Source | Données | Coût | TTL cache |
|---|---|---|---|
| **DINUM API** (primaire) | SIREN + RNE + Ratios | Gratuit | 30 jours |
| INSEE SIRENE | Identification (fallback) | Gratuit | 30 jours |
| Infogreffe | Bilans, actes légaux | Payant | 7 jours |
| BODACC | Annonces légales | Gratuit | 1 heure |
| NewsAPI | Actualités | Payant | 30 min |

### Schéma base de données (Cloud SQL)

```sql
-- Entreprises
CREATE TABLE companies (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    siren      VARCHAR(9) UNIQUE NOT NULL,
    name       TEXT,
    metadata   JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cache PostgreSQL (remplace Redis)
CREATE TABLE cache_entries (
    cache_key   TEXT PRIMARY KEY,
    value       JSONB NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    source_type VARCHAR(30),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_cache_expires ON cache_entries(expires_at);

-- Embeddings (pgvector — remplace Pinecone)
CREATE TABLE document_embeddings (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    chunk_text TEXT,
    embedding  VECTOR(768),   -- text-embedding-004
    source     VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON document_embeddings
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## Plan d'implémentation (4 phases, ~4 semaines)

### Phase 0 — Infrastructure GCP *(2-3 jours)*
- [ ] Activer APIs : Cloud Run, Cloud SQL, GCS, Secret Manager, Artifact Registry, Cloud Build
- [ ] Cloud SQL : `db-f1-micro`, PostgreSQL 15, extension `pgvector`
- [ ] GCS : buckets `dd-raw-data` + `dd-processed`
- [ ] Secret Manager + `cloudbuild.yaml`

### Phase 1 — Backend MVP *(1 semaine)*
Endpoints : `/search`, `/company/{siren}`, `/report/generate`, `/report/{id}`, `/report/{id}/stream`, `/chat/{report_id}`
- [ ] FastAPI + SQLAlchemy async + Alembic
- [ ] Cache L1 (`cachetools`) + L2 (table `cache_entries`)
- [ ] Collecteurs : DINUM, INSEE, Infogreffe, BODACC
- [ ] Circuit breakers + rate limiting + BackgroundTasks
- [ ] Docker + Cloud Run

### Phase 2 — IA & RAG *(3-4 jours)*
- [ ] Gemini 1.5 Flash (rapports) + `text-embedding-004` (pgvector)
- [ ] Pipeline RAG : chunk → embed → pgvector → retrieve → generate
- [ ] Chat post-rapport avec citations + **Red Flags** automatiques

### Phase 3 — Frontend *(1 semaine)*
- [ ] Next.js : recherche, fiche, rapport progressif, chat, export PDF
- [ ] Cloud Run (Next.js containerisé)

### Phase 4 — Finalisation *(2-3 jours)*
- [ ] Alerte budget Gemini (Cloud Billing)
- [ ] Étape de validation humaine avant finalisation rapport
- [ ] Tests (> 70% couverture)

---

## Setup local

### Prérequis
Google Cloud SDK, Python 3.11+, Node.js 18+, Docker

```bash
# Authentification GCP
gcloud auth login && gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# Activer les APIs
gcloud services enable run.googleapis.com sqladmin.googleapis.com \
  storage.googleapis.com secretmanager.googleapis.com \
  artifactregistry.googleapis.com cloudbuild.googleapis.com

# Cloud SQL (db-f1-micro)
gcloud sql instances create dd-postgres \
  --database-version=POSTGRES_15 --tier=db-f1-micro --region=europe-west1
gcloud sql databases create dd_intelligence --instance=dd-postgres

# GCS
gsutil mb -l europe-west1 gs://dd-raw-data-YOUR_PROJECT
gsutil mb -l europe-west1 gs://dd-processed-YOUR_PROJECT
```

### Variables d'environnement (`.env`)

```bash
# GCP
GCP_PROJECT_ID=your-project-id
GCP_REGION=europe-west1

# Cloud SQL (via Cloud SQL Auth Proxy en local)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/dd_intelligence
# En production (Cloud Run) :
# DATABASE_URL=postgresql+asyncpg://postgres:password@/dd_intelligence?host=/cloudsql/PROJECT:europe-west1:dd-postgres

# Pas de REDIS_URL — cache géré par cachetools + PostgreSQL

# Cloud Storage
GCS_RAW_BUCKET=dd-raw-data-your-project
GCS_PROCESSED_BUCKET=dd-processed-your-project

# Gemini API (AI Studio — pay-per-use)
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL_CHAT=gemini-1.5-flash
GEMINI_MODEL_EMBED=text-embedding-004

# APIs French Data
DINUM_API_URL=https://recherche-entreprises.api.gouv.fr
INSEE_API_KEY=your-insee-api-key
INFOGREFFE_API_KEY=your-infogreffe-api-key
BODACC_API_URL=https://bodacc-datadila.opendatasoft.com/api/explore/v2.1
NEWS_API_KEY=your-newsapi-key

# App
ENVIRONMENT=development
SECRET_KEY=your-secret-key
DEBUG=true
```

### Frontend (`frontend/.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_CHAT=true
NEXT_PUBLIC_ENABLE_EXPORT_PDF=true
```

### Démarrage local

```bash
# Cloud SQL Auth Proxy (Windows)
Start-Process .\cloud-sql-proxy.exe -ArgumentList "PROJECT:europe-west1:dd-postgres --port=5432"

# Backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn api_services.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev

# Tests
pytest tests/ -v
```

### Déploiement GCP

```bash
gcloud builds submit --config=cloudbuild.yaml .
```

### Secrets en production

```bash
echo -n "your-key" | gcloud secrets create GEMINI_API_KEY --data-file=-
gcloud run services update dd-api \
  --update-secrets=GEMINI_API_KEY=GEMINI_API_KEY:latest
```

---

## Structure du projet

```
dd-intelligence-assistant/
├── api_services/              # FastAPI backend (Cloud Run)
│   ├── main.py
│   ├── routers/               # search, report, chat
│   └── core/                  # config, auth, cache
├── data_acquisition_engine/   # Collecteurs données françaises
│   └── collectors/
│       ├── official/          # DINUM, INSEE, Infogreffe
│       ├── financial/         # BODACC
│       └── news/              # NewsAPI, RSS
├── rag_pipeline/              # Embeddings + retrieval (pgvector)
├── llm_orchestration/         # Gemini Flash (rapports + chat)
├── report_generation/         # Export PDF
├── frontend/                  # Next.js (Cloud Run)
├── shared/                    # Utilitaires communs
├── terraform/                 # IaC (optionnel)
└── tests/
```

---

## Contribuer

```bash
git checkout develop && git pull
git checkout -b feature/ma-feature
# ... développement ...
git push origin feature/ma-feature
# Ouvrir une PR vers develop
```

**Conventions** : commits conventionnels (`feat:`, `fix:`, `docs:`), ruff + black, type hints obligatoires, pas de secrets en clair.

**Ajouter un collecteur** : hériter de `BaseCollector`, implémenter `collect(siren: str) -> Dict`, ajouter circuit breaker + rate limit, écrire tests.

---

## Évolutions futures

| Volume | Ajout | Coût additionnel |
|---|---|---|
| > 1000 req/jour (multi-instances) | Memorystore Redis | +€40/mois |
| > 5000 rapports/mois | Cloud SQL → `db-g1-small` | +€16/mois |
| > 10000 req/jour | Pub/Sub + Cloud Tasks | ~+€5/mois |

---

## Troubleshooting

| Problème | Solution |
|---|---|
| `database does not exist` | Cloud SQL Auth Proxy actif + database créée |
| `google.auth.DefaultCredentialsError` | `gcloud auth application-default login` |
| `pgvector not found` | Lancer `CREATE EXTENSION vector;` sur l'instance |
| Import error collecteurs | Activer venv : `venv\Scripts\activate` |

---

**Babacar GUEYE** — v2.1 (GCP Lean) — Février 2026
