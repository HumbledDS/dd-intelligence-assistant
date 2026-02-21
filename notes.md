1 — Un utilisateur fait une recherche
Frontend → GET /api/v1/search?q=carrefour

Dans 
api_services/routers/search.py
 :

Le router vérifie le cache L1 en RAM (cachetools.TTLCache) → si trouvé, réponse en < 10ms
Sinon, il vérifie le cache L2 dans PostgreSQL (table cache_entries) → si trouvé, < 200ms
Sinon, appelle le collecteur DINUM (
dinum_collector.py
) → API gratuite de l'État, 400 req/min, renvoie SIREN + nom + secteur + dirigeants
Si DINUM échoue → fallback INSEE SIRENE (
insee_collector.py
)
Le résultat est stocké dans L1 + L2 (TTL 30 jours pour données légales stables)
Réponse renvoyée au frontend
2 — L'analyste demande un rapport
Frontend → POST /api/v1/report/generate avec { siren: "552032534", report_type: "standard" }

Dans 
api_services/routers/reports.py
 :

Vérifie si un rapport pour ce SIREN est en cache → si oui, le retourne directement
Si non : crée un job en mémoire { job_id: "uuid", status: "queued" }
Lance background_tasks.add_task(...) → FastAPI démarre le pipeline sans bloquer la réponse
Retourne immédiatement { job_id: "xxxx", status: "queued" } au frontend
Le frontend reçoit le job_id en < 100ms. L'analyste peut déjà lire pendant que le backend collecte.

3 — Le pipeline de collecte tourne en arrière-plan
_run_report_pipeline()
 dans 
reports.py
 — 4 phases séquentielles :

python
# Phase 1 — Identité (dure 1-3s)
identity = await _dinum.get_company(siren)
job["sections"].append({"type": "identity", "data": identity})
# → ici le frontend peut déjà afficher la fiche d'identité
# Phase 2 — Légal & Financier (dure 5-30s selon réseau)
legal = await _infogreffe.get_company_data(siren)   # bilans, actes
bodacc = await _bodacc.get_announcements(siren)      # annonces légales
job["sections"].append({"type": "legal", ...})
job["sections"].append({"type": "bodacc", ...})
# Phase 3 — Réputation (skip si report_type == "quick")
news = await _news.get_news(company_name)            # NewsAPI
job["sections"].append({"type": "news", ...})
# Phase 4 — Gemini génère la synthèse
synthesis = await _llm.generate(siren, sections, report_type)
job["sections"].append({"type": "synthesis", ...})
# Post-rapport : embed tout pour le chat RAG
await _embedder.embed_report(siren, sections)
job["status"] = "completed"
Chaque phase ajoute à job["sections"] dès qu'elle est prête.

4 — Le frontend reçoit les sections au fur et à mesure (SSE)
En parallèle de l'étape 3, le frontend ouvre un flux SSE :

Frontend → GET /api/v1/report/{job_id}/stream

Dans 
reports.py
 — 
event_generator()
 :

python
while True:
    # Envoie les nouvelles sections disponibles
    while sent < len(job["sections"]):
        yield f"data: {json.dumps(sections[sent])}\n\n"
        sent += 1
    
    # Vérifie si terminé
    if job["status"] in ("completed", "failed"):
        break
    
    await asyncio.sleep(1)  # polling toutes les secondes
Résultat : l'analyste voit la section Identité apparaître en premier (en quelques secondes), puis Légal, puis Réputation, puis la Synthèse IA. Il lit pendant que le système collecte.

5 — Gemini génère la synthèse
Dans 
llm_orchestration/report_generator.py
 :

python
# Toutes les données collectées → assemblées en texte
sections_text = "
[IDENTITY]
{ nom: Carrefour, siren: ..., dirigeants: ... }
[LEGAL]
{ bilans: ..., actes: ... }
[NEWS]
{ articles: [...] }
"
# Prompt Gemini 1.5 Flash
"Tu es un expert DD. À partir de ces données, rédige un rapport structuré...
 Identifie les Red Flags. Cite tes sources."
response = await gemini_model.generate_content_async(prompt)
Gemini renvoie un rapport narratif + les Red Flags extraits automatiquement (lignes contenant ⚠️ ou red flag).

6 — Le Chat IA (RAG)
Une fois le rapport généré, l'analyste peut poser des questions : "Quels sont les risques liés aux dirigeants ?"

Frontend → POST /api/v1/chat/552032534 + { question: "..." }

Dans 
api_services/routers/chat.py
 :

Appelle Retriever.retrieve(query, siren, db)
Dans 
rag_pipeline/retriever.py
 : 2. Embed la question avec Gemini text-embedding-004 → vecteur de 768 dimensions 3. Cherche dans PostgreSQL (pgvector) les 5 chunks les plus proches en similarité cosinus :

sql
ORDER BY embedding <=> :query_vector
LIMIT 5
Retourne les chunks au router
De retour dans 
chat.py
 : 5. Passe les chunks + la question à ReportGenerator.answer_question() 6. Gemini répond en se basant uniquement sur les extraits sourcés → pas d'hallucination, les sources sont citées

7 — Où va tout ça dans PostgreSQL
companies          ← fiche entreprise (SIREN, nom, metadata)
requests           ← chaque demande de rapport (status, cache_hit, coût)
analysis_versions  ← versions des analyses (hash, chemin GCS)
cache_entries      ← cache L2 (remplace Redis, clé/valeur/expiration)
document_embeddings← vectors 768D de chaque chunk (pgvector, pour le RAG)
Le cache L2 fonctionne comme Redis mais dans PostgreSQL :

L1 (cachetools) : RAM, par instance Cloud Run, TTL court (5 min)
L2 (PostgreSQL) : persistant, partagé si plusieurs instances, TTL long (30j pour données légales)
8 — Déploiement (Cloud Build)
git push → Cloud Build déclenché automatiquement
  1. pytest tests/
  2. docker build → image poussée dans Artifact Registry
  3. gcloud run deploy dd-api
       → Cloud SQL Auth Proxy (connexion sécurisée sans IP publique)
       → Secret Manager (clés API injectées au runtime)
       → auto-scaling 0→N instances selon la charge
Le frontend Next.js est containerisé séparément et déployé sur son propre service Cloud Run.

Résumé du flux complet
1. Recherche (< 1s cache / 3s live)
2. Rapport demandé → job créé, fond de tâche lancé
3. Collecte par phases (DINUM → Infogreffe → BODACC → News)
4. Sections streamées via SSE au fur et à mesure
5. Gemini Flash synthétise + génère Red Flags
6. Embeddings stockés dans pgvector pour le chat
7. Chat IA : question → embed → pgvector → Gemini → réponse sourcée