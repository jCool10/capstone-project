# Design Guidelines

## Overview

This document specifies the frontend design system, component patterns, and visual consistency rules for the capstone project. All UI text is currently in Vietnamese; future internationalization should follow these principles.

---

## Design System Foundation

### Color Palette

**Semantic Colors (HSL variables):**

```css
:root {
  /* Primary */
  --color-primary: 213 95% 56%;        /* Blue #0D8FFF */
  --color-primary-dark: 213 95% 40%;   /* Dark Blue */
  --color-primary-light: 213 95% 70%;  /* Light Blue */
  
  /* Secondary */
  --color-secondary: 263 80% 50%;      /* Purple #8B5CF6 */
  --color-secondary-dark: 263 80% 35%;
  --color-secondary-light: 263 80% 65%;
  
  /* Neutral */
  --color-background: 0 0% 100%;       /* White */
  --color-foreground: 213 13% 23%;     /* Dark Gray #2D3748 */
  --color-muted: 210 16% 82%;          /* Light Gray #CBD5E0 */
  --color-muted-foreground: 213 13% 45%;
  
  /* Status */
  --color-success: 142 71% 45%;        /* Green #22C55E */
  --color-warning: 38 92% 50%;         /* Amber #FCD34D */
  --color-destructive: 0 84% 60%;      /* Red #EF4444 */
  --color-info: 213 95% 56%;           /* Blue (same as primary) */
  
  /* Interactive */
  --color-link: 213 95% 56%;           /* Primary blue */
  --color-focus: 263 80% 50%;          /* Purple highlight */
  --color-border: 210 16% 82%;         /* Muted */
}

/* Dark Mode */
[data-theme='dark'] {
  --color-background: 213 13% 23%;     /* Dark Gray */
  --color-foreground: 0 0% 100%;       /* White */
  --color-muted: 213 12% 35%;          /* Dark Muted */
  --color-muted-foreground: 210 16% 82%;
  --color-border: 213 12% 35%;
  
  /* Colors remain same for accessibility contrast */
}
```

### Typography

**Font Stack:**
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
```

**Scale (Tailwind):**
- `text-xs` (12px): Labels, badges, hints
- `text-sm` (14px): Input text, secondary text
- `text-base` (16px): Body text, normal paragraphs
- `text-lg` (18px): Subheadings
- `text-xl` (20px): Section headings
- `text-2xl` (24px): Page headings
- `text-3xl` (30px): Hero headings

**Weight:**
- Regular (400): Body text, inputs
- Medium (500): Labels, buttons
- Semibold (600): Subheadings
- Bold (700): Headings

**Line Height:**
- Compact: 1.2 (headings)
- Normal: 1.5 (body)
- Relaxed: 1.75 (large text blocks)

### Spacing

**Scale (Tailwind):**
```
4px (p-1), 8px (p-2), 12px (p-3), 16px (p-4), 
20px (p-5), 24px (p-6), 32px (p-8), 40px (p-10)
```

**Rules:**
- Horizontal padding: 16px (desktop), 12px (tablet)
- Vertical padding: 12px (compact), 16px (comfortable)
- Grid gap: 16px (default), 24px (spacious)
- Margin between sections: 32px

### Rounded Corners

```css
border-radius: 4px   (sm: input borders, badges)
border-radius: 8px   (md: cards, modals)
border-radius: 12px  (lg: large containers)
border-radius: 50%   (full: avatars, buttons)
```

### Shadows

```css
box-shadow: 0 1px 2px rgba(0,0,0,0.05)        (sm)
box-shadow: 0 4px 6px rgba(0,0,0,0.10)        (md: cards, dropdowns)
box-shadow: 0 10px 15px rgba(0,0,0,0.15)      (lg: modals, popovers)
box-shadow: 0 20px 25px rgba(0,0,0,0.20)      (xl: z-index elevation)
```

---

## Component Library (shadcn/ui)

### Available Components

All components are from Radix UI + shadcn/ui customization:

| Component | Use Case | Notes |
|-----------|----------|-------|
| **Button** | Actions, CTAs | Variants: primary, secondary, outline, ghost, destructive |
| **Input** | Text fields, search | With validation error states |
| **Label** | Form labels | Associates with inputs via `htmlFor` |
| **Checkbox** | Yes/no options | Multiple selection |
| **Select** | Dropdowns | Multi-select via Radix Select |
| **Dialog** | Modals | Focused, dismissible with Escape |
| **Tooltip** | Hints | Hover-triggered, delay 200ms |
| **Tabs** | Tabbed content | Keyboard navigation (arrow keys) |
| **Separator** | Visual dividers | Vertical or horizontal |
| **ScrollArea** | Scrollable containers | Custom scrollbar styling |
| **Avatar** | User profiles | Fallback to initials |
| **Toast** | Notifications | Dismiss auto after 3s |
| **Dropdown Menu** | Context menus | Click to open, click outside to close |

### Button Variants

```tsx
// Primary (CTA)
<Button className="bg-primary text-white">
  Send Query
