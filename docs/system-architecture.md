# System Architecture

## High-Level Component Diagram

```mermaid
graph TB
    subgraph Client["Frontend Layer"]
        UI["Next.js App<br/>(React 18 + Tailwind)"]
        Store["React Query<br/>(State Management)"]
    end

    subgraph API["API Gateway"]
        Auth["Auth Service<br/>(JWT RS256)"]
        Files["Files Service<br/>(Upload, Query)"]
        Enc["Encryption Service<br/>(RSA per-user)"]
    end

    subgraph Data["Data Layer"]
        DB["MongoDB<br/>(Users, Workspaces, Messages)"]
        S3["AWS S3<br/>(PDFs)"]
    end

    subgraph RAG["RAG Service"]
        Loader["File Loader<br/>(PDF, DOCX, TXT)"]
        Split["Text Splitter<br/>(512 tok, 128 ov)"]
        Embed["Embedding Model<br/>(BAAI/bge-m3)"]
        Hybrid["Hybrid Search<br/>(Milvus + BM25)"]
        Rerank["Re-ranker<br/>(cross-encoder)"]
        LLM["LLM Chain<br/>(Remote HTTP)"]
    end

    subgraph Storage["Vector Storage"]
        Milvus["Milvus<br/>(Vector DB)"]
        BM25["BM25 Index<br/>(Persisted)"]
    end

    UI --> Store
    Store --> Auth
    Store --> Files
    Files --> Enc
    
    Auth --> DB
    Files --> DB
    Files --> S3
    Files --> Loader
    
    Loader --> Split
    Split --> Embed
    Embed --> Milvus
    Embed --> BM25
    
    Files --> Hybrid
    Hybrid --> Milvus
    Hybrid --> BM25
    Hybrid --> Rerank
    Rerank --> LLM
    LLM -.->|HTTP| ExtLLM["External LLM<br/>(Llama 3.2 3B)"]
```

---

## Query Execution Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant NodeAPI
    participant PyRAG
    participant Milvus
    participant BM25
    participant Reranker
    participant ExtLLM

    User->>Frontend: Type query
    Frontend->>NodeAPI: POST /api/files/workspace/slug/query<br/>{query, history}
    
    NodeAPI->>NodeAPI: Validate auth + workspace
    NodeAPI->>NodeAPI: Create Message record
    
    NodeAPI->>PyRAG: POST /query<br/>{query, collection, history}
    
    PyRAG->>PyRAG: Embed query (BAAI/bge-m3)
    
    par Dense Search
        PyRAG->>Milvus: Search k=20
        Milvus-->>PyRAG: Dense results
    and Sparse Search
        PyRAG->>BM25: Search k=20
        BM25-->>PyRAG: Sparse results
    end
    
    PyRAG->>PyRAG: Fuse (RRF or linear)
    PyRAG->>Reranker: Score top candidates
    Reranker-->>PyRAG: Ranked top-5
    
    PyRAG->>PyRAG: Build prompt with chunks + history
    PyRAG->>ExtLLM: POST /v1/chat/completions
    ExtLLM-->>PyRAG: Response text
    
    PyRAG-->>NodeAPI: {docs, response, stats}
    
    NodeAPI->>NodeAPI: Encrypt response (RSA)
    NodeAPI->>NodeAPI: Store Message + sources
    NodeAPI-->>Frontend: Response + metadata
    
    Frontend->>Frontend: Decrypt + render
    Frontend-->>User: Display chat + sources
