# Codebase Summary

## Project Structure

```
capstone-project/
├── client/                    # Frontend (Next.js 14, React 18, TypeScript)
├── node-server/              # Backend API (Express, TypeScript, Node 18+)
├── python-server/            # RAG Service (FastAPI, Python 3.11)
├── translator/               # EN→VI translation pipeline (Python)
├── llm/                       # LLM fine-tuning (Llama 3.2 3B)
├── docker-compose.yml        # Multi-service orchestration
├── README.md                 # Project overview
└── docs/                     # Documentation
    ├── project-overview-pdr.md
    ├── codebase-summary.md
    ├── code-standards.md
    ├── system-architecture.md
    ├── deployment-guide.md
    ├── project-roadmap.md
    └── design-guidelines.md
```

## Service Breakdown

### Frontend (`client/`)

**Tech Stack:**
- Next.js 14.2.5 (App Router)
- React 18.2.0
- TypeScript 4.9.5 (strict mode)
- Tailwind CSS 3.3.2 + tailwindcss-animate
- Radix UI (shadcn/ui components)
- TanStack React Query 5.52.1
- React Hook Form 7.52.2 + Zod 3.23.8
- Axios 1.7.4
- next-themes (dark/light mode)
- Lucide icons

**Directory Structure:**
```
client/
├── app/
│   ├── (auth)/                # Public auth routes
│   │   ├── login/
│   │   ├── register/
│   │   └── forgot-password/
│   ├── (root)/                # Protected app routes
│   │   ├── page.tsx           # Homepage
│   │   ├── create/            # Create workspace
│   │   ├── workspace/[slug]/  # Chat interface
│   │   └── layout.tsx
│   ├── components/
│   │   ├── ui/                # shadcn primitives
│   │   ├── layouts/           # Header, Sidebar
│   │   ├── shared/            # ChatBubble, PromptInput, SourceDocuments
│   │   ├── modals/            # UploadModal, ReEmbedDialog
│   │   └── workspaces/        # Workspace components
│   ├── hooks/
│   │   ├── useAuth.ts         # Auth context hook (duplicate: also in context)
│   │   └── use*.ts
│   ├── providers/
│   │   ├── AuthProvider.tsx
│   │   ├── ThemeProvider.tsx
│   │   ├── ProtectedProvider.tsx
│   │   └── index.tsx
│   ├── context/
│   │   ├── AuthContext.tsx    # Auth state + useAuth (duplicate of hooks/)
│   │   └── *.tsx
│   ├── types/
│   ├── utils/
│   │   ├── axios.ts
│   │   ├── api.ts
│   │   └── *.ts
│   └── styles/
│       ├── globals.css        # HSL tokens, dark mode via next-themes
│       └── *.css
├── public/
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.ts
└── .eslintrc.json
```

**Key Features:**
- Protected routes in `(root)` group; public in `(auth)` group
- Auth state via context + React Query (custom hooks in both `hooks/` and `context/`)
- Axios interceptor for JWT refresh-on-401 with queued pending requests
- Custom headers: `Authorization: Bearer {token}`, `refresh-token`, `client-id`
- Dark mode via next-themes (class-based)
- HSL CSS variables for theming
- Zod schemas for form validation
- UI strings in Vietnamese (noted as current state, not a blocker)

**Known Issues:**
- Duplicate `useAuth` hook (exists in both `hooks/` and `context/`)
- Two file upload code paths (`/api/files/embed` vs `/api/files/upload/{slug}`)

---

### Backend API (`node-server/`)

**Tech Stack:**
- Express 4.21.2
- TypeScript 5.7.3
- Node 18+ (LTS)
- Mongoose 8.10.1 (MongoDB ODM)
- JWT 9.0.2 (RS256 algorithm)
- AWS SDK v3 (S3)
- Bcrypt 5.1.1 (12 rounds)
- Multer-S3 3.0.1
- Winston 3.17.0 + daily-rotate-file
- Helmet 8.0.0, CORS, compression
- IORedis 5.5.0 (configured, unused)
- Firebase Admin 13.1.0 (parsed, unused)
- express-rate-limit 7.5.0 (installed, not applied)

