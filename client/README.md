# 🎨 Frontend - Next.js Application

Ứng dụng frontend được xây dựng với Next.js 14, sử dụng App Router và các công nghệ hiện đại để tạo ra giao diện người dùng đẹp và responsive cho hệ thống RAG Chat.

## 🛠️ Tech Stack

- **Framework**: Next.js 14 với App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI Primitives
- **State Management**: Tanstack Query (React Query)
- **Form Handling**: React Hook Form + Zod validation
- **Icons**: Lucide React
- **Theme**: Dark/Light mode với next-themes
- **HTTP Client**: Axios
- **File Upload**: React Dropzone

## 🏗️ Cấu trúc thư mục

```
client/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth group routes
│   │   ├── login/         # Trang đăng nhập
│   │   └── register/      # Trang đăng ký
│   ├── (root)/            # Main app routes
│   │   ├── create/        # Tạo workspace mới
│   │   ├── workspace/[slug]/ # Workspace chat
│   │   └── page.tsx       # Trang chủ
│   └── layout.tsx         # Root layout
│
├── components/            # React components
│   ├── layouts/          # Layout components
│   │   ├── Header.tsx    # App header
│   │   ├── Sidebar.tsx   # Navigation sidebar
│   │   └── nav-user.tsx  # User navigation
│   ├── modals/          # Modal dialogs
│   │   ├── UploadModal.tsx     # File upload modal
│   │   └── ReEmbedDialog.tsx   # Re-embed modal
│   ├── shared/          # Shared components
│   │   ├── ChatContainer.tsx        # Main chat interface
│   │   ├── ChatBubble.tsx          # Chat message bubble
│   │   ├── PromptInput.tsx         # Chat input
│   │   └── SourceDocumentsModal.tsx # Source docs modal
│   ├── ui/              # Base UI components (Radix UI)
│   └── workspaces/      # Workspace components
│
├── hooks/               # Custom React hooks
│   ├── useAuth.ts       # Authentication hook
│   ├── useFileUpload.ts # File upload hook
│   └── useWorkspaces.ts # Workspace management
│
├── utils/              # Utility functions
│   ├── axios.ts        # Axios configuration
│   └── index.ts        # General utilities
│
├── types/              # TypeScript type definitions
│   ├── index.ts        # Main types
│   └── nav.ts          # Navigation types
│
└── config/             # Configuration files
    ├── site.ts         # Site configuration
    └── global-config.ts # Global config
```

## 🚀 Bắt đầu

### Cài đặt dependencies

```bash
cd client
yarn install
```

### Chạy development server

```bash
yarn dev
```