```

---

## Embedding & File Processing Pipeline

```mermaid
graph LR
    File["PDF/DOCX/TXT File<br/>(from S3)"] -->|Download| Loader["FileLoader<br/>(pypdf, python-docx)"]
    
    Loader -->|Extract text| Split["TextSplitter<br/>(sentence-level,<br/>512 tok, 128 ov)"]
    
    Split -->|List of chunks| Embed["Embedding Model<br/>(BAAI/bge-m3,<br/>batch_size=32)"]
    
    Embed -->|Embeddings<br/>1024-dim| MilvusStore["MilvusStore<br/>(add_vectors)"]
    
    Embed -->|Chunk text| BM25Build["BM25Index.build<br/>(VinAI tokenizer<br/>for Vietnamese)"]
    
    MilvusStore -->|Indexed vectors| Milvus["Milvus Collection<br/>(L2/COSINE metric)"]
    
    BM25Build -->|Persisted| BM25File["bm25_indices/<br/>collection.pkl"]
    
    MilvusStore -->|Result| Result["EmbedResult:<br/>status, chunks, files"]
```

---

## Authentication & Key Rotation Flow

```mermaid
sequenceDiagram
    participant Client
    participant NodeAPI
    participant MongoDB
    participant JWT

    Client->>NodeAPI: POST /api/auth/register<br/>{email, password}
    NodeAPI->>NodeAPI: Hash password (bcrypt, 12 rounds)
    NodeAPI->>MongoDB: Create User + UserKeyPair
    NodeAPI->>NodeAPI: Generate RSA 2048 keypair
    NodeAPI->>MongoDB: Encrypt privKey with MASTER_ENCRYPTION_KEY
    NodeAPI-->>Client: User ID

    Client->>NodeAPI: POST /api/auth/login<br/>{email, password}
    NodeAPI->>MongoDB: Fetch User
    NodeAPI->>NodeAPI: Compare password hash
    NodeAPI->>JWT: Sign token (RS256, privateKey)
    NodeAPI->>MongoDB: Store refreshToken in Keystore
    NodeAPI-->>Client: {accessToken, refreshToken, expiresIn}

    Client->>NodeAPI: Request with accessToken
    NodeAPI->>MongoDB: Fetch user's publicKey
    NodeAPI->>JWT: Verify token signature
    NodeAPI-->>Client: Response (if valid)

    Client->>NodeAPI: POST /api/auth/refresh-token
    NodeAPI->>MongoDB: Lookup refreshToken in Keystore
    NodeAPI->>JWT: Issue new accessToken
    NodeAPI-->>Client: {accessToken, expiresIn}

    Client->>NodeAPI: POST /api/auth/rotate-keys
    NodeAPI->>NodeAPI: Generate new RSA keypair
    NodeAPI->>MongoDB: Update UserKeyPair + Keystore
    NodeAPI-->>Client: Key rotation complete
```

---

## Encryption/Decryption Flow

```mermaid
graph TB
    subgraph ClientSide["Client Side"]
        PlainData["Plaintext Data"]
        PublicKey["User's Public Key<br/>(from /api/auth/public-key)"]
        Encrypt["Browser Crypto<br/>RSA-OAEP"]
        CipherData["Ciphertext"]
    end

    subgraph ServerSide["Server Side"]
        Request["POST /api/auth/encrypt<br/>{data}"]
        GetPrivKey["Fetch encryptedPrivKey<br/>from MongoDB"]
        DecryptPriv["Decrypt privKey<br/>using MASTER_ENCRYPTION_KEY"]
        EncryptData["RSA-OAEP encrypt<br/>with public key"]
        ResponseEnc["Return encrypted data"]
    end

    subgraph DecryptSide["Decryption"]
        GetEncryptedPrivKey["Fetch encryptedPrivKey<br/>from MongoDB"]
        DecryptPrivKey["Decrypt using MASTER_KEY"]
        DecryptRequest["POST /api/auth/decrypt<br/>{ciphertext}"]
        RSADecrypt["RSA-OAEP decrypt<br/>with private key"]
        PlaintextResponse["Return plaintext"]
    end

    PlainData --> PublicKey
    PublicKey --> Encrypt
    Encrypt --> CipherData
    CipherData --> Request
    
    Request --> GetPrivKey
    GetPrivKey --> DecryptPriv
    DecryptPriv --> EncryptData
    EncryptData --> ResponseEnc
    
    CipherData -.->|For decryption| GetEncryptedPrivKey
    GetEncryptedPrivKey --> DecryptPrivKey
    DecryptPrivKey --> DecryptRequest
    DecryptRequest --> RSADecrypt
    RSADecrypt --> PlaintextResponse
