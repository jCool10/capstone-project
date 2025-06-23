# 🚀 Backend API - Node.js Server

Backend API được xây dựng với Express.js và TypeScript, cung cấp các API endpoints cho authentication, file management, và tích hợp với RAG service. Server sử dụng MongoDB làm database chính và AWS S3 để lưu trữ files.

## 🛠️ Tech Stack

- **Framework**: Express.js với TypeScript
- **Database**: MongoDB với Mongoose ODM
- **Authentication**: JWT (Access & Refresh tokens)
- **File Storage**: AWS S3 với Multer
- **Logging**: Winston với Daily Rotate File
- **Security**: Helmet, CORS, Rate Limiting
- **Validation**: Custom middlewares
- **Development**: Nodemon, ESLint, Prettier

## 🏗️ Cấu trúc thư mục

```
node-server/
├── src/
│   ├── configs/              # Cấu hình
│   │   ├── express.config.ts    # Express app configuration
│   │   ├── mongoose.config.ts   # MongoDB connection
│   │   ├── logger.config.ts     # Winston logger setup
│   │   └── s3.config.ts         # AWS S3 configuration
│   │
│   ├── controllers/          # Route controllers
│   │   ├── auth.controller.ts   # Authentication logic
│   │   └── files.controller.ts  # File management logic
│   │
│   ├── core/                # Core utilities
│   │   ├── error.response.ts    # Error response handler
│   │   ├── success.response.ts  # Success response handler
│   │   └── JWT.ts              # JWT token utilities
│   │
│   ├── helpers/             # Helper functions
│   │   └── cathAsync.ts       # Async error catcher
│   │
│   ├── middlewares/         # Express middlewares
│   │   ├── errorHandler.middleware.ts # Global error handler
│   │   └── multer.middleware.ts       # File upload middleware
│   │
│   ├── models/              # MongoDB schemas
│   │   ├── user.model.ts        # User schema
│   │   ├── workspace.model.ts   # Workspace schema
│   │   ├── message.model.ts     # Chat message schema
│   │   ├── apiKey.model.ts      # API key schema
│   │   ├── keyStore.model.ts    # Key store schema
│   │   └── userKeyPair.model.ts # User key pair schema
│   │
│   ├── repositories/        # Data access layer
│   │   ├── user.repo.ts         # User repository
│   │   ├── worksapce.repo.ts    # Workspace repository
│   │   ├── message.repo.ts      # Message repository
│   │   └── keystore.repo.ts     # Keystore repository
│   │
│   ├── routes/              # API routes
│   │   ├── index.ts            # Main router
│   │   ├── auth.route.ts       # Authentication routes
│   │   └── files.route.ts      # File management routes
│   │
│   ├── services/            # Business logic layer
│   │   ├── auth.service.ts      # Authentication service
│   │   ├── files.service.ts     # File management service
│   │   ├── encryption.service.ts # Encryption utilities
│   │   ├── firebase.service.ts   # Firebase integration
│   │   └── keyStore,service.ts   # Key store service
│   │
│   ├── utils/               # Utility functions
│   │   ├── bcrypt.ts           # Password hashing
│   │   ├── jwt.ts              # JWT utilities
│   │   ├── s3.ts               # S3 operations
│   │   ├── auth.util.ts        # Auth utilities
│   │   └── encryption.util.ts   # Encryption utilities
│   │
│   ├── index.ts             # Application entry point
│   └── type.d.ts            # TypeScript type definitions
│
├── uploads/                 # Local file uploads (development)
├── logs/                   # Application logs
├── dockerfile              # Docker configuration
├── nodemon.json           # Nodemon configuration
├── tsconfig.json          # TypeScript configuration
└── package.json           # Dependencies and scripts
```

## 🚀 Bắt đầu

### Yêu cầu hệ thống

- Node.js 18+
- MongoDB 6.0+
- AWS S3 Account (cho production)
- TypeScript knowledge

### Cài đặt dependencies

```bash
cd node-server
yarn install
```

### Cấu hình Environment Variables

Tạo file `.env` trong thư mục `node-server`:

