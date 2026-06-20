# Code Standards & Conventions

This document specifies coding standards, file organization, and error handling patterns across all services.

## Global Standards

### Language & Type Safety
- **TypeScript (TS):** Strict mode enabled (`strict: true` in tsconfig.json)
- **Python:** Type hints preferred (PEP 484); use `typing` module
- **Comments:** Explain *why*, not *what*; code is self-documenting
- **Naming:** camelCase (JS/TS), snake_case (Python), kebab-case (filenames)

### Version Control
- **Commit format:** Conventional Commits (feat, fix, docs, test, chore, refactor)
- **Branches:** feature/{name}, bugfix/{name}, docs/{name}
- **Pull requests:** Require code review for main; test on feature branches

### Code Review Checklist
- [ ] TypeScript strict + no `any` (without justification comment)
- [ ] Error handling (no unhandled rejections, try/catch for async)
- [ ] No hardcoded secrets, API keys, or credentials
- [ ] Tests pass (where applicable)
- [ ] Linting + formatting pass
- [ ] Documentation updated if API or behavior changed

---

## Frontend (`client/`)

### File Organization

```
client/app/
├── (auth)/
│   ├── login/
│   │   ├── page.tsx       # Route component
│   │   └── layout.tsx     # Auth layout
│   └── register/
│       └── page.tsx
├── (root)/
│   ├── page.tsx
│   ├── create/page.tsx
│   ├── workspace/[slug]/page.tsx
│   └── layout.tsx
├── components/
│   ├── ui/                # shadcn/ui primitives (Button, Input, etc.)
│   ├── layouts/
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── ProfileDropdown.tsx
│   ├── shared/
│   │   ├── ChatBubble.tsx
│   │   ├── PromptInput.tsx
│   │   └── SourceDocuments.tsx
│   ├── modals/
│   │   ├── UploadModal.tsx
│   │   └── ReEmbedDialog.tsx
│   └── workspaces/
│       └── WorkspaceSelector.tsx
├── hooks/
│   ├── useAuth.ts         # ⚠️ Duplicate: also in context/
│   └── use*.ts
├── context/
│   ├── AuthContext.tsx    # ⚠️ Contains useAuth (duplicates hooks/)
│   └── *.tsx
├── providers/
│   ├── AuthProvider.tsx
│   ├── ThemeProvider.tsx
│   ├── ProtectedProvider.tsx
│   └── index.tsx
├── types/
│   ├── index.ts           # Re-export all types
│   ├── auth.ts
│   ├── workspace.ts
│   └── api.ts
├── utils/
│   ├── axios.ts           # Axios instance + interceptor
│   ├── api.ts             # API client functions
│   └── *.ts
└── styles/
    ├── globals.css        # Tailwind imports, HSL tokens
    └── *.css
```

### TypeScript Patterns

**Strict Mode Config:**
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

**Naming Conventions:**
- Components: PascalCase (`ChatBubble.tsx`)
- Hooks: camelCase prefixed `use` (`useAuth.ts`, `useWorkspace.ts`)
- Types: PascalCase (`User`, `Workspace`, `Message`)
- Files: kebab-case for non-components, PascalCase for components
- Constants: UPPER_SNAKE_CASE (`API_BASE_URL`, `MAX_FILE_SIZE`)

**Type Definitions:**
```typescript
// types/auth.ts
export interface User {
  id: string;
  email: string;
  createdAt: Date;
}

export interface AuthToken {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export type AuthStatus = 'idle' | 'pending' | 'authenticated' | 'failed';
```

**Component Pattern:**
```typescript
// components/shared/ChatBubble.tsx
import React from 'react';

interface ChatBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  sourceDocuments?: Document[];
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({
  role,
  content,
  sourceDocuments,
}) => {
  // Implementation
  return <div>...</div>;
};
```

**Hook Pattern:**
```typescript
// hooks/useAuth.ts
import { useContext } from 'react';
import { AuthContext } from '@/context/AuthContext';

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

**API Client:**
```typescript
// utils/api.ts
import { axiosInstance } from './axios';

export const authAPI = {
  login: (email: string, password: string) =>
    axiosInstance.post('/auth/login', { email, password }),
  register: (email: string, password: string) =>
    axiosInstance.post('/auth/register', { email, password }),
};

export const workspaceAPI = {
  list: () => axiosInstance.get('/files/workspaces'),
  query: (slug: string, query: string, history: string[]) =>
    axiosInstance.post(`/files/workspace/${slug}/query`, {
      query,
      history,
    }),
};
```

### Styling

**Tailwind Configuration:**
```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        // Define HSL tokens for light/dark mode
        primary: 'hsl(var(--color-primary))',
        secondary: 'hsl(var(--color-secondary))',
      },
    },
  },
};
```

**CSS Variables (globals.css):**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --color-primary: 213 95% 56%; /* Blue */
    --color-secondary: 263 80% 50%; /* Purple */
    --color-background: 0 0% 100%; /* White */
    --color-foreground: 213 13% 23%; /* Dark gray */
  }

  [data-theme='dark'] {
    --color-primary: 213 95% 56%;
    --color-secondary: 263 80% 50%;
    --color-background: 213 13% 23%;
    --color-foreground: 0 0% 100%;
  }
}
```

