import { Schema, model, Types } from 'mongoose'

const DOCUMENT_NAME = 'Workspace'
const COLLECTION_NAME = 'Workspaces'

function generateSlug(length: number = 10): string {
  const characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  let slug = ''
  for (let i = 0; i < length; i++) {
    const randomIndex = Math.floor(Math.random() * characters.length)
    slug += characters[randomIndex]
  }
  return slug
}

export default interface Workspace {
  _id?: Types.ObjectId
  name: string
  slug?: string
  user: Types.ObjectId
  isEmbedded?: boolean
  filePaths?: string[]
  fileKeys?: string[]
}

export enum MessageType {
  API_MESSAGE = 'apiMessage',
  USER_MESSAGE = 'userMessage'
}

const workspaceSchema = new Schema(
  {
    name: {
      type: String,
      required: true
    },
    slug: {
      type: String,
      required: true,
      unique: true,
      default: () => `wo${generateSlug()}`
    },
    user: {
      type: Schema.Types.ObjectId,
      required: true
    },
    isEmbedded: {
      type: Boolean,
      default: false
    },
    filePaths: {
      type: [String],
      default: []
    },
    fileKeys: {
      type: [String],
      default: []
    }
  },
  {
    timestamps: true,
    collection: COLLECTION_NAME,
    versionKey: false
  }
)

export const WorkspaceModel = model(DOCUMENT_NAME, workspaceSchema)