```

---

## Workspace Isolation Architecture

```mermaid
graph TB
    subgraph User1["User 1 (ABC123)"]
        WS1["Workspace A<br/>slug: ws-prod"]
        Files1["files.pdf<br/>data.docx"]
        Msgs1["Message history"]
    end

    subgraph User2["User 2 (XYZ789)"]
        WS2["Workspace B<br/>slug: ws-test"]
        Files2["report.pdf"]
        Msgs2["Message history"]
    end

    subgraph MongoDB["MongoDB Collections"]
        Users["Users Collection"]
        Workspaces["Workspaces Collection"]
        Messages["Messages Collection"]
        KeyPairs["UserKeyPair Collection"]
    end

    subgraph S3["AWS S3 Bucket"]
        S3User1["User1/<br/>ws-prod/"]
        S3User2["User2/<br/>ws-test/"]
    end

    subgraph Milvus["Milvus Collections"]
        Milvus1["ws-prod<br/>(User1)"]
        Milvus2["ws-test<br/>(User2)"]
    end

    User1 --> WS1
    WS1 --> Files1
    WS1 --> Msgs1

    User2 --> WS2
    WS2 --> Files2
    WS2 --> Msgs2

    WS1 -.->|Query checks<br/>userId| Users
    WS1 -.->|Isolation layer| Workspaces
    Msgs1 -.->|workspaceSlug<br/>match| Messages

    Files1 -.->|S3 prefix| S3User1
    Files2 -.->|S3 prefix| S3User2

    WS1 -.->|Collection<br/>name| Milvus1
    WS2 -.->|Collection<br/>name| Milvus2
```

---

## Docker Compose Service Dependencies

```mermaid
graph TD
    subgraph MilvusStack["Milvus Stack"]
        ETCD["ETCD<br/>v3.5.5<br/>port: 2379"]
        MinIO["MinIO<br/>port: 9000/9001"]
        Milvus["Milvus<br/>v2.3.3<br/>port: 19530"]
    end

    subgraph Services["Application Services"]
        PyServer["python-server<br/>FastAPI<br/>port: 8080"]
        NodeServer["node-server<br/>Express<br/>port: 3001→3000"]
        Client["client<br/>Next.js<br/>port: 3000"]
    end

    subgraph External["External Dependencies"]
        MongoDB["MongoDB<br/>(Atlas or local)"]
        S3["AWS S3"]
        ExtLLM["External LLM<br/>(HTTP endpoint)"]
    end

    ETCD --> Milvus
    MinIO --> Milvus
    Milvus --> PyServer
    
    PyServer --> NodeServer
    NodeServer --> Client
    
    PyServer -.->|MILVUS_URI| Milvus
    NodeServer -.->|DB_URL| MongoDB
    NodeServer -.->|S3 creds| S3
    PyServer -.->|HTTP POST| ExtLLM