```bash
# Database
DB_URL=mongodb://localhost:27017/capstone-db

# JWT Configuration
ACCESS_TOKEN_VALIDITY_SEC=3600          # 1 hour
REFRESH_TOKEN_VALIDITY_SEC=604800       # 7 days
JWT_SECRET=your-super-secret-jwt-key
REFRESH_JWT_SECRET=your-refresh-secret-key

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=ap-southeast-1
AWS_BUCKET=your-s3-bucket-name

# Server Configuration
NODE_ENV=development
PORT=3000

# External Services
PYTHON_RAG_SERVICE_URL=http://localhost:8080

# Firebase (Optional)
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_PRIVATE_KEY=your-firebase-private-key
FIREBASE_CLIENT_EMAIL=your-firebase-client-email
```

### Chạy ở chế độ development

```bash
yarn dev
```

Server sẽ chạy tại: http://localhost:3000

### Build và chạy production

```bash
yarn build
yarn start
```

## 🔧 Scripts có sẵn

```bash
# Development
yarn dev              # Chạy với nodemon (hot reload)
yarn build            # Build TypeScript to JavaScript
yarn start            # Chạy production build

# Code Quality
yarn lint             # Chạy ESLint
yarn lint:fix         # Fix ESLint errors tự động
yarn prettier         # Check code formatting
yarn prettier:fix     # Format code với Prettier
```

## 📊 API Endpoints

### Authentication Endpoints

#### POST /api/auth/register

Đăng ký tài khoản mới

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "fullName": "Nguyễn Văn A"
}
```

**Response:**

```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user": {
      "id": "user_id",
      "email": "user@example.com",
      "fullName": "Nguyễn Văn A"
    },
    "tokens": {
      "accessToken": "jwt_access_token",
      "refreshToken": "jwt_refresh_token"
    }
  }
}
```

#### POST /api/auth/login

Đăng nhập

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```

#### POST /api/auth/refresh

Refresh access token

**Request Body:**

```json
{
  "refreshToken": "jwt_refresh_token"
}
```

#### POST /api/auth/logout

Đăng xuất (invalidate tokens)

**Headers:**

```
Authorization: Bearer jwt_access_token
```

### File Management Endpoints

#### POST /api/files/upload

Upload PDF file

**Headers:**

```
Authorization: Bearer jwt_access_token
Content-Type: multipart/form-data
```

**Request Body (FormData):**

```
file: PDF file
workspaceId: workspace_id (optional)
```

**Response:**

```json
{
  "success": true,
  "message": "File uploaded successfully",
  "data": {
    "fileId": "file_id",
    "fileName": "document.pdf",
    "fileSize": 1024000,
    "s3Url": "https://bucket.s3.region.amazonaws.com/path/to/file.pdf",
    "uploadedAt": "2024-01-01T00:00:00.000Z"
  }
}
```

#### GET /api/files

Lấy danh sách files của user

**Headers:**

```
Authorization: Bearer jwt_access_token
```

**Query Parameters:**

```
workspaceId: workspace_id (optional)
page: 1 (optional, default: 1)
limit: 10 (optional, default: 10)
```

#### DELETE /api/files/:fileId

Xóa file

**Headers:**

```
Authorization: Bearer jwt_access_token
```

### Workspace Endpoints

#### POST /api/workspaces

Tạo workspace mới

#### GET /api/workspaces

Lấy danh sách workspaces

#### GET /api/workspaces/:workspaceId/messages

Lấy lịch sử chat

## 🏗️ Kiến trúc ứng dụng

### Repository Pattern

```typescript
// repositories/user.repo.ts
export class UserRepository {
  static async findByEmail(email: string): Promise<IUser | null> {
    return await UserModel.findOne({ email }).lean()
  }

  static async create(userData: CreateUserInput): Promise<IUser> {
    const user = new UserModel(userData)
    return await user.save()
  }

  static async updateById(userId: string, updateData: UpdateUserInput): Promise<IUser | null> {
    return await UserModel.findByIdAndUpdate(userId, updateData, { new: true }).lean()
  }
}
```

### Service Layer

