# Project Roadmap

## Current Status (v1.0 — MVP)

### ✅ Completed
- Full-stack RAG architecture (Next.js + Express + FastAPI)
- User authentication (JWT RS256, key rotation)
- PDF/DOCX/TXT file upload & processing
- Hybrid search (Milvus + BM25) with RRF fusion
- Cross-encoder re-ranking (ms-marco-MiniLM-L-6-v2)
- LLM inference chain (Llama 3.2 3B via remote HTTP)
- Workspace isolation (per-user, per-workspace)
- RSA 2048 per-user encryption
- Dark/light theme (next-themes)
- Docker Compose deployment
- Winston logging (daily rotation)
- Error handling with custom exception hierarchy

### 🚧 In Progress / Partial
- Test coverage (no unit/integration test suites yet)
- API documentation (no Swagger/OpenAPI)
- Monitoring/alerting (basic health checks only)
- Rate limiting (installed but not applied)

### ❌ Not Yet Started
- Mobile UI (desktop-first only)
- Advanced analytics dashboard
- Fine-tuned LLM (using pre-trained remote)
- Real-time collaboration
- OCR for scanned PDFs

---

## Known Issues & Technical Debt

### High Priority (Fix Before Production)

| Issue | Severity | Impact | Est. Effort | Notes |
|-------|----------|--------|------------|-------|
| **Hardcoded LLM endpoint IP** | 🔴 | Fragile; breaks if IP changes | 2h | Move `35.221.160.224:8000` to `LLM_ENDPOINT` env var |
| **Duplicate `useAuth` hook** | 🟠 | Maintenance burden | 1h | Remove one; unify in `context/` or `hooks/` |
| **Duplicate file upload paths** | 🟠 | Code smell; maintenance risk | 2h | Consolidate `/api/files/embed` + `/api/files/upload/{slug}` logic |
| **No test suites** | 🔴 | Undetected regressions | 20h+ | Add Jest (Frontend + Backend) + pytest (RAG) |
| **BM25 index versioning** | 🟠 | Stale indices on re-embed | 3h | Define invalidation strategy (delete + rebuild vs. merge) |

### Medium Priority (Before v1.1)

| Issue | Severity | Impact | Est. Effort | Notes |
|-------|----------|--------|------------|-------|
| **Protected route guard** | 🟡 | Verify ProtectedProvider blocks unauthenticated access | 2h | Add tests for redirect logic |
| **Redis configured but unused** | 🟡 | Dangling dependency; clutter | 4h | Decide: sessions? rate-limit store? cache? Remove if not needed |
| **Firebase Admin parsed but unused** | 🟡 | Dead code | 2h | Remove or implement (push notifications?) |
| **Rate limiting not applied** | 🟡 | Brute force attack vector on auth | 3h | Wire express-rate-limit to `/api/auth/*` |
| **API documentation missing** | 🟡 | Onboarding friction | 5h | Add Swagger/OpenAPI generation |
| **Monitoring minimal** | 🟡 | Blind spot for production issues | 8h | Add Prometheus + Grafana + alerts |

### Low Priority (Nice to Have)

| Issue | Severity | Impact | Est. Effort | Notes |
|-------|----------|--------|------------|-------|
| Pagination for large message history | 🟢 | UX: slow scroll with 1000+ messages | 2h | Lazy load or cursor-based pagination |
| Search across workspaces | 🟢 | User convenience | 3h | Global query without picking workspace |
| Conversation export (PDF/Markdown) | 🟢 | User request | 2h | Format chat history + sources |
| File metadata enrichment | 🟢 | Better source attribution | 3h | Extract author, date, summary from PDF |
| Batch operations | 🟢 | Admin convenience | 4h | Delete multiple files, re-embed all |

---

## Near-Term Roadmap (1–3 months)

### Phase 1: Stability & Testing (Weeks 1–2)

**Goal:** Make codebase production-ready

- [ ] Add Jest test suites (frontend components, auth flows)
- [ ] Add pytest for RAG service (embedding, retrieval, LLM chain)
- [ ] Set up CI/CD pipeline (GitHub Actions: lint, test, build)
- [ ] Fix duplicate `useAuth` hook (consolidate in `context/`)
- [ ] Move hardcoded LLM IP to `LLM_ENDPOINT` env var
- [ ] Apply rate limiting to auth endpoints (5 attempts/min)

**Metrics:**
- Test coverage ≥ 70% (lines of code)
- All CI checks pass on PR
- Zero hardcoded secrets in codebase

**Deliverables:**
- `.github/workflows/test.yml` (CI config)
- `__tests__/` directories in frontend and backend
- Updated `.env.example` with `LLM_ENDPOINT`

---

### Phase 2: Observability & Monitoring (Weeks 3–4)

**Goal:** Gain visibility into production behavior

- [ ] Set up Prometheus + Grafana (Docker Compose sidecar)
- [ ] Add Prometheus client libs (prom-client for Node, prometheus-client for Python)
- [ ] Create dashboards: Request rate, latency P95, error rate, Milvus health
- [ ] Configure alerting rules (service down, error rate > 10%, latency > 5s)
- [ ] Add distributed tracing (optional: Jaeger)
- [ ] Document runbook for common incidents