### Form Validation

**Zod + React Hook Form Pattern:**
```typescript
// components/shared/LoginForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const loginSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Min 8 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export const LoginForm = () => {
  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    // Handle submit
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} />
      {errors.email && <p>{errors.email.message}</p>}
    </form>
  );
};
```

---

## Backend API (`node-server/`)

### File Organization

```
src/
├── index.ts                    # Entry point
├── core/
│   ├── error.response.ts       # Error hierarchy
│   ├── success.response.ts     # Success response wrapper
│   └── JWT.ts                  # JWT config
├── controllers/
│   ├── auth.controller.ts
│   └── files.controller.ts
├── routes/
│   ├── auth.route.ts
│   ├── files.route.ts
│   └── index.ts
├── services/
│   ├── auth.service.ts
│   ├── files.service.ts
│   ├── encryption.service.ts
│   └── key-store.service.ts
├── models/
│   ├── User.ts
│   ├── Workspace.ts
│   ├── Message.ts
│   └── Keystore.ts
├── repositories/
│   ├── workspace.repo.ts
│   └── *.repo.ts
├── middlewares/
│   ├── errorHandler.middleware.ts
│   ├── authentication.ts
│   ├── multer.middleware.ts
│   └── logging.ts
├── utils/
│   ├── jwt.ts
│   ├── auth.util.ts
│   ├── encryption.util.ts
│   ├── s3.ts
│   └── bcrypt.ts
├── helpers/
│   └── catchAsync.ts
└── config/
    └── *.ts
```

### TypeScript Patterns

**Error Class Hierarchy:**
```typescript
// core/error.response.ts
export class BaseError extends Error {
  constructor(
    public statusCode: number,
    public message: string,
    public isOperational = true
  ) {
    super(message);
    Object.setPrototypeOf(this, BaseError.prototype);
  }
}

export class NotFoundError extends BaseError {
  constructor(message = 'Not found') {
    super(404, message);
    Object.setPrototypeOf(this, NotFoundError.prototype);
  }
}

export class BadRequestError extends BaseError {
  constructor(message = 'Bad request') {
    super(400, message);
    Object.setPrototypeOf(this, BadRequestError.prototype);
  }
}

export class UnauthorizedError extends BaseError {
  constructor(message = 'Unauthorized') {
    super(401, message);
    Object.setPrototypeOf(this, UnauthorizedError.prototype);
  }
}
```

**Success Response Wrapper:**
```typescript
// core/success.response.ts
export class SuccessResponse {
  constructor(
    public data: any,
    public message: string = 'Success',
    public statusCode: number = 200
  ) {}

  send = (res: Response) => {
    res.status(this.statusCode).json({
      statusCode: this.statusCode,
      message: this.message,
      data: this.data,
    });
  };
}
```

**Async Error Wrapper:**
```typescript
// helpers/catchAsync.ts
const catchAsync = (fn: Function) => {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};
```

**Service Pattern:**
```typescript
// services/auth.service.ts
export class AuthService {
  async register(email: string, password: string) {
    const existing = await User.findOne({ email });
    if (existing) {
      throw new ConflictError('Email already registered');
    }

    const hashedPassword = await bcrypt.hash(password, 12);
    const user = await User.create({ email, password: hashedPassword });

    return { userId: user._id };
  }

  async login(email: string, password: string) {
    const user = await User.findOne({ email });
    if (!user) {
      throw new UnauthorizedError('Invalid credentials');
    }

    const isValid = await bcrypt.compare(password, user.password);
    if (!isValid) {
      throw new UnauthorizedError('Invalid credentials');
    }

    return { userId: user._id };
  }
}
```

**Controller Pattern:**
```typescript
// controllers/auth.controller.ts
import { SuccessResponse } from '@/core/success.response';

export class AuthController {
  private authService = new AuthService();

  register = async (req: Request, res: Response) => {
    const { email, password } = req.body;
    const result = await this.authService.register(email, password);
    new SuccessResponse(result, 'User registered', 201).send(res);
  };

  login = async (req: Request, res: Response) => {
    const { email, password } = req.body;
    const result = await this.authService.login(email, password);
    new SuccessResponse(result, 'Login successful').send(res);
  };
}
```

**Route Pattern:**
```typescript
// routes/auth.route.ts
export const authRouter = (router: Router) => {
  const controller = new AuthController();

  router.use('/auth', router);

  // Public
  router.post('/register', catchAsync(controller.register));
  router.post('/login', catchAsync(controller.login));

  // Protected
  router.use(authentication);
  router.post('/logout', catchAsync(controller.logout));
};
```

