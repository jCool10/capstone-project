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
  _id?: Types.ObjectId
  workspaceSlug: string
  messages: IMessage[]
}

const messagesSchema = new Schema(
  {
    workspaceSlug: { type: String, required: true },
    messages: [
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
        sourceDocs: [
          {
            text: String,
            metadata: Object
          }
        ]
      }
    ]
  },
  { timestamps: true, collection: COLLECTION_NAME }
)

export const MessagesModel = model(DOCUMENT_NAME, messagesSchema)
