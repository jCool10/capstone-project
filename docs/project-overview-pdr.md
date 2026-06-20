# Project Overview & PDR (Product Development Requirements)

**Project:** RAG Chat with PDF — Capstone Project

**Type:** Full-stack web application with microservices architecture

**Description:** Multi-user system for intelligent conversation with PDF documents via Retrieval-Augmented Generation (RAG). Users upload PDFs into workspaces, then query them using an AI chat interface powered by hybrid semantic + keyword search and LLM inference.

## Problem & Goals

### Problem
- Manual document analysis is time-consuming (searching, cross-referencing, synthesizing)
- Standard keyword search misses semantic relationships in document content
- No native solution for multi-document Q&A with source attribution

### Goals
1. Enable users to ask questions about PDF content and receive accurate, sourced answers
2. Build hybrid retrieval (vector embeddings + BM25) for robust search across different document styles
3. Provide secure per-user workspace isolation with end-to-end encryption
4. Support iterative Q&A with conversation history
5. Ship production-ready stack (Docker, monitoring, error handling)

## Target Users

| User Type | Use Case |
|-----------|----------|
| Students/Teachers | Search lecture notes, textbooks, research papers |
| Researchers | Analyze multi-paper citations and cross-references |
| Business Analysts | Extract insights from contracts, reports, policies |
| Legal Professionals | Review compliance documents, precedents |
| Data Scientists | Query datasets, methodology docs, ML papers |

## Scope

### In Scope
- User registration, login, JWT authentication, key rotation
- PDF/DOCX/TXT upload (max 10 files, max 100MB per workspace)
- Vector embeddings (BAAI/bge-m3, 1024-dim)
- Hybrid search: Milvus (dense L2/COSINE) + BM25 (with Vietnamese tokenizer)
- Result re-ranking (cross-encoder: ms-marco-MiniLM-L-6-v2)
- LLM inference (Llama 3.2 3B via remote HTTP)
- Workspace management (create, switch, isolation)
- Chat history per workspace
- RSA 2048 per-user keypair for encryption
- Dark/light theme (responsive to 1024px min-width)

### Out of Scope
- Real-time collaborative editing
- OCR for scanned PDFs
- Mobile-first design (desktop primary)
- Advanced analytics dashboard
- Fine-tuned LLM deployment (uses pre-trained remote)
- Multi-language UI translation (Vietnamese labels only)

## Success Metrics

| Metric | Target | Validation |
|--------|--------|-----------|
| Upload latency | < 30s per 10MB PDF | Performance test |
| Query end-to-end | < 5s response | Load test p95 |
| Retrieval accuracy | MRR ≥ 0.8 on ground truth | RAGEvaluator script |
| System uptime | 99% | Monitoring logs |
| Auth security | < 1 failed login per 100 attempts | Audit trail |
| User success rate | > 90% complete RAG cycle | User feedback |

## Technical Constraints

| Constraint | Rationale |
|-----------|-----------|
| Node 18+, Python 3.11 | LTS stability for production |
| TypeScript strict mode | Catch errors at compile-time |
| RSA 2048-bit keys | Industry standard security |
| Docker Compose | Reproducible multi-service deployment |
| Milvus v2.3.3 | Stable vector DB with proven scaling |
| Max 10 files per embed | Prevent single-request timeout |
| 1024-dim embeddings | Balance accuracy vs memory/latency |
| Express 4.21, FastAPI 0.115 | Stable, production-ready frameworks |

## Architecture Overview

```
┌─────────────────────────────────────────┐
│  Frontend Layer (Next.js 14 + React 18) │
│  • Protected routes (/, /create, /workspace/*) │
│  • Auth routes (/login, /register) │
│  • Dark mode + Tailwind styling │
└────────────────┬────────────────────────┘
                 │ REST API (Axios)
                 │ Authorization: Bearer {accessToken}
┌────────────────▼────────────────────────┐
│   API Gateway (Express 4.21 + TS)       │
│   • JWT validation (RS256)               │
│   • File upload to S3                    │
│   • Workspace isolation logic            │
│   • Error handling & logging (Winston)   │
└────────────────┬────────────────────────┘
         ┌───────┴────────┐
         │                │
  ┌──────▼──────┐  ┌──────▼────────┐
  │  MongoDB    │  │  AWS S3       │
  │ (users,     │  │  (PDF files)  │
  │  workspaces,│  │               │
  │  messages)  │  │               │
  └─────────────┘  └─────────────┬─┘
                                 │ S3 download
                    ┌────────────▼──────────────────┐
                    │  RAG Service (FastAPI)        │
                    │  • File parsing (PDF, DOCX)   │
                    │  • Chunking (512 tok, 128 ov) │
                    │  • Embedding (BAAI/bge-m3)    │
                    │  • Hybrid search (Milvus+BM25)│
                    │  • Re-ranking (cross-encoder) │
                    │  • LLM chain (remote HTTP)    │
                    └────────────┬───────────────────┘
                        ┌────────┴────────┐
                        │                 │
                 ┌──────▼──────┐  ┌───────▼──────────┐
                 │  Milvus     │  │  BM25 indices    │
                 │  Vector DB  │  │  (persisted)     │
                 │             │  │                  │
                 └─────────────┘  └──────────────────┘
```