```

---

## Data Model Relationships

```mermaid
erDiagram
    USER ||--o{ WORKSPACE : owns
    USER ||--o{ KEYSTORE : has
    USER ||--o{ USERKEYPAIR : "has RSA"
    
    WORKSPACE ||--o{ MESSAGE : contains
    WORKSPACE ||--o{ FILE : has
    
    MESSAGE ||--o{ SOURCE_DOC : references
    
    USER {
        ObjectId _id
        string email
        string password_hash
        datetime created_at
    }
    
    WORKSPACE {
        ObjectId _id
        string slug
        ObjectId userId
        string name
        boolean isEmbedded
        array filePaths
        array fileKeys
        datetime created_at
    }
    
    MESSAGE {
        ObjectId _id
        string workspaceSlug
        array messages
        datetime created_at
    }
    
    FILE {
        string name
        string key
        string s3_url
        int fileSize
        array chunks
    }
    
    SOURCE_DOC {
        string content
        object metadata
        float score
        string source_file
    }
    
    KEYSTORE {
        string userId
        string publicKey
        string refreshToken
        string signature
        string keyId
    }
    
    USERKEYPAIR {
        string userId
        string encryptedPrivateKey
        string algorithm
        string status
    }
```

---

## Hybrid Search Fusion Logic

```mermaid
graph LR
    Query["User Query"]
    QEmbed["Embed Query<br/>(BAAI/bge-m3)"]
    
    subgraph DenseSearch["Dense Search"]
        MVSearch["Milvus.search<br/>k=20"]
        MVResults["Dense Results<br/>with scores"]
    end
    
    subgraph SparseSearch["Sparse Search"]
        BM25Search["BM25.search<br/>k=20"]
        BM25Results["Sparse Results<br/>with scores"]
    end
    
    Query --> QEmbed
    QEmbed --> MVSearch
    QEmbed --> BM25Search
    
    MVSearch --> MVResults
    BM25Search --> BM25Results
    
    MVResults --> Fusion{Fusion Method}
    BM25Results --> Fusion
    
    Fusion -->|RRF| RRFMethod["Reciprocal Rank Fusion<br/>score = 1/(k + rank)"]
    Fusion -->|Linear| LinearMethod["Weighted Sum<br/>score = 0.6*dense + 0.4*sparse"]
    
    RRFMethod --> Normalize["Normalize & Sort"]
    LinearMethod --> Normalize
    
    Normalize --> TopK["Select Top-5"]
    TopK --> Rerank["Re-ranker<br/>(cross-encoder)"]
    Rerank --> Final["Final Top-5"]
```

---

## Re-ranking Pipeline

```mermaid
sequenceDiagram
    participant Fusion as Fused Results<br/>k=5-10
    participant Reranker as Cross-encoder Model<br/>ms-marco-MiniLM-L-6-v2
    participant Score as Scoring
    participant Output as Top-5 Ranked

    Fusion->>Reranker: For each pair<br/>(query, doc)
    
    loop For k documents
        Reranker->>Score: Compute relevance score<br/>(0 to 1)
        Score-->>Reranker: Score
    end
    
    Reranker-->>Output: Sort by score (descending)
    Output-->>Output: Select top-5
```

---

## Error Handling & Recovery

```mermaid
graph TD
    Request["Incoming Request"]
    
    Request --> Auth{Auth Valid?}
    Auth -->|No| AuthErr["UnauthorizedError<br/>401"]
    Auth -->|Yes| Validate{Data Valid?}
    
    Validate -->|No| ValErr["BadRequestError<br/>400"]
    Validate -->|Yes| Resource{Resource Exists?}
    
    Resource -->|No| NotFound["NotFoundError<br/>404"]
    Resource -->|Yes| Permission{User Owned?}
    
    Permission -->|No| Forbidden["ForbiddenError<br/>403"]
    Permission -->|Yes| Process["Process Request"]
    
    Process --> Success{Success?}
    Success -->|Yes| Return["SuccessResponse<br/>200/201"]
    Success -->|No| ServerErr["InternalServerError<br/>500"]
    
    AuthErr --> Middleware["Error Middleware"]
    ValErr --> Middleware
    NotFound --> Middleware
    Forbidden --> Middleware
    ServerErr --> Middleware
    
    Middleware --> Log["Log Error<br/>(Winston)"]
    Log --> Response["JSON Response<br/>+ statusCode + message"]
    Response --> Client["Return to Client"]
    Return --> Client
```

---

## Monitoring & Observability

```mermaid
graph TB
    subgraph Logs["Logging"]
        NodeLog["Node.js<br/>(Winston)<br/>→ logs/app-YYYY-MM-DD.log"]
        PyLog["Python<br/>(logging)<br/>→ stdout/stderr"]
    end
    
    subgraph Metrics["Metrics"]
        ReqCount["Request Count<br/>by endpoint"]
        LatencyP95["Latency P95<br/>(endpoint, method)"]
        ErrorRate["Error Rate<br/>by status code"]
    end
    
    subgraph Health["Health Checks"]
        NodeHealth["Node: GET /health"]
        PyHealth["Python: GET /"]
        MilvusHealth["Milvus: /healthz"]
        MongoHealth["MongoDB: ping"]
    end
    
    subgraph Alerts["Alerts"]
        ServiceDown["Service down<br/>(health check fails)"]
        ErrorRate10["Error rate > 10%<br/>(5xx errors)"]
        LatencyP95High["Latency P95 > 5s<br/>(slow endpoint)"]
    end
    
    Logs --> Metrics
    Health --> Alerts
    Metrics --> Alerts
```

---

## Technology Stack Summary

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | Next.js | 14.2.5 | SSR + App Router |
| | React | 18.2.0 | UI components |
| | Tailwind CSS | 3.3.2 | Styling |
| | TypeScript | 4.9.5 | Type safety |
| | TanStack React Query | 5.52.1 | State mgmt |
| **Backend API** | Express | 4.21.2 | HTTP framework |
| | TypeScript | 5.7.3 | Type safety |
| | Mongoose | 8.10.1 | MongoDB ODM |
| | JWT | 9.0.2 | Authentication (RS256) |
| | AWS SDK | v3 | S3 uploads |
| | Winston | 3.17.0 | Logging |
| **RAG Service** | FastAPI | 0.115.12 | Python async API |
| | BAAI/bge-m3 | 1.3.4 | Embeddings (1024-dim) |
| | pymilvus | 2.4.10 | Vector DB client |
| | rank-bm25 | 0.2.2 | Keyword search |
| | transformers | 4.51.3 | ML models |
| **Infrastructure** | Milvus | 2.3.3 | Vector database |
| | MongoDB | 5.0+ | Document store |
| | AWS S3 | - | File storage |
| | Docker | - | Containerization |
| | Docker Compose | - | Orchestration |

---

## Deployment Architecture (Production)

```mermaid
graph TB
    subgraph CloudInfra["Cloud Infrastructure"]
        ALB["Application Load Balancer"]
        K8S["Kubernetes Cluster"]
    end
    
    subgraph K8SPods["K8S Pods"]
        ClientPod["Client Pod<br/>Next.js x3"]
        APIPod["API Pod<br/>Express x5"]
        RAGPod["RAG Pod<br/>FastAPI x2"]
    end
    
    subgraph Managed["Managed Services"]
        MongoDB["MongoDB Atlas"]
        S3["AWS S3"]
        ECR["AWS ECR<br/>(Image Registry)"]
    end
    
    subgraph VectorDB["Vector Database"]
        MilvusCluster["Milvus Cluster<br/>(HA mode)"]
    end
    
    subgraph Monitoring["Observability"]
        Prometheus["Prometheus<br/>(Metrics)"]
        Grafana["Grafana<br/>(Dashboards)"]
        CloudWatch["CloudWatch<br/>(Logs)"]
    end
    
    Users["Users<br/>(HTTPS)"] --> ALB
    ALB --> K8S
    K8S --> K8SPods
    
    ClientPod --> APIPod
    APIPod --> MongoDB
    APIPod --> S3
    APIPod --> RAGPod
    RAGPod --> MilvusCluster
    
    ECR -.->|Pull images| K8SPods
    
    K8SPods -.->|Metrics| Prometheus
    Prometheus -.-> Grafana
    K8SPods -.->|Logs| CloudWatch
```

Currently deployed on **Docker Compose (single-machine)**. See [deployment-guide.md](./deployment-guide.md) for setup instructions.
