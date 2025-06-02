import { Schema, model, Types } from 'mongoose'
import { nanoid } from 'nanoid'

const DOCUMENT_NAME = 'Workspace'
const COLLECTION_NAME = 'Workspaces'

export default interface Workspace {
  _id?: Types.ObjectId
  name: string
  slug?: string
  user: Types.ObjectId
  isEmbedded?: boolean
  filePaths?: string[]
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
      default: () => `wo${nanoid(10)}`
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
    }
  },
  {
    timestamps: true,
    collection: COLLECTION_NAME,
    versionKey: false
  }
)

export const WorkspaceModel = model(DOCUMENT_NAME, workspaceSchema)