## Data Flow — Query Execution

```
1. User submits query in /workspace/[slug] chat
   └─> Frontend POST /api/files/workspace/:slug/query
       
2. Node API validates auth + workspace access
   └─> Creates Message record (status: pending)
   
3. Call Python RAG service: POST http://python-server:8080/query
   {
     "query": "What is machine learning?",
     "collection_name": "workspace_abc123",
     "history": ["What is AI?", "Define neural networks"]
   }
   
4. Python RAG Pipeline:
   a) Embed query → BAAI/bge-m3 → 1024-dim vector
   b) Dense search → Milvus k=20 candidates
   c) Sparse search → BM25 k=20 candidates
   d) Fusion → RRF (k=60) or linear weighted average
   e) Re-rank → cross-encoder top-5 candidates
   f) Build prompt with chunks + history
   g) Call LLM: POST http://35.221.160.224:8000/v1/chat/completions
   h) Return {docs: [...], response: "...", search_stats: {...}}
   
5. Node API:
   a) Encrypt response with user's public key
   b) Store Message record with source docs
   c) Return to frontend
   
6. Frontend displays:
   a) LLM response in chat
   b) Source documents with links
   c) Conversation history (paginated)
```

## Acceptance Criteria

- [ ] All 6 services launch via `docker-compose up` without errors
- [ ] Register → Login → Workspace creation flow completes (< 10s)
- [ ] Upload 5 PDFs (10 MB each), embedding completes (< 2 min)
- [ ] Query returns top-5 results + LLM response (< 5s)
- [ ] Source documents marked with file name + page/section
- [ ] Workspace isolation: user cannot access other users' workspaces
- [ ] JWT refresh token prevents re-login on expiry
- [ ] RSA encryption/decryption end-to-end (encryption works for >1KB text)
- [ ] Dark mode persists across sessions
- [ ] Health check endpoints return 200 for all services
- [ ] Logs rotated daily, no log file > 100 MB

## Known Limitations & Roadmap Items

See [project-roadmap.md](./project-roadmap.md) for:
- Unused dependencies (Redis, Firebase Admin)
- Hardcoded LLM endpoint IP (needs env var)
- Duplicate auth hooks and file upload code paths
- Missing test coverage
- BM25 index versioning strategy

## Key Design Decisions

1. **RSA per-user keypairs:** Each user gets a keypair stored in DB; private key encrypted with MASTER_ENCRYPTION_KEY. Enables future PKI extensions (message signing, audit trails).

2. **Hybrid search with fusion:** Dense embeddings catch semantic similarity; sparse BM25 catches exact terms. RRF (reciprocal rank fusion) balances both without parameter tuning.

3. **Sentence-level chunking:** 512 tokens, 128 token overlap, hierarchical (paragraph → sentence). Preserves context better than fixed-size chunks.

4. **Cross-encoder re-ranking:** After fusion, pick top-5 by cross-encoder score. Expensive but ensures quality for LLM context window.

5. **Remote LLM (not local):** Uses external HTTP endpoint for inference. Reduces deployment complexity; trades off latency for maintainability.

6. **Workspace isolation at API layer:** Each query checks `user_id` matches workspace owner. Prevents data leakage.

7. **Docker Compose (not K8s):** Single-machine deployment. Scales vertically; simpler operations.

## Related Documentation

- [Codebase Summary](./codebase-summary.md) — Service-by-service breakdown
- [Code Standards](./code-standards.md) — Style, structure, error handling patterns
- [System Architecture](./system-architecture.md) — Detailed diagrams, auth/encryption flows
- [Deployment Guide](./deployment-guide.md) — Running Docker, env vars, troubleshooting
- [Project Roadmap](./project-roadmap.md) — Known gaps, future work