**Directory Structure:**
```
node-server/
├── src/
│   ├── index.ts               # App entry, Express setup
│   ├── type.d.ts              # Global type definitions
│   ├── core/
│   │   ├── JWT.ts             # JWT config
│   │   ├── error.response.ts  # Error class hierarchy
│   │   └── success.response.ts # Success response wrapper
│   ├── controllers/
│   │   ├── auth.controller.ts
│   │   └── files.controller.ts
│   ├── routes/
│   │   ├── auth.route.ts
│   │   └── files.route.ts
│   ├── services/
│   │   ├── auth.service.ts
│   │   ├── files.service.ts
│   │   ├── encryption.service.ts
│   │   ├── key-store.service.ts
│   │   └── firebase.service.ts
│   ├── models/
│   │   ├── User.ts
│   │   ├── Workspace.ts
│   │   ├── Message.ts
│   │   ├── Keystore.ts
│   │   └── UserKeyPair.ts
│   ├── repositories/
│   │   ├── workspace.repo.ts
│   │   └── *.repo.ts
│   ├── middlewares/
│   │   ├── errorHandler.middleware.ts
│   │   ├── multer.middleware.ts
│   │   ├── authentication.ts
│   │   ├── cors.ts
│   │   └── logging.ts
│   ├── utils/
│   │   ├── jwt.ts
│   │   ├── auth.util.ts
│   │   ├── encryption.util.ts
│   │   ├── s3.ts
│   │   ├── bcrypt.ts
│   │   ├── communicationKey.ts
│   │   └── *.ts
│   ├── helpers/
│   │   └── cathAsync.ts       # Async error wrapper
│   └── config/
│       └── *.ts
├── uploads/                   # Temp upload dir
├── logs/                      # Winston logs (daily rotation)
├── Dockerfile
├── package.json
├── tsconfig.json
└── .eslintrc.json
```

**API Endpoints:**

| Route | Method | Auth | Purpose |
|-------|--------|------|---------|
| `/api/auth/register` | POST | ❌ | Register user |
| `/api/auth/login` | POST | ❌ | Authenticate (returns tokens) |
| `/api/auth/logout` | POST | ✅ | Invalidate tokens |
| `/api/auth/refresh-token` | POST | ✅ | Get new access token |
| `/api/auth/rotate-keys` | POST | ✅ | Rotate RSA keypair |
| `/api/auth/public-key/:userId` | GET | ✅ | Fetch user's public key |
| `/api/auth/encrypt` | POST | ✅ | Encrypt data with user's public key |
| `/api/auth/decrypt` | POST | ✅ | Decrypt data with user's private key |
| `/api/files/embed` | POST | ✅ | Upload files for embedding (multipart, max 10) |
| `/api/files/workspaces` | GET | ✅ | List user's workspaces |
| `/api/files/workspace/:slug` | GET | ✅ | Get workspace details + files |
| `/api/files/workspace/:slug/query` | POST | ✅ | Query workspace (calls RAG service) |
| `/api/files/workspace/:slug/messages` | GET | ✅ | Get message history |

**Models:**

| Model | Fields | Purpose |
|-------|--------|---------|
| **User** | `_id`, `email`, `password_hash`, `created_at` | Authentication |
| **Workspace** | `_id`, `slug`, `userId`, `name`, `isEmbedded`, `filePaths[]`, `fileKeys[]`, `created_at` | Multi-user isolation |
| **Message** | `_id`, `workspaceSlug`, `messages[]` | Chat history |
| **Keystore** | `userId`, `publicKey`, `refreshToken`, `signature`, `keyId` | JWT key rotation |
| **UserKeyPair** | `userId`, `encryptedPrivateKey`, `algorithm`, `status` | RSA keypairs |
| **ApiKey** | `userId`, `key`, `secret`, `scope[]` | Future API auth |