```typescript
// services/auth.service.ts
export class AuthService {
  static async register(userData: RegisterInput): Promise<AuthResponse> {
    // 1. Validate input
    const existingUser = await UserRepository.findByEmail(userData.email)
    if (existingUser) {
      throw new BadRequestError('Email already exists')
    }

    // 2. Hash password
    const hashedPassword = await bcrypt.hash(userData.password, 12)

    // 3. Create user
    const user = await UserRepository.create({
      ...userData,
      password: hashedPassword
    })

    // 4. Generate tokens
    const tokens = await JWTService.generateTokenPair(user.id, user.email)

    // 5. Save refresh token
    await KeyStoreService.createKeyStore(user.id, tokens.refreshToken)

    return {
      user: {
        id: user.id,
        email: user.email,
        fullName: user.fullName
      },
      tokens
    }
  }
}
```

### Middleware Pattern

```typescript
// middlewares/auth.middleware.ts
export const authenticateToken = catchAsync(async (req: AuthRequest, res: Response, next: NextFunction) => {
  // 1. Get token from header
  const authHeader = req.headers.authorization
  const token = authHeader && authHeader.split(' ')[1]

  if (!token) {
    throw new UnauthorizedError('Access token required')
  }

  // 2. Verify token
  const decoded = jwt.verify(token, process.env.JWT_SECRET!) as JwtPayload

  // 3. Get user info
  const user = await UserRepository.findById(decoded.userId)
  if (!user) {
    throw new UnauthorizedError('User not found')
  }

  // 4. Attach user to request
  req.user = user
  next()
})
```

## 🔐 Security Features

### Authentication & Authorization

- **JWT Tokens**: Access token (1 hour) + Refresh token (7 days)
- **Password Hashing**: Bcrypt với salt rounds = 12
- **Token Blacklisting**: Invalid tokens lưu trong Redis
- **Role-based Access**: Admin, User roles

### Security Middlewares

```typescript
// configs/express.config.ts
app.use(helmet()) // Security headers
app.use(cors(corsOptions)) // CORS configuration
app.use(compression()) // Gzip compression
app.use(morgan('combined')) // Request logging

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Max 100 requests per window
  message: 'Too many requests from this IP'
})
app.use(limiter)
```

### Input Validation

```typescript
// utils/validation.ts
export const registerSchema = {
  email: {
    isEmail: {
      errorMessage: 'Invalid email format'
    }
  },
  password: {
    isLength: {
      options: { min: 6 },
      errorMessage: 'Password must be at least 6 characters'
    }
  },
  fullName: {
    notEmpty: {
      errorMessage: 'Full name is required'
    }
  }
}
```

## 📁 File Upload System

### AWS S3 Integration

```typescript
// configs/s3.config.ts
export const s3Client = new S3Client({
  region: process.env.AWS_REGION!,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!
  }
})

// utils/s3.ts
export class S3Service {
  static async uploadFile(file: Express.Multer.File, key: string): Promise<string> {
    const uploadParams = {
      Bucket: process.env.AWS_BUCKET!,
      Key: key,
      Body: file.buffer,
      ContentType: file.mimetype
    }

    const result = await s3Client.send(new PutObjectCommand(uploadParams))
    return `https://${process.env.AWS_BUCKET}.s3.${process.env.AWS_REGION}.amazonaws.com/${key}`
  }

  static async deleteFile(key: string): Promise<void> {
    const deleteParams = {
      Bucket: process.env.AWS_BUCKET!,
      Key: key
    }

    await s3Client.send(new DeleteObjectCommand(deleteParams))
  }
}
```

### Multer Configuration

```typescript
// middlewares/multer.middleware.ts
export const uploadMiddleware = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB limit
  },
  fileFilter: (req, file, cb) => {
    if (file.mimetype === 'application/pdf') {
      cb(null, true)
    } else {
      cb(new Error('Only PDF files are allowed'))
    }
  }
})
```

## 📝 Logging System

### Winston Configuration

```typescript
// configs/logger.config.ts
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    // Console transport for development
    new winston.transports.Console({
      format: winston.format.simple()
    }),

    // File transport with rotation
    new winston.transports.DailyRotateFile({
      filename: 'logs/application-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      maxSize: '20m',
      maxFiles: '14d'
    }),

    // Error log file
    new winston.transports.DailyRotateFile({
      filename: 'logs/error-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      level: 'error',
      maxSize: '20m',
      maxFiles: '30d'
    })
  ]
})
```

## 🔄 Integration với Python RAG Service

### RAG Service Client

```typescript
// services/rag.service.ts
export class RAGService {
  private static readonly RAG_BASE_URL = process.env.PYTHON_RAG_SERVICE_URL