</Button>

// Secondary (Alternative)
<Button variant="secondary">
  Cancel
</Button>

// Outline (Tertiary)
<Button variant="outline">
  Learn More
</Button>

// Ghost (Minimal)
<Button variant="ghost" size="sm">
  Skip
</Button>

// Destructive (Danger)
<Button variant="destructive">
  Delete Workspace
</Button>

// Disabled
<Button disabled>
  Processing...
</Button>
```

### Form Patterns

**Zod + React Hook Form:**

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const schema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Min 8 chars'),
  remember: z.boolean().optional(),
});

type FormData = z.infer<typeof schema>;

export const LoginForm = () => {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    // Handle login
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input
          {...register('email')}
          id="email"
          type="email"
          placeholder="name@example.com"
        />
        {errors.email && (
          <p className="text-sm text-destructive">{errors.email.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <Input
          {...register('password')}
          id="password"
          type="password"
          placeholder="••••••••"
        />
        {errors.password && (
          <p className="text-sm text-destructive">{errors.password.message}</p>
        )}
      </div>

      <Button type="submit" className="w-full">
        Sign In
      </Button>
    </form>
  );
};
```

---

## Layout Patterns

### Header

**Sticky header with:**
- Logo/brand (left)
- Navigation links (center, on desktop)
- User profile dropdown (right)
- Dark mode toggle (right)

```tsx
export const Header = () => {
  const { user } = useAuth();

  return (
    <header className="sticky top-0 z-40 border-b bg-background">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <div className="text-xl font-bold">RAG Chat</div>
        <nav className="hidden md:flex gap-6">
          <a href="/">Home</a>
          <a href="/create">New Chat</a>
        </nav>
        <div className="flex items-center gap-4">
          <ThemeToggle />
          {user && <ProfileDropdown />}
        </div>
      </div>
    </header>
  );
};
```

### Sidebar

**Left sidebar (on protected routes):**
- Workspace switcher (dropdown)
- Quick actions (New Chat button)
- Workspace navigation (links)
- Collapsible on mobile (hamburger menu)

```tsx
export const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Mobile toggle */}
      <button
        className="md:hidden fixed top-4 left-4 z-50"
        onClick={() => setIsOpen(!isOpen)}
      >
        ☰
      </button>

      {/* Sidebar */}
      <aside
        className={`${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } fixed md:relative md:translate-x-0 transition-transform w-60 h-screen border-r bg-muted p-4 md:p-6`}
      >
        <div className="space-y-6">
          <WorkspaceSelector />
          <Button className="w-full">+ New Chat</Button>
          <nav className="space-y-2">
            {/* Navigation items */}
          </nav>
        </div>
      </aside>
    </>
  );
};
```

### Chat Interface

**Main content area with:**
- Message list (scrollable)
- Input prompt box (sticky at bottom)
- Source documents (toggleable sidebar on desktop)

```tsx
export const ChatInterface = ({ workspaceSlug }: { workspaceSlug: string }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    // Call API to query
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <ChatBubble key={msg.id} {...msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <PromptInput
        value={input}
        onChange={setInput}
        onSend={handleSend}
        disabled={/* loading state */}
      />
    </div>
  );
};
```

