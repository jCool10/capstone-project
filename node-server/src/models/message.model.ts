import { Schema, model, Types } from 'mongoose'

const DOCUMENT_NAME = 'Message'
const COLLECTION_NAME = 'Messages'

export enum MessageType {
  API_MESSAGE = 'apiMessage',
  USER_MESSAGE = 'userMessage'
}

export interface IMessage {
  type: MessageType
  message: string
  sourceDocs?: string[]
}

export interface IMessages {
  _id: Types.ObjectId
  workspaceId: Types.ObjectId
  messages: IMessage[]
}

const messageSchema = new Schema(
  {
    type: {
      type: String,
      enum: Object.values(MessageType),
      required: true
    },
    message: {
      type: String,
      required: true
    },
    sourceDocs: Array
  },
  {
    _id: false
  }
)

const messagesSchema = new Schema(
  {
    workspaceId: { type: Schema.Types.ObjectId, required: true },
    messages: [messageSchema]
  },
  { timestamps: true, collection: COLLECTION_NAME }
)

export const MessagesModel = model(DOCUMENT_NAME, messagesSchema)
