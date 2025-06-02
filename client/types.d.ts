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
}

export interface IMessage {
  _id?: string
  content: string
  role: string
  workspaceSlug: string
}