**Key Services:**
- **AuthService:** Register, login, logout, refresh, key rotation, encryption/decryption
- **FilesService:** Upload to S3, embed (call RAG), query (call RAG), workspace CRUD
- **EncryptionService:** RSA encrypt/decrypt per user
- **KeyStoreService:** Manage JWT keys, refresh tokens, key rotation (RS256 + passphrase)
- **FirebaseService:** Stub (not used)

**Error Hierarchy:**
- `BaseError` (base class)
  - `NotFoundError` (404)
  - `BadRequestError` (400)
  - `UnauthorizedError` (401)
  - `ConflictError` (409)
  - `ForbiddenError` (403)
  - `InternalServerError` (500)

**Middleware Stack:**
1. Helmet (security headers)
2. CORS (localhost:3000)
3. compression (gzip, 100KB threshold)
4. morgan (HTTP logging)
5. express-winston (structured logging)
6. multer-S3 (file upload)
7. errorHandler (catch-all)

**Auth Flow:**
- JWT RS256: public key per user (from Keystore)
- Refresh token stored in DB
- Custom middleware `authentication` verifies token signature
- Failed auth returns 401 + refresh hint
- Queued pending requests retry after token refresh

---

### RAG Service (`python-server/`)

**Tech Stack:**
- FastAPI 0.115.12
- Uvicorn 0.34.3
- Python 3.11
- FlagEmbedding 1.3.4 (BAAI/bge-m3)
- pymilvus 2.4.10
- sentence-transformers 4.1.0
- rank-bm25 0.2.2
- cross-encoder (ms-marco-MiniLM-L-6-v2)
- transformers 4.51.3, torch 2.7.0
- pypdf 5.5.0, python-docx 1.1.2
- python-dotenv

**Directory Structure:**
```
python-server/
├── app/
│   ├── main.py                # FastAPI entry point
│   ├── core/
│   │   ├── config.yaml        # Settings (models, vector store, search)
│   │   ├── file-loader.py     # PDF/DOCX/TXT loading
│   │   ├── text-splitter.py   # Sentence-level chunking
│   │   └── embedding.py       # BAAI/bge-m3 wrapper
│   ├── services/
│   │   ├── rag_service.py     # Main RAG pipeline
│   │   ├── milvus_store.py    # Vector DB wrapper
│   │   ├── bm25_index.py      # BM25 ranking
│   │   ├── reranker.py        # Cross-encoder re-ranking
│   │   └── llm_chain.py       # LLM inference
│   ├── evaluation/
│   │   ├── rag_evaluator.py   # Metrics (precision, recall, MRR, NDCG, MAP)
│   │   └── ground_truth/      # Test data
│   └── utils/
│       └── *.py
├── data/
│   ├── bm25_indices/          # Persisted BM25 indices per collection
│   │   └── {collection}.pkl
│   └── sample_docs/           # Sample PDFs for testing
├── volumes/
├── requirements.txt
├── Dockerfile
├── config.yaml
└── .env
```

**Endpoints:**

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Health check |
| `/query` | POST | Execute query with history |
| `/embed` | POST | Embed documents into collection |

**Request/Response Schemas:**

```python
# POST /query
{
  "query": "What is machine learning?",
  "collection_name": "workspace_abc123",
  "history": ["What is AI?", "Explain neurons"]
}
→ {
  "docs": [
    {
      "content": "...",
      "metadata": {"file": "paper.pdf", "page": 5},
      "score": 0.92
    }
  ],
  "response": "Machine learning is...",
  "search_stats": {"dense_k": 20, "sparse_k": 20, "reranked_k": 5}
}

# POST /embed
{
  "file_paths": ["/tmp/doc1.pdf", "/tmp/doc2.docx"],
  "collection_name": "workspace_abc123"
}
→ {
  "embedding_results": [
    {"file": "doc1.pdf", "chunks": 42, "status": "success"}
  ],
  "bm25_index": "built"
}
```

**RAG Pipeline:**

1. **File Loading:**
   - PDF: pypdf
   - DOCX: python-docx
   - TXT: plaintext
   - Extract metadata (filename, page, section)

2. **Text Splitting:**
   - Sentence-level (NLTK/spaCy)
   - Chunk: 512 tokens
   - Overlap: 128 tokens
   - Hierarchical: paragraph → sentence

3. **Embedding:**
   - Model: BAAI/bge-m3 (1024-dim)
   - Batch size: 32
   - Device: auto-detect (MPS/CUDA/CPU)
   - Normalized L2

4. **Vector Storage (Milvus):**
   - Collection per workspace
   - Metric: L2 or COSINE
   - Index: IVF_FLAT or HNSW
   - Persistence: etcd + MinIO

5. **Hybrid Retrieval:**
   - Dense: Milvus k=20
   - Sparse: BM25 k=20
   - Fusion: RRF (k=60) or linear (α=0.6 dense, 0.4 sparse)
   - Output: top-5 combined

6. **Re-ranking:**
   - Model: cross-encoder (ms-marco-MiniLM-L-6-v2)
   - Score: 0–1 (semantic relevance)
   - Select: top-5 candidates

7. **LLM Inference:**
   - Endpoint: http://35.221.160.224:8000/v1/chat/completions (HARDCODED)
   - Model: jCool10/jCool10-LLaMA3-VietQA-3B-merged
   - Params: max_tokens=1000, temperature=0.7, top_p=0.9
   - Fallback: static response if unreachable

**Config (config.yaml):**

```yaml
document_processing:
  chunk_size: 512
  overlap: 128
  split_method: sentence

models:
  embedding:
    name: BAAI/bge-m3
    dimension: 1024
    batch_size: 32
  llm:
    endpoint: http://35.221.160.224:8000/v1/chat/completions
    model: jCool10/jCool10-LLaMA3-VietQA-3B-merged
    max_tokens: 1000

vector_store:
  type: milvus
  uri: ${MILVUS_URI}
  metric: COSINE

hybrid_search:
  enabled: true
  dense_weight: 0.6
  sparse_weight: 0.4
  fusion: rrf

bm25_index_dir: ./data/bm25_indices

device: mps  # or cuda, cpu, auto
max_workers: 10
```

**Key Services:**
- **RAGService:** Orchestrates full pipeline
- **MilvusStore:** Vector DB interface
- **BM25Index:** Keyword search, persists to disk
- **Reranker:** Cross-encoder scoring
- **LLMChain:** Prompt construction, LLM call

---

### Translation Service (`translator/`)

**Purpose:** EN→VI translation for instruction dataset preparation (for fine-tuning).

**Tech Stack:**
- Python 3.11
- transformers, PyTorch
- bitsandbytes (4-bit quantization)
- VinAI `vinai/vinai-translate-en2vi` (primary)
- googletrans (fallback)
- datasets, LRU cache, exponential backoff

**Directory Structure:**
```
translator/
├── providers/
│   ├── vinai_provider.py       # VinAI seq2seq
│   └── fallback_provider.py    # googletrans fallback
├── configs/
│   └── translation_config.py
├── filters/
│   └── fail_translation_filter.py
├── datasets/
│   ├── alpaca_cleaned.py
│   ├── openorca.py
│   ├── webglm_qa.py
│   └── *.py
├── main.py
└── requirements.txt
```

**Supported Datasets:**
- YahmaAlpaca
- OpenOrca
- webglm-qa
- Databricks Dolly 15k
- MathInstruct
- MBZUAI-Bactrian-X
- grade-school-math

**Caching:** LRU 5000 entries, exponential backoff (max 20 list / 10 string).

---

### LLM Fine-tuning (`llm/`)

**Purpose:** Fine-tune Llama 3.2 3B on instruction-following tasks.

**Tech Stack:**
- unsloth (optimized LoRA)
- transformers, PEFT (LoRA rank 16, 4-bit)
- TRL trainer
- Weights & Biases (monitoring)
- PyTorch

**Directory Structure:**
```
llm/
├── train.py               # Fine-tuning script
├── eval.py                # Evaluation (ROUGE, BLEU)
├── configs/
│   └── training_config.yaml
└── requirements.txt
```

**Input:** JSON files in `/workspace/dataset/`
**Output:** HF Hub `jCool10/chat_anything-3B` (merged + unmerged)

---

## Infrastructure (`docker-compose.yml`)

**Services:**

| Service | Image | Port | Purpose | Health Check |
|---------|-------|------|---------|--------------|
| etcd | coreos/etcd:v3.5.5 | 2379 | Config for Milvus | etcdctl endpoint health |
| minio | minio/minio:RELEASE.2023-03-20 | 9000/9001 | Object storage for Milvus | curl /minio/health/live |
| milvus | milvusdb/milvus:v2.3.3 | 19530/9091 | Vector database | curl /healthz |
| python-server | custom (FastAPI) | 8080 | RAG pipeline | curl / |
| node-server | custom (Express) | 3001→3000 | REST API | curl /health |
| client | custom (Next.js) | 3000 | Frontend | curl / |

**Network:** `capstone_network` bridge (172.20.0.0/16)

**Volumes:**
- `etcd_data` → ETCD persistence
- `minio_data` → MinIO object storage
- `milvus_data` → Milvus indexes
- `./python-server/data` → Sample docs, BM25 indices
- `./node-server/uploads` → Temp file uploads
- `./node-server/logs` → Winston logs

---

## Build & Deploy

**Scripts:**

| Service | Dev | Build | Start |
|---------|-----|-------|-------|
| client | `yarn dev` | `yarn build` | `yarn start` |
| node-server | `yarn dev` (nodemon) | `yarn build` (tsc+tsc-alias) | `yarn start` |
| python-server | `python app/main.py` | Docker build | `docker-compose up` |
| translator | `python main.py` | Docker build | Batch only |
| llm | `python train.py` | Docker build | Batch only |

**Environment Variables:**

Key vars (see `env.example`):
- `DB_URL` — MongoDB connection string
- `ACCESS_TOKEN_VALIDITY_SEC` — JWT expiry (3600s default)
- `REFRESH_TOKEN_VALIDITY_SEC` — Refresh token expiry (86400s default)
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_BUCKET` — S3 upload
- `NEXT_PUBLIC_API_URL` — Frontend points to this API
- `EMBEDDING_MODEL` — BAAI/bge-base-en-v1.5 (can override)
- `HUGGING_FACE_HUB_TOKEN` — For HF model download
- `MILVUS_URI` — Milvus endpoint (http://milvus:19530 in Docker)

---

## Key Dependencies & Versions

| Package | Version | Purpose |
|---------|---------|---------|
| Next.js | 14.2.5 | Frontend framework |
| React | 18.2.0 | UI library |
| Tailwind | 3.3.2 | Styling |
| Express | 4.21.2 | API framework |
| Mongoose | 8.10.1 | MongoDB ODM |
| FastAPI | 0.115.12 | Python API framework |
| BAAI/bge-m3 | 1.3.4 | Embedding model |
| pymilvus | 2.4.10 | Vector DB client |
| rank-bm25 | 0.2.2 | BM25 ranking |
| torch | 2.7.0 | Deep learning framework |

---

## Monitoring & Logging

- **Frontend:** Browser console (Next.js dev tools)
- **Node API:** Winston (daily rotation) → `./node-server/logs/`
- **Python RAG:** stdout/stderr → Docker logs
- **Database:** MongoDB Atlas (if cloud) or local
- **Health checks:** All services expose `/health` or `/` endpoint (tested by Docker)

---

## Known Gaps

See [project-roadmap.md](./project-roadmap.md) for:
- Redis configured but unused
- Firebase Admin parsed but unused
- Rate-limit dependency not applied
- Hardcoded LLM IP address
- Duplicate auth hooks
- No test suites