**Metrics:**
- Dashboard displays p99 query latency, error rate, service health
- Alerts fire within 60s of issue

**Deliverables:**
- `prometheus.yml` + `grafana/dashboards/` directory
- Alert rules in Prometheus config
- Runbook docs in `docs/runbooks/`

---

### Phase 3: Documentation & API (Weeks 5–6)

**Goal:** Enable external integration and onboarding

- [ ] Auto-generate Swagger/OpenAPI from Express routes
- [ ] Add API endpoint documentation with examples
- [ ] Create postman collection for manual testing
- [ ] Write onboarding guide for new developers
- [ ] Document RAG pipeline internals (embedding, retrieval, re-ranking)

**Deliverables:**
- `docs/api-docs.md` or `swagger.json`
- `docs/rag-pipeline-internals.md`
- Postman collection in `postman/`

---

### Phase 4: Minor UX Improvements (Weeks 7–8)

**Goal:** Polish user experience

- [ ] Message pagination (lazy load old messages)
- [ ] Consolidate file upload code paths (`/embed` vs `/upload/{slug}`)
- [ ] Add file metadata display (name, size, chunk count)
- [ ] Implement search history (recent queries)
- [ ] Add keyboard shortcuts (Cmd+K for search, Esc to close modals)

**Deliverables:**
- Updated API routes (`POST /api/files/upload`)
- New components in `client/app/components/`

---

## Medium-Term Roadmap (3–6 months)

### Phase 5: Advanced Retrieval

- [ ] Query expansion (rephrase user question → multiple sub-queries)
- [ ] Reranker chain (cross-encoder + diversity reranker)
- [ ] Graph-based retrieval (extract entity relationships from chunks)
- [ ] Multi-hop reasoning (chain of thought for complex questions)

**Effort:** 20–30 hours

---

### Phase 6: Improved Embedding

- [ ] Experiment with multi-vector retrieval (lexical + semantic + semantic-dense)
- [ ] Fine-tune embedding model on domain-specific corpus (optional)
- [ ] Implement dynamic chunking (adjust chunk size based on document type)
- [ ] Add multi-modal support (images, tables via LayoutLM or similar)

**Effort:** 25–35 hours

---

### Phase 7: LLM Improvements

- [ ] Deploy local LLM (quantized Llama 3.2 on GPU) instead of remote
- [ ] Fine-tune LLM on instruction-following tasks (use `translator/` + `llm/` services)
- [ ] Implement retrieval-aware LLM (context windows, prompt engineering)
- [ ] Add hallucination detection (confidence scoring, fact verification)

**Effort:** 30–40 hours (if local LLM) or 10–15 hours (if remote only)

---

### Phase 8: Scaling & Infrastructure

- [ ] Migrate to Kubernetes (EKS or GKE)
- [ ] Auto-scaling: HPA for frontend, API, RAG services
- [ ] Distributed Milvus cluster (HA mode)
- [ ] MongoDB sharding (if dataset grows > 100GB)
- [ ] CDN for static assets (CloudFront)

**Effort:** 40–50 hours

---

## Long-Term Vision (6+ months)

### Phase 9: Enterprise Features

- [ ] Role-based access control (RBAC): Admin, Editor, Viewer
- [ ] Audit logging (who accessed what, when)
- [ ] Single Sign-On (SSO: Okta, Google Workspace)
- [ ] Compliance (SOC 2, GDPR, HIPAA)
- [ ] Data retention policies (auto-delete after N days)

**Effort:** 50–60 hours

---

### Phase 10: Advanced Analytics

- [ ] Query analytics dashboard (popular queries, dwell time, satisfaction)
- [ ] Document analytics (most cited chunks, coverage gaps)
- [ ] User analytics (adoption, feature usage, churn)
- [ ] Cost estimation (API calls, embedding compute, storage)

**Effort:** 20–30 hours

---

### Phase 11: Mobile & Progressive Web App

- [ ] Responsive UI for tablets (iPad)
- [ ] PWA features (offline mode, push notifications)
- [ ] Native mobile apps (React Native or Flutter) — optional

**Effort:** 30–50 hours

---

### Phase 12: Ecosystem & Integrations

- [ ] Slack bot integration (query via Slack)
- [ ] Notion/Google Drive sync (auto-index documents)
- [ ] Zapier integration (IFTTT automation)
- [ ] Webhooks (notify external systems on certain events)

**Effort:** 20–40 hours

---

## Dependency & Decision Matrix

### Blocking Issues (Block Everything Until Resolved)

| Issue | Blocker For | Owner | Timeline |
|-------|-----------|-------|----------|
| Hardcoded LLM IP | Prod deployment | Backend lead | Week 1 |
| No test coverage | CI/CD enforcement | QA / All leads | Week 2 |
| Duplicate auth hooks | Code stability | Frontend lead | Week 1 |

### Decision Points (Requires Input)