---

## Component Patterns

### ChatBubble

**Props:**
```typescript
interface ChatBubbleProps {
  role: 'user' | 'assistant';      // Message sender
  content: string;                   // Message text
  sourceDocuments?: SourceDoc[];     // References
  timestamp?: Date;                  // Optional
  isLoading?: boolean;               // Streaming indicator
}
```

**Styling:**
- User message: Right-aligned, primary blue background, white text
- Assistant message: Left-aligned, muted background, dark text
- Sources: Collapsed by default, expandable list with links

```tsx
export const ChatBubble: React.FC<ChatBubbleProps> = ({
  role,
  content,
  sourceDocuments,
}) => {
  const [showSources, setShowSources] = useState(false);

  return (
    <div
      className={`flex ${role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div
        className={`max-w-xs md:max-w-md lg:max-w-lg px-4 py-2 rounded-lg ${
          role === 'user'
            ? 'bg-primary text-white'
            : 'bg-muted text-foreground'
        }`}
      >
        <p className="text-sm md:text-base">{content}</p>

        {sourceDocuments && (
          <button
            onClick={() => setShowSources(!showSources)}
            className="text-xs mt-2 underline opacity-75"
          >
            {showSources ? 'Hide' : 'Show'} sources ({sourceDocuments.length})
          </button>
        )}

        {showSources && (
          <SourceDocuments documents={sourceDocuments} />
        )}
      </div>
    </div>
  );
};
```

### PromptInput

**Features:**
- Textarea with auto-expand (grows as user types)
- Send button (keyboard shortcut: Cmd+Enter)
- Character counter (optional)
- Disabled state while processing

```tsx
interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
  placeholder?: string;
}

