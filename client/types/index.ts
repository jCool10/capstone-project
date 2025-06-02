export interface IWorkspace {
  name: string
  slug: string
  user: string
  model: string
  isEmbedded?: boolean
  filePaths?: string[]
  createdAt?: string
  _id?: string
}

export interface IMessage {
  _id?: string
  content: string
  role: "user" | "assistant"
  workspaceSlug?: string
  createdAt?: string
}