| Decision | Options | Recommendation | Timeline |
|----------|---------|-----------------|----------|
| **Redis use case** | (A) Remove, (B) Sessions, (C) Rate-limit store, (D) Cache | Recommend (A) remove if unused; else (C) rate-limit store | Week 1 |
| **Firebase use case** | (A) Remove, (B) Push notifications, (C) Auth provider | Recommend (A) remove; not in MVP scope | Week 1 |
| **Local vs. Remote LLM** | (A) Keep remote (simple), (B) Deploy local (control, cost) | Recommend (A) remote for MVP; (B) later if cost/latency issues | Month 3 |
| **Kubernetes adoption** | (A) Stay on Docker Compose, (B) Migrate to K8s | Recommend (A) until 10x growth; (B) when scaling | Month 4 |
| **Mobile strategy** | (A) Responsive web only, (B) PWA, (C) Native apps | Recommend (A) v1, then (B) if demand | Month 6 |

---

## Success Metrics

### MVP Success (Current)
- ✅ All services deploy via Docker Compose
- ✅ User can register, login, upload PDFs, query, get answers < 5s
- ✅ Query accuracy (MRR) ≥ 0.8
- ✅ System uptime ≥ 99%
- ✅ Auth security (failed logins < 1%)

### Phase 1–2 Success (Month 1)
- Test coverage ≥ 70%
- CI/CD pipeline enforces all tests pass
- Zero prod incidents due to missing error handling
- Mean time to resolution (MTTR) < 5 min for common issues

### Phase 3–4 Success (Month 2)
- API fully documented with Swagger
- Zero customer support questions about "how to use API"
- 90% of new developers onboard within 2 hours
- File consolidation reduces API endpoints from 2 to 1

### Phase 5–8 Success (Month 4)
- Query latency P95 < 3s (currently ~5s)
- Embedding accuracy improves via fine-tuning
- System scales to 10x current load without re-architecture
- Cost per query decreases 30% (via local LLM)

---

## Resource Allocation

### Team Composition
- **Backend Lead:** Responsible for Phase 1–2 (tests, hardcoded fixes)
- **Frontend Lead:** Responsible for Phase 2 (monitoring client), Phase 4 (UX)
- **DevOps:** Responsible for Phase 2 (infra), Phase 5–8 (scaling)
- **ML Engineer:** Responsible for Phase 6–7 (embedding, LLM fine-tuning)
- **Product Manager:** Prioritization, timeline negotiation

### Estimated Capacity
- **Sprint velocity:** 20–25 hours/week (accounting for overhead)
- **Runway:** 3 months to Phase 3; 6 months to Phase 5

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Remote LLM endpoint goes down | 🟠 High (external service) | Users can't query | (1) Add fallback response, (2) Deploy local LLM |
| Milvus performance degrades at scale | 🟡 Medium | Queries slow down | (1) Monitor query latency, (2) Add caching, (3) Shard collection |
| MongoDB storage exceeds limits | 🟡 Medium | No new documents | (1) Set up archival, (2) Implement retention policy |
| Embedding model becomes outdated | 🟡 Medium | Accuracy drops | (1) Monitor benchmark performance, (2) Fine-tune on new data |
| Key dev leaves team | 🟠 High (small team) | Knowledge loss | (1) Document internals, (2) Cross-train, (3) Code reviews |

---

## Dependencies

### External
- **MongoDB Atlas:** Managed database; SLA 99.9%
- **AWS S3:** File storage; SLA 99.99%
- **External LLM endpoint** (35.221.160.224): Single point of failure → FIX ASAP
- **HuggingFace Hub:** Model downloads (internet-dependent)

### Internal
- Milvus ← Python RAG service
- Python RAG service ← Node API
- Node API ← Frontend
- Frontend ← All services (health checks)

**Critical path:** External LLM endpoint → (Mitigation: add timeout + fallback response)

---

## Budget & Timeline

### Phase 1–2 (MVP Hardening)
- **Timeline:** 2–3 weeks
- **Effort:** 30–40 hours
- **Cost:** ~$2,000–3,000 (developer time)

### Phase 3–4 (Documentation & UX)
- **Timeline:** 2 weeks
- **Effort:** 15–20 hours
- **Cost:** ~$1,000–1,500

### Phase 5–8 (Advanced Features)
- **Timeline:** 8–12 weeks
- **Effort:** 100–150 hours
- **Cost:** ~$7,000–10,000

### Total (Months 1–6)
- **Timeline:** 6 months
- **Total Effort:** 200–250 hours
- **Total Cost:** ~$12,000–16,000

---

## Stakeholder Sign-Off

- [ ] Product Owner: Approve roadmap priorities
- [ ] Backend Lead: Commit to Phase 1–2 timeline
- [ ] Frontend Lead: Commit to Phase 4 timeline
- [ ] DevOps: Commit to Phase 2, 5–8 timeline
- [ ] ML Lead: Commit to Phase 6–7 timeline (if applicable)

---

## Review Schedule

- **Monthly:** Roadmap review, reprioritization based on user feedback
- **Quarterly:** Deep dive on completed phases, lessons learned
- **Biannually:** Strategic review, pivot if needed

See [project-overview-pdr.md](./project-overview-pdr.md) for current status and acceptance criteria.
