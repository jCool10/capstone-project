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
  workspaceSlug?: string
  createdAt?: string

  // Backend format
  message?: string
  type?: "userMessage" | "apiMessage"
  sourceDocs?: string[]

  // Frontend format
  content?: string
  role?: "user" | "assistant"
  sourceDocuments?: SourceDocument[]
}

// Extended message interface to handle all possible properties
export interface ExtendedMessage extends IMessage {
  message: string
  type: "userMessage" | "apiMessage"
  sourceDocs: string[]
  content: string
  role: "user" | "assistant"
  sourceDocuments: SourceDocument[]
}

export interface SourceDocument {
  id: string
  text: string
  metadata: {
    file_name: string
  }
}