export const PromptInput: React.FC<PromptInputProps> = ({
  value,
  onChange,
  onSend,
  disabled,
  placeholder = 'Ask about your documents...',
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      onSend();
    }
  };

  return (
    <div className="border-t bg-background p-4 sticky bottom-0">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className="w-full resize-none rounded-lg border px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
      />
      <div className="flex justify-between items-center mt-2">
        <span className="text-xs text-muted-foreground">
          {value.length} / 5000
        </span>
        <Button
          onClick={onSend}
          disabled={disabled || !value.trim()}
          size="sm"
        >
          {disabled ? 'Sending...' : 'Send'}
        </Button>
      </div>
    </div>
  );
};
```

### UploadModal

**Features:**
- Drag-and-drop zone
- File type validation (PDF, DOCX, TXT)
- File size validation (max 100MB per workspace)
- Progress bar during upload
- Error handling with clear messages

```tsx
export const UploadModal = ({
  isOpen,
  onClose,
  workspaceSlug,
}: {
  isOpen: boolean;
  onClose: () => void;
  workspaceSlug: string;
}) => {
  const [files, setFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files);
    setFiles((prev) => [...prev, ...droppedFiles]);
  };

  const handleUpload = async () => {
    setIsUploading(true);
    setError(null);

    try {
      // Call API to embed
      await fileAPI.embed(files, workspaceSlug);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload Documents</DialogTitle>
        </DialogHeader>

        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:bg-muted transition"
        >
          <p className="text-sm text-muted-foreground">
            Drag files here or click to browse
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            PDF, DOCX, or TXT (max 100MB per workspace)
          </p>
        </div>

        {files.length > 0 && (
          <div className="space-y-2">
            {files.map((file) => (
              <div
                key={file.name}
                className="flex justify-between items-center p-2 bg-muted rounded"
              >
                <span className="text-sm">{file.name}</span>
                <button
                  onClick={() =>
                    setFiles(files.filter((f) => f.name !== file.name))
                  }
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}

        {error && <div className="text-sm text-destructive">{error}</div>}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleUpload}
            disabled={files.length === 0 || isUploading}
          >
            {isUploading ? 'Uploading...' : 'Upload'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
```

---

## Dark Mode Implementation

**Using next-themes:**

```tsx
// providers/ThemeProvider.tsx
export const ThemeProvider = ({ children }: { children: React.ReactNode }) => {
  return (
    <NextThemesProvider attribute="class" defaultTheme="system" enableSystem>
      {children}
    </NextThemesProvider>
  );
};

// components/shared/ThemeToggle.tsx
export const ThemeToggle = () => {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
    >
      {theme === 'dark' ? '☀️' : '🌙'}
    </Button>
  );
};
```

**Tailwind config for dark mode:**

```typescript
// tailwind.config.ts
export default {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: 'hsl(var(--color-primary))',
        secondary: 'hsl(var(--color-secondary))',
        background: 'hsl(var(--color-background))',
        foreground: 'hsl(var(--color-foreground))',
        muted: 'hsl(var(--color-muted))',
        'muted-foreground': 'hsl(var(--color-muted-foreground))',
        // ... other colors
      },
    },
  },
};
```

---

## Accessibility Standards

### WCAG 2.1 AA Compliance

- **Color Contrast:** All text ≥ 4.5:1 (normal) or 3:1 (large)
- **Focus Indicators:** Visible focus ring (2px solid) on all interactive elements
- **Keyboard Navigation:** Tab order logical, no keyboard traps
- **ARIA Labels:** Buttons, icons, inputs have descriptive labels
- **Error Messages:** Associated with form fields, visible in color + text
- **Images:** All images have alt text or aria-hidden if decorative

### Checklist

- [ ] Color contrast checked (no white text on light blue)
- [ ] Focus ring visible on buttons, inputs, links
- [ ] Form error messages describe problem clearly
- [ ] Modals have focus trap (focus stays inside)
- [ ] Icons have titles or aria-labels
- [ ] Video/audio has captions (future feature)

### Example

```tsx
<button
  className="focus:ring-2 focus:ring-offset-2 focus:ring-primary"
  aria-label="Send message"
  disabled={isDisabled}
>
  Send
</button>
```

---

## Responsive Design

### Breakpoints (Tailwind)

```
sm:  640px   (mobile landscape)
md:  768px   (tablet)
lg:  1024px  (desktop)
xl:  1280px  (large desktop)
```

### Mobile-First Strategy

**Design for mobile first, then enhance:**

```tsx
// Mobile: single column
// Tablet: two columns
// Desktop: three columns
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {items.map((item) => (
    <Card key={item.id}>{item}</Card>
  ))}
</div>
```

### Desktop Minimum Width

- **Min viewport:** 1024px
- **Max content width:** 1280px
- **Horizontal padding:** 16px (mobile), 32px (desktop)

---

## Animation & Transitions

**Subtle, purposeful animations only:**

```css
/* From tailwindcss-animate */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideDown {
  from { transform: translateY(-10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* Usage */
.fade-in { animation: fadeIn 0.2s ease-out; }
.slide-down { animation: slideDown 0.3s ease-out; }
```

**Duration guidelines:**
- Fade: 200ms (quick feedback)
- Slide/Transform: 300ms (natural motion)
- Hover: 150ms (responsive)

---

## Known State: Vietnamese UI Labels

**Current:** All UI strings are in Vietnamese (see `client/app/components/` and `client/app/` for examples).

**Internalization Plan (Future):**
- Extract strings to `i18n/locales/en.json` and `vi.json`
- Use `next-i18next` or similar
- Support EN + VI at launch

**For now:** Document this as "Vietnamese UI, English docs."

---

## Design Debt & Future Improvements

- [ ] Create design tokens file (colors, spacing, typography)
- [ ] Build Storybook for component showcase
- [ ] Add animations to chat (message entrance, loading)
- [ ] Implement responsive sidebar (currently mobile-clunky)
- [ ] Add onboarding tour (first-time user flow)
- [ ] Create design system documentation (Figma or similar)

---

## Resources

- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Radix UI Docs](https://www.radix-ui.com/docs/primitives/overview/introduction)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [next-themes GitHub](https://github.com/pacocoursey/next-themes)

See [code-standards.md](./code-standards.md) for component implementation patterns and [system-architecture.md](./system-architecture.md) for overall architecture.
