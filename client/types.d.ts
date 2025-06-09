interface File extends Blob {
  readonly lastModified: number
  readonly name: string
}

// Mở rộng interface File bằng cách thêm các trường mới
interface File {
  readonly author: string // Trường mới
  readonly description: string // Trường mới
}

export interface IWorkspace {
  _id?: string
  name: string
  slug: string
  user: string
  model: string
  isEmbedded: boolean
}

export interface IMessage {
  _id?: string
  messages: {
    content: string
    role: string
    workspaceSlug: string
  }[]
}

export interface IMessages {
  _id?: string
  content: string
  role: string
  workspaceSlug: string
  sourceDocuments?: {
    content: string
  }[]
}
