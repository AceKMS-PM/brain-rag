# Brain AI - Votre Second Brain Local

Système RAG (Retrieval-Augmented Generation) fonctionnant entièrement en local, sans dépendance cloud externe.

## 1. Présentation

Brain AI vous permet de:
- Stocker vos documents (markdown) localement
- Rechercher semantiquement (comprend le sens) + par mots-clés
- Poser des questions et obtenir des réponses générées par une IA locale
- Tout ça sans envoyer vos données à l'extérieur

**Cas d'usage**: Notes personnelles, documentation technique, Base de connaissances.

## 2. Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Documents     │────▶│   Ingestion  │────▶│    LanceDB      │
│   (~/memory/)   │     │  (chunking) │     │   (vecteurs)    │
└─────────────────┘     └──────────────┘     └─────────────────┘
                                                        │
                        ┌──────────────────────────────┘
                        ▼
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Question      │────▶│   Recherche │────▶│      LLM        │
│   utilisateur   │     │   (hybride)  │     │   (Qwen 1.5B)   │
└─────────────────┘     └──────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │    Réponse      │
                                               │   + Sources     │
                                               └─────────────────┘
```

## 3. Composants Détaillés

### 3.1 config.py - Configuration

Contient tous les paramètres du système:

| Paramètre | Description | Valeur par défaut |
|-----------|-------------|------------------|
| `MEMORY_PATH` | Dossier racine des documents | `~/memory` |
| `DOCUMENTS_PATH` | Sous-dossier avec les .md | `~/memory/documents` |
| `INDEX_PATH` | Stockage de l'index | `~/memory/_index` |
| `MODELS_PATH` | Dossier des modèles GGUF | `~/models` |
| `EMBEDDING_MODEL_PATH` | Modèle d'embedding | Qwen3-Embedding-0.6B |
| `LLM_MODEL_PATH` | Modèle de génération | Qwen2.5-1.5B |
| `CHUNK_SIZE` | Taille des segments | 512 tokens |
| `TOP_K` | Nombre de résultats | 5 |
| `LLM_N_CTX` | Contexte max LLM | 1024 tokens |

**Note**: Tous les chemins sont absolus, calculés depuis `MODELS_PATH`.

---

### 3.2 ingest.py - Ingestion des documents

**Rôle**: Transformer vos fichiers markdown en vecteurs searchable.

**Processus**:
```
1. Parcourir ~/memory/documents/*.md
2. Pour chaque fichier:
   a. Lire le contenu
   b. Parser le markdown
   c. Découper en chunks (par headers: ##, ###)
   d. Générer un vecteur d'embedding pour chaque chunk
   e. Stocker dans LanceDB (texte + vecteur + filename)
```

**Fonctions principales**:
- `ingest_documents()` - Lance l'ingestion complète
- `get_embedding_model()` - Charge le modèle d'embedding (paresseux)
- `get_db()` - Ouvre la base LanceDB

**Chunking sémantique**: Au lieu de couper par taille fixe, on coupe aux headers markdown (`##`, `###`). Cela préserve le contexte logique de chaque section.

**Stockage**: LanceDB (SQLite + vecteurs) dans `~/memory/_index/`

---

### 3.3 search.py - Recherche hybride

**Rôle**: Trouver les documents les plus pertinents pour une question.

**Stratégie**: Hybrid Search = Vector Search + BM25 + Reciprocal Rank Fusion

```
┌─────────────────────────────────────────────────────┐
│                   RECHERCHE HYBRIDE                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Question ─┬──▶ Vector Search ──▶ [score_vector]   │
│            │                                         │
│            └──▶ BM25 Search ──▶ [score_bm25]       │
│                        │                            │
│                        ▼                            │
│            Reciprocal Rank Fusion (RRF)            │
│            score = k/(rank_vector + k) + k/(rank_bm25 + k) │
│                        │                            │
│                        ▼                            │
│               Top-K résultats fusionnés            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Pourquoi deux méthodes?**
- **Vector Search** (semantique): Trouve des documents qui "signifient" la même chose, même sans mots identiques. Ex: "chat" → trouve "félin"
- **BM25** (keywords): Trouve les documents avec les mots exacts. Bon pour les termes techniques spécifiques.

**RRF (Reciprocal Rank Fusion)**: Combine les deux scores pour obtenir les meilleurs résultats des deux mondes.

---

### 3.4 llm.py - Génération de réponse

**Rôle**: Générer une réponse en langage naturel à partir du contexte trouvé.

**Processus**:
```
1. Récupérer les chunks pertinents (depuis search.py)
2. Nettoyer le texte (enlever les #, **, etc.)
3. Construire le prompt avec:
   - Instructions système
   - Contexte (chunks sélectionnés)
   - Question de l'utilisateur
4. Envoyer au modèle Qwen2.5-1.5B
5. Retourner la réponse générée
```

**Modèle utilisé**: Qwen2.5-1.5B-Instruct (GGUF Q4_K_M)
- ~1GB sur disque
- ~1.5GB RAM à l'exécution
- 1024 tokens de contexte

**Prompt utilisé**:
```
<|im_start|>system
Tu es un assistant utile. Réponds en français avec les infos du contexte.
Si pas assez d'info, dis "Je ne sais pas".
<|im_end|>
<|im_start|>user
Contexte: {context[:500]}

Question: {question}
<|im_end|>
<|im_start|>assistant
```

**Paramètres de génération**:
- `temperature`: 0.3 (peu créatif, factuel)
- `max_tokens`: 256 (réponses courtes)
- `stop`: `<|im_end|>`

---

### 3.5 webui.py + templates/index.html - Interface

**Rôle**: Interface utilisateur style OpenWebUI.

**Technologies**:
- FastAPI (backend Python)
- HTML/CSS/JS vanilla (frontend)
- localStorage (historique des chats)

**Fonctionnalités UI**:
- Zone de saisie de question
- Affichage des messages (user/assistant)
- Rendu markdown (titres, listes, code, gras)
- Bouton copier pour les blocs de code
- Historique des conversations (sidebar)
- Compteur de documents indexés
- Toggle "Web Search" (infrastructure prête)

**Couleurs**: Style OpenWebUI
- Fond: `#0b1326` (dark navy)
- Accent: `#d0bcff` (violet)

---

### 3.6 main.py - API REST

**Points d'entrée**:

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/` | Status du service |
| GET | `/health` | Health check |
| POST | `/ingest` | Lancer l'ingestion |
| POST | `/query` | Poser une question |
| GET | `/stats` | Nombre de chunks |

**Format `/query`**:
```json
{
  "question": "quelle est la commande git pour rebase?",
  "top_k": 5,
  "web_search": false
}
```

**Réponse**:
```json
{
  "question": "...",
  "answer": "La commande est git rebase ...",
  "sources": [
    {"filename": "git.md", "text": "..."}
  ]
}
```

---

### 3.7 websearch.py - Recherche web

**Rôle**: (Optionnel) Rechercher sur le web quand le toggle est activé.

**Statut**: Infrastructure prête, nécessite:
- Accès réseau externe (non bloqué)
- OU SearXNG auto-hébergé (Docker)

**Pour激活**: Voir section "Web Search" plus bas.

---

## 4. Modèles AI Utilisés

| Modèle | Taille | Usage | Location |
|--------|--------|-------|----------|
| Qwen3-Embedding-0.6B | ~1.1GB | Vecteurs (semantique) | `~/models/Qwen3-Embedding-0.6B-f16.gguf` |
| Qwen2.5-1.5B-Instruct | ~1GB | Génération texte | `~/models/qwen2.5-1.5b-instruct-q4_k_m.gguf` |

**Quantification**: Le LLM est en Q4_K_M (quantization 4-bit), ce qui réduit son poids de 3GB à ~1GB sans perte significative de qualité.

---

## 5. Commandes

### Démarrer le service

```bash
cd ~/brain/rag-service
source venv/bin/activate

# Méthode 1: Direct
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Méthode 2: Background (recommandé pour session persistante)
setsid python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Méthode 3: Script (si disponible)
./brain-ai start
```

### Arrêter le service

```bash
pkill -f "uvicorn app.main"
# ou
./brain-ai stop
```

### Vérifier le statut

```bash
curl http://localhost:8000/health
```

### Ré-ingérer les documents

```bash
curl -X POST http://localhost:8000/ingest
```

---

## 6. Utilisation

### Via l'interface web

1. Ouvrir: http://localhost:8000
2. Taper une question dans la zone de saisie
3. Appuyer sur "Envoyer" ou Entrée
4. Voir la réponse + sources en dessous

### Via l'API

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "comment utiliser git rebase?"}'
```

---

## 7. Ajouter des Documents

1. Créer/éditer des fichiers `.md` dans `~/memory/documents/`
2. Relancer l'ingestion:
   ```bash
   curl -X POST http://localhost:8000/ingest
   ```
3. Les nouveaux documents sont automatiquement indexés

**Format recommandé**:
```markdown
# Titre du document

## Section 1
Contenu de la section...

## Section 2
Contenu de la section...
```

---

## 8. Web Search (Optionnel)

Pour utiliser la recherche web:

### Option A: Accès direct (si réseau non bloqué)
- Installer les dépendances: `pip install googlesearch-python`
- Le toggle dans l'UI enverra les requêtes à Google

### Option B: SearXNG auto-hébergé
1. Ajouter SearXNG à docker-compose:
   ```yaml
   searxng:
     image: searxng/searxng
     ports:
       - "8080:8080"
   ```
2. Modifier `websearch.py` pour interroger `http://searxng:8080/search`

---

## 9. Dépannage

### Le service ne démarre pas
- Vérifier les logs: `cat /tmp/rag.log`
- Vérifier que les modèles existent: `ls ~/models/*.gguf`
- Vérifier le port: `lsof -i :8000`

### Pas de résultats de recherche
- Ré-ingérer: `curl -X POST http://localhost:8000/ingest`
- Vérifier les documents: `ls ~/memory/documents/`

### Le LLM répond mal
- Le modèle 1.5B est limité, les réponses peuvent être imprécises
- Vérifier que les chunks retournés sont pertinents

### Lenteur
- Réduire `TOP_K` dans config.py (défaut: 5)
- Réduire `LLM_N_CTX` (défaut: 1024)

---

## 10. Fichiers du Projet

```
~/brain/rag-service/
├── app/
│   ├── __init__.py      # Package initialization
│   ├── config.py       # Configuration centrale
│   ├── ingest.py       # Ingestion documents
│   ├── search.py       # Recherche hybride
│   ├── llm.py          # Génération réponses
│   ├── webui.py        # Setup UI FastAPI
│   ├── main.py         # Points d'entrée API
│   └── websearch.py    # Recherche web (optionnel)
├── templates/
│   └── index.html      # Interface utilisateur
├── venv/               # Environnement virtuel Python
├── brain-ai            # Script de commande
├── requirements.txt    # Dépendances Python
└── README.md          # Cette documentation
```

---

## 11. Caractéristiques Techniques

- **RAM utilisée**: ~3-4GB (embedding + LLM + système)
- **Stockage index**: ~10-50MB selon nombre de documents
- **Latence moyenne**: 2-5s par requête
- **CPU**: Intel i7-6600U (2 cœurs, 4 threads) sufficient

---

*Document généré pour Brain AI - Second Brain Local*