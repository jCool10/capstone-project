# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

Polyglot monorepo (no workspace manager). Each service has its own dependencies and is built/run independently.

| Path | Stack | Port |
|---|---|---|
| `client/` | Next.js 14 (App Router), React 18, TypeScript, Tailwind + shadcn/ui | 3000 |
| `node-server/` | Express 4 + TypeScript, Mongoose, JWT RS256, AWS S3, Winston | 3001 → container 3000 |
| `python-server/` | FastAPI, BAAI/bge-m3 embeddings, Milvus, BM25, cross-encoder reranker | 8080 |
| `translator/` | Python EN→VI translation pipeline (VinAI seq2seq, googletrans fallback) | — |
| `llm/` | Python LoRA fine-tuning (unsloth, PEFT, TRL) for Llama 3.2 3B | — |

Infra services (via `docker-compose.yml`): etcd, MinIO (9000/9001), Milvus standalone (19530/9091).

Detailed per-service breakdown: `docs/codebase-summary.md`. Diagrams: `docs/system-architecture.md`.

## Common commands

### Whole stack (Docker)

```bash
cp env.example .env                  # then fill in DB_URL, AWS_*, HUGGING_FACE_HUB_TOKEN
docker-compose up -d                 # wait ~2 min for Milvus init
docker-compose ps                    # check health
docker-compose logs -f <service>
docker-compose down                  # stop; add -v to wipe volumes
```

### `client/` (yarn)

```bash
cd client
yarn install
yarn dev                             # http://localhost:3000
yarn typecheck                       # tsc --noEmit
yarn lint           / yarn lint:fix
yarn format:check   / yarn format:write
yarn build          / yarn start
```

### `node-server/` (yarn)

```bash
cd node-server
yarn install
yarn dev                             # nodemon, watches src/
yarn build                           # rimraf dist + tsc + tsc-alias (path aliases)
yarn start                           # node dist/index.js
yarn lint           / yarn lint:fix
yarn prettier       / yarn prettier:fix
```

**Important:** the build step requires `tsc-alias` to rewrite TS path aliases — running plain `tsc` is not enough.

### `python-server/`

```bash
cd python-server
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app/main.py                   # http://localhost:8080
```

Requires a reachable Milvus (`MILVUS_URI`, defaults to `http://localhost:19530`).

### Tests

No test suites exist yet in any service. Adding them is on the roadmap (`docs/project-roadmap.md`). Until then, verify changes via the running stack and the health endpoints below.

### Health checks

```bash
curl http://localhost:3000           # Frontend
curl http://localhost:3001/health    # Node API
curl http://localhost:8080/          # RAG service
curl http://localhost:9091/healthz   # Milvus
```

## Architecture — the big picture

### Request flow (query path)

1. **Browser** → `client/` calls `node-server` with `Authorization`, `refresh-token`, and `client-id` headers (Axios interceptor in `client/utils/axios.ts` handles refresh-on-401 with a batched-pending queue).
2. **`node-server`** verifies the JWT against the per-user public key stored in the `Keystore` collection (RS256). Workspace ownership is enforced by `userId` checks in `FilesService`.
3. For `POST /api/files/workspace/:slug/query`, `node-server` forwards the query to `python-server` at `POST /query` (`http://python-server:8080` in Docker, `http://0.0.0.0:8080` locally).
4. **`python-server`** runs the RAG pipeline:
   - **Hybrid retrieve** — Milvus dense search (k=20) + BM25 sparse search (k=20, Vietnamese-aware via `underthesea`, falls back to simple split). Fused via RRF (`k=60`) by default, or linear blend (α=0.6 dense / 0.4 sparse).
   - **Rerank** — cross-encoder `ms-marco-MiniLM-L-6-v2` selects final top-5.
   - **LLM** — remote HTTP call to `35.221.160.224:8000/v1/chat/completions` (currently hardcoded; see roadmap).
5. Response returns through `node-server` (wrapped in `SuccessResponse`) to the chat UI with source documents attached.

### Embed path

`POST /api/files/embed` (multipart, max 10 files) → multer-S3 uploads to AWS S3 → `node-server` downloads to OS tmpdir → calls `python-server` `POST /embed` with file paths and `collection_name` → `FileLoader` (PDF/DOCX/TXT) → `sentence_splitter` (chunk 512, overlap 128) → `BAAI/bge-m3` embeddings (1024-dim) → Milvus collection + BM25 index persisted at `data/bm25_indices/{collection}.pkl`. Embedding runs in a `ThreadPoolExecutor` (`max_workers=4`).

### Auth & encryption

- Login issues an access token + a Keystore entry containing the public key, signed refresh token, and a `keyId`.
- Each user has a `UserKeyPair` (RSA) whose private key is encrypted with `MASTER_ENCRYPTION_KEY` before storage. `POST /api/auth/encrypt` / `decrypt` use these keys; `rotate-keys` issues a new pair while preserving history (`status: 'active' | 'revoked' | 'decrypt-only'`).
- Middleware lives in `node-server/src/middlewares/authentication.ts` and `errorHandler.ts`. Custom error classes (`BaseError`, `NotFoundError`, `BadRequestError`, …) in `src/core/` produce a uniform JSON error shape.

### Frontend routing

App Router with two route groups:
- `(auth)/` — public: `/login`, `/register`, `/forgot-password`. Plain layout, no sidebar.
- `(root)/` — protected: `/`, `/create`, `/workspace/[slug]`. Sidebar layout via `components/layouts/`.

Auth state lives in `context/AuthContext.tsx` and is persisted in `localStorage` (`accessToken`, `refreshToken`, `user`). React Query (`components/providers/ProtectedProvider`) handles server state and cache invalidation on upload.

## Known gotchas

- **Two file-upload code paths**: `apis/files.ts` calls `/api/files/embed` (multipart via Axios) while the workspace page uses a direct `fetch` to `/api/files/upload/{workspaceSlug}`. Pick one before adding upload features. (See `docs/project-roadmap.md`.)
- **Duplicate `useAuth` hook**: defined in both `context/AuthContext.tsx` and `hooks/useAuth.ts`. The hooks/ version wraps mutations; the context version is the raw consumer. Don't import both in the same file.
- **Hardcoded LLM endpoint** in `python-server` (`35.221.160.224:8000`). Treat as a TODO; do not bake new hardcoded URLs.
- **Redis (IORedis) and Firebase Admin** are wired into `node-server` config but unused. Don't import them until a use case is decided.
- **Rate-limit middleware** is in `package.json` but not applied to routes — auth endpoints are currently unprotected against brute force.
- **`HUGGING_FACE_HUB_TOKEN`** is declared in `env.example` but HF model downloads run unauthenticated. Required only for gated models.
- **Build cache invalidation for BM25**: re-embedding a collection does not version the BM25 pickle. Delete the file under `data/bm25_indices/` if you change the chunking strategy.

## Conventions

- **TypeScript strict** is on in both `client/` and `node-server/`. Avoid `any`.
- **File naming**: kebab-case in JS/TS/shell; snake_case in Python; PascalCase for React component files (`ChatBubble.tsx`).
- **Path aliases**: `node-server` uses `@/` aliases resolved by `tsc-alias` at build time. `client` uses Next.js's default `@/` alias.
- **Response shape (node-server)**: always wrap in `SuccessResponse` (`{ status, message, data }`); throw a `BaseError` subclass for failures — the global `errorHandler` formats them.
- **Logging**: Winston with `winston-daily-rotate-file` in `node-server` (`logs/app-YYYY-MM-DD.log`); stdlib `logging` in Python. Never log passwords, tokens, or full emails.
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, …). Do not add AI-tool references in messages.
- **Markdown**: per `.claude/rules/`, only create new `.md` files under `docs/` or `plans/` unless the user explicitly asks otherwise.

Deeper conventions per service: `docs/code-standards.md`. Design tokens / shadcn patterns: `docs/design-guidelines.md`. Deployment & troubleshooting: `docs/deployment-guide.md`.