  static async processQuery(query: string, workspaceId: string): Promise<RAGResponse> {
    try {
      const response = await axios.post(`${this.RAG_BASE_URL}/chat`, {
        query,
        workspace_id: workspaceId
      })

      return response.data
    } catch (error) {
      logger.error('RAG service error:', error)
      throw new ServiceUnavailableError('RAG service is unavailable')
    }
  }

  static async embedDocuments(fileIds: string[], workspaceId: string): Promise<void> {
    try {
      await axios.post(`${this.RAG_BASE_URL}/embed`, {
        file_ids: fileIds,
        workspace_id: workspaceId
      })
    } catch (error) {
      logger.error('Document embedding error:', error)
      throw new ServiceUnavailableError('Failed to embed documents')
    }
  }
}
```

## 🧪 Testing

### Unit Tests

```typescript
// __tests__/services/auth.service.test.ts
describe('AuthService', () => {
  describe('register', () => {
    it('should register new user successfully', async () => {
      const userData = {
        email: 'test@example.com',
        password: 'password123',
        fullName: 'Test User'
      }

      const result = await AuthService.register(userData)

      expect(result.user.email).toBe(userData.email)
      expect(result.tokens.accessToken).toBeDefined()
      expect(result.tokens.refreshToken).toBeDefined()
    })

    it('should throw error for existing email', async () => {
      // Test implementation
    })
  })
})
```

### Integration Tests

```bash
# Chạy tests
yarn test
yarn test:watch
yarn test:coverage
```

## 🐳 Docker Support

### Dockerfile

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN yarn install --frozen-lockfile

COPY . .
RUN yarn build

FROM node:18-alpine AS runner

WORKDIR /app
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nodeuser

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

USER nodeuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

CMD ["node", "dist/index.js"]
```

## 📊 Monitoring & Health Checks

### Health Check Endpoint

```typescript
// routes/health.route.ts
router.get('/health', (req: Request, res: Response) => {
  res.status(200).json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV,
    version: process.env.npm_package_version
  })
})
```

### Error Monitoring

```typescript
// middlewares/errorHandler.middleware.ts
export const errorHandler = (error: Error, req: Request, res: Response, next: NextFunction) => {
  logger.error('Unhandled error:', {
    error: error.message,
    stack: error.stack,
    url: req.url,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  })

  if (error instanceof CustomError) {
    return res.status(error.statusCode).json({
      success: false,
      message: error.message,
      ...(process.env.NODE_ENV === 'development' && { stack: error.stack })
    })
  }

  res.status(500).json({
    success: false,
    message: 'Internal server error'
  })
}
```

## 🚀 Deployment

### Production Environment

```bash
# Build và deploy
yarn build
PM2_HOME=/opt/pm2 pm2 start dist/index.js --name "capstone-api"

# Với Docker
docker build -t capstone-api .
docker run -d -p 3000:3000 --env-file .env capstone-api
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'yarn'

      - name: Install dependencies
        run: yarn install --frozen-lockfile

      - name: Run tests
        run: yarn test

      - name: Build application
        run: yarn build

      - name: Deploy to server
        run: |
          # Deploy script here
```

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch: `git checkout -b feature/new-feature`
3. Follow TypeScript và ESLint rules
4. Write tests cho new features
5. Update documentation nếu cần
6. Submit pull request

---

📚 **Documentation Links:**

- [Express.js Guide](https://expressjs.com/)
- [MongoDB with Mongoose](https://mongoosejs.com/)
- [JWT Best Practices](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)
- [AWS S3 SDK](https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/)