### Naming Conventions
- **Files:** kebab-case (`auth-service.ts`, `error-handler.ts`)
- **Classes:** PascalCase (`AuthService`, `UserRepository`)
- **Functions:** camelCase (`createUser()`, `getUserById()`)
- **Constants:** UPPER_SNAKE_CASE (`DB_URL`, `JWT_EXPIRY`)
- **Interfaces:** PascalCase (`IUser`, `IWorkspace`) or without `I` prefix

### Error Handling

**Response Middleware:**
```typescript
// middlewares/errorHandler.middleware.ts
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  if (err instanceof BaseError) {
    return res.status(err.statusCode).json({
      statusCode: err.statusCode,
      message: err.message,
      data: null,
    });
  }

  console.error(err);
  return res.status(500).json({
    statusCode: 500,
    message: 'Internal server error',
    data: null,
  });
});
```

**Usage:**
```typescript
// In service
if (!workspace) {
  throw new NotFoundError('Workspace not found');
}

// In controller
try {
  const data = await this.service.getData();
  new SuccessResponse(data).send(res);
} catch (error) {
  // catchAsync wrapper handles + error middleware catches
  throw error;
}
```

### Authentication & Authorization

**JWT Middleware:**
```typescript
// utils/auth.util.ts
export const authentication = (req: Request, res: Response, next: NextFunction) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) {
    throw new UnauthorizedError('No token provided');
  }

  try {
    const decoded = jwt.verify(token, publicKey);
    req.user = decoded;
    next();
  } catch (error) {
    throw new UnauthorizedError('Invalid token');
  }
};
```

**Usage:**
```typescript
// Apply to routes
router.use(authentication);
router.post('/protected-route', controller.protectedAction);
```

---

## RAG Service (`python-server/`)

### File Organization

```
app/
├── main.py                 # FastAPI entry point
├── core/
│   ├── config.yaml         # Settings
│   ├── file_loader.py      # PDF/DOCX/TXT loaders
│   ├── text_splitter.py    # Chunking logic
│   └── embedding.py        # Embedding model wrapper
├── services/
│   ├── rag_service.py      # Orchestrator
│   ├── milvus_store.py     # Vector DB
│   ├── bm25_index.py       # BM25 ranking
│   ├── reranker.py         # Cross-encoder
│   └── llm_chain.py        # LLM inference
├── evaluation/
│   ├── rag_evaluator.py    # Metrics
│   └── ground_truth/
├── utils/
│   └── *.py
└── __init__.py
```

### Python Conventions

**Type Hints:**
```python
# services/rag_service.py
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    collection_name: str
    history: List[str]

class Document(BaseModel):
    content: str
    metadata: Dict[str, str]
    score: float

class QueryResponse(BaseModel):
    docs: List[Document]
    response: str
    search_stats: Dict[str, int]
```

**Service Pattern:**
```python
# services/rag_service.py
class RAGService:
    def __init__(self, config_path: str = './config.yaml'):
        self.config = self._load_config(config_path)
        self.embedding_model = self._init_embedding()
        self.milvus_store = MilvusStore(self.config)
        self.bm25_index = BM25Index(self.config)
        self.reranker = Reranker(self.config)
        self.llm_chain = LLMChain(self.config)

    def embed_documents(
        self,
        file_paths: List[str],
        collection_name: str
    ) -> Dict[str, any]:
        """
        Embed documents into Milvus + build BM25 index.

        Args:
            file_paths: List of file paths to embed
            collection_name: Milvus collection name

        Returns:
            Dict with status, chunk count, error details
        """
        try:
            documents = self._load_files(file_paths)
            chunks = self._split_texts(documents)
            embeddings = self._embed_chunks(chunks)
            self.milvus_store.add_vectors(collection_name, embeddings)
            self.bm25_index.build(collection_name, chunks)
            return {'status': 'success', 'chunks': len(chunks)}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def query_documents(
        self,
        query: str,
        collection_name: str,
        history: Optional[List[str]] = None
    ) -> QueryResponse:
        """
        Execute RAG query: retrieve → rerank → LLM.
        """
        query_embedding = self.embedding_model.embed(query)
        
        # Hybrid retrieval
        dense_docs = self.milvus_store.search(
            collection_name, query_embedding, k=20
        )
        sparse_docs = self.bm25_index.search(query, k=20)
        
        # Fusion
        fused_docs = self._fuse_results(dense_docs, sparse_docs)
        
        # Re-rank
        reranked_docs = self.reranker.rank(query, fused_docs, top_k=5)
        
        # LLM inference
        prompt = self._build_prompt(query, reranked_docs, history)
        response = self.llm_chain.generate(prompt)
        
        return QueryResponse(
            docs=reranked_docs,
            response=response,
            search_stats={'dense_k': 20, 'sparse_k': 20, 'reranked_k': 5}
        )

    def _load_files(self, file_paths: List[str]) -> List[Document]:
        """Load PDF, DOCX, TXT files."""
        documents = []
        for path in file_paths:
            if path.endswith('.pdf'):
                documents.extend(PDFLoader(path).load())
            elif path.endswith('.docx'):
                documents.extend(DocxLoader(path).load())
            else:
                documents.extend(TextLoader(path).load())
        return documents

    def _split_texts(self, documents: List[Document]) -> List[Dict]:
        """Split documents into chunks."""
        splitter = SentenceSplitter(
            chunk_size=512,
            overlap=128
        )
        return splitter.split_documents(documents)

    def _embed_chunks(self, chunks: List[Dict]) -> List[Tuple[str, List[float]]]:
        """Embed text chunks."""
        texts = [c['content'] for c in chunks]
        embeddings = self.embedding_model.encode(texts, batch_size=32)
        return list(zip(texts, embeddings))
```