Ứng dụng sẽ chạy tại [http://localhost:3000](http://localhost:3000)

### Build production

```bash
yarn build
yarn start
```

## 🔧 Scripts có sẵn

```bash
# Development
yarn dev              # Chạy dev server
yarn build            # Build production
yarn start            # Chạy production server

# Code Quality
yarn lint             # Chạy ESLint
yarn lint:fix         # Fix ESLint errors
yarn typecheck        # Type checking
yarn format:write     # Format code với Prettier
yarn format:check     # Check code formatting
```

## 🎨 UI Components

### Base Components (Radix UI)

Dự án sử dụng các components từ Radix UI đã được customize:

- `Button` - Buttons với variants khác nhau
- `Input` - Text inputs với validation
- `Dialog` - Modal dialogs
- `DropdownMenu` - Dropdown menus
- `Avatar` - User avatars
- `Badge` - Status badges
- `Card` - Container cards
- `Toast` - Notification toasts

### Custom Components

#### ChatContainer

```typescript
// Main chat interface component
<ChatContainer workspaceId={workspaceId} messages={messages} onSendMessage={handleSendMessage} />
```

#### FileUploader

```typescript
// File upload component với drag & drop
<FileUploader
  onUpload={handleFileUpload}
  accept=".pdf"
  maxSize={10 * 1024 * 1024} // 10MB
/>
```

#### UploadModal

```typescript
// Modal để upload files
<UploadModal isOpen={isUploadModalOpen} onClose={() => setIsUploadModalOpen(false)} workspaceId={workspaceId} />
```

## 🔐 Authentication

### Auth Context

```typescript
// Sử dụng AuthContext để quản lý trạng thái authentication
const { user, login, logout, isLoading } = useAuth()
```

### Protected Routes

```typescript
// Routes được bảo vệ bằng ProtectedProvider
<ProtectedProvider>
  <App />
</ProtectedProvider>
```

### Login Flow

1. User nhập credentials tại `/login`
2. Call API `/auth/login`
3. Lưu JWT tokens vào localStorage
4. Redirect đến dashboard

## 🌐 API Integration

### Axios Configuration

```typescript
// utils/axios.ts
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    "Content-Type": "application/json",
  },
})

// Auto attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

### API Calls

```typescript
// apis/auth.ts
export const authAPI = {
  login: (credentials: LoginRequest) => api.post("/auth/login", credentials),

  register: (data: RegisterRequest) => api.post("/auth/register", data),

  refreshToken: (refreshToken: string) => api.post("/auth/refresh", { refreshToken }),
}

// apis/files.ts
export const filesAPI = {
  upload: (file: File, workspaceId: string) => {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("workspaceId", workspaceId)

    return api.post("/files/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
  },

  getFiles: (workspaceId: string) => api.get(`/files?workspaceId=${workspaceId}`),
}
```

## 🎯 State Management

### React Query (TanStack Query)

```typescript
// hooks/useWorkspaces.ts
export const useWorkspaces = () => {
  return useQuery({
    queryKey: ["workspaces"],
    queryFn: () => workspacesAPI.getAll(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// hooks/useFileUpload.ts
export const useFileUpload = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: filesAPI.upload,
    onSuccess: () => {
      queryClient.invalidateQueries(["files"])
      toast.success("File uploaded successfully!")
    },
    onError: (error) => {
      toast.error("Upload failed: " + error.message)
    },
  })
}
```

## 🎨 Styling & Theming

### Tailwind CSS

Dự án sử dụng Tailwind CSS với custom configuration:

```javascript
// tailwind.config.js
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        // Custom color palette
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

### Dark/Light Mode

```typescript
// components/theme-toggle.tsx
import { useTheme } from "next-themes"

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  return (
    <Button variant="ghost" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
      {theme === "dark" ? <Sun /> : <Moon />}
    </Button>
  )
}
```

## 📱 Responsive Design

### Breakpoints

```css
/* Mobile first approach */
sm: '640px'   /* Tablet */
md: '768px'   /* Desktop */
lg: '1024px'  /* Large desktop */
xl: '1280px'  /* Extra large */
```

### Mobile Hook

```typescript
// hooks/use-mobile.tsx
export function useIsMobile() {
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkDevice = () => {
      setIsMobile(window.innerWidth < 768)
    }

    checkDevice()
    window.addEventListener("resize", checkDevice)

    return () => window.removeEventListener("resize", checkDevice)
  }, [])

  return isMobile
}
```

## 🔧 Environment Variables

```bash
# .env.local
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:3001/api
NODE_ENV=development
```

## 🧪 Testing

### Component Testing

```typescript
// __tests__/components/Button.test.tsx
import { render, screen } from "@testing-library/react"

import { Button } from "@/components/ui/button"

describe("Button", () => {
  it("renders button with text", () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText("Click me")).toBeInTheDocument()
  })
})
```

## 🚀 Deployment

### Docker Build

```dockerfile
# dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app

COPY --from=builder /app/next.config.mjs ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
CMD ["npm", "start"]
```

### Vercel Deployment

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

## 🐛 Debugging

### Development Tools

```typescript
// Enable React Query DevTools in development
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"

export default function App() {
  return (
    <>
      <YourApp />
      {process.env.NODE_ENV === "development" && <ReactQueryDevtools initialIsOpen={false} />}
    </>
  )
}
```

## 📚 Documentation

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Radix UI](https://www.radix-ui.com/docs)
- [React Query](https://tanstack.com/query/latest)

## 🤝 Contributing

1. Tạo feature branch từ `main`
2. Implement changes với proper TypeScript types
3. Add tests cho new components
4. Ensure code formatting với Prettier
5. Submit PR với clear description

---

💡 **Tips**: Sử dụng VSCode với các extensions: ES7+ React/Redux/React-Native snippets, Tailwind CSS IntelliSense, TypeScript Importer