**Error Handling:**
```python
# main.py
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={'detail': str(exc)},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f'Unhandled exception: {exc}', exc_info=True)
    return JSONResponse(
        status_code=500,
        content={'detail': 'Internal server error'},
    )
```

**Config Loading:**
```python
# core/config.py
import yaml
from dataclasses import dataclass

@dataclass
class RAGConfig:
    chunk_size: int
    overlap: int
    embedding_model: str
    embedding_dim: int
    llm_endpoint: str
    milvus_uri: str

    @classmethod
    def load(cls, path: str = './config.yaml'):
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
```

### Naming Conventions
- **Files:** snake_case (`rag_service.py`, `milvus_store.py`)
- **Classes:** PascalCase (`RAGService`, `MilvusStore`)
- **Functions:** snake_case (`embed_documents()`, `query_documents()`)
- **Constants:** UPPER_SNAKE_CASE (`MAX_CHUNK_SIZE`, `EMBEDDING_DIM`)
- **Private:** Prefix with `_` (`_load_files()`, `_fuse_results()`)

---

## Shared Patterns

### Logging

- **Node:** Winston + `winston-daily-rotate-file` writes `logs/app-YYYY-MM-DD.log` (rotation 100 MB, 14 days), JSON format + timestamp, console transport in dev. Config in `node-server/src/configs/logger.ts`.
- **Python:** stdlib `logging` with `RotatingFileHandler` (`logs/app.log`, 100 MB, 14 backups), format `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.
- **Never log PII** — strip passwords, tokens, full emails before logging.

### Testing Approach

No test suites currently exist — adding them is on the roadmap. When introduced:

- **Frontend:** Jest + React Testing Library; co-locate as `components/__tests__/*.test.tsx`; render component, assert via `screen.getByText`.
- **Backend:** Jest + Supertest; place at `__tests__/*.test.ts`; spin up Express app, hit routes, assert status + payload.
- **Python:** pytest; fixtures per service (e.g. `rag_service`); use `tmp_path` for file-based tests; assert returned dict shape.

See [project-roadmap.md](./project-roadmap.md) for the testing rollout plan.

---

## Linting & Formatting

**Frontend (ESLint + Prettier):**
```bash
yarn lint           # Check style
yarn lint:fix       # Auto-fix
yarn format:check   # Check formatting
yarn format:write   # Auto-format
```

**Backend (ESLint + Prettier):**
```bash
yarn lint           # Check style
yarn lint:fix       # Auto-fix
yarn prettier       # Check formatting
yarn prettier:fix   # Auto-format
```

**Python (pylint + black):**
```bash
pylint app/        # Lint
black app/         # Format
```

---

## Security Checklist

- [ ] No hardcoded secrets (use env vars)
- [ ] SQL injection: Use parameterized queries (Mongoose auto-escapes)
- [ ] XSS: React auto-escapes; use DOMPurify if rendering HTML
- [ ] CSRF: Use CSRF tokens on state-changing routes
- [ ] Authentication: JWT RS256, 15-min access token, refresh token in httpOnly cookie (future)
- [ ] Authorization: Check resource ownership before returning
- [ ] Rate limiting: Apply to auth endpoints (configured but not used)
- [ ] Logging: Never log PII (passwords, tokens, emails)
- [ ] Dependencies: Keep up-to-date; run `npm audit` monthly

---

## Documentation Standards

- **README:** Quick start, setup, key endpoints
- **In-code comments:** Explain non-obvious logic
- **Type definitions:** Self-document via types instead of comments
- **API docs:** Swagger/OpenAPI (future enhancement)
- **Architecture:** Mermaid diagrams in separate doc file

See [system-architecture.md](./system-architecture.md) for diagrams.
