'use strict'

import { Schema, model, Types } from 'mongoose'

const DOCUMENT_NAME = 'ApiKey'
const COLLECTION_NAME = 'ApiKeys'

export enum Permission {
  USER = 'USER',
  ADMIN = 'ADMIN'
}

export default interface ApiKey {
  _id: Types.ObjectId
  key: string
  version: number
  permissions: Permission[]
  comments: string[]
  status?: boolean
  createdAt?: Date
  updatedAt?: Date
}

const apiKeySchema = new Schema<ApiKey>(
  {
    key: {
      type: Schema.Types.String,
      required: true,
      unique: true,
      maxlength: 1024,
      trim: true
    },
    version: {
      type: Schema.Types.Number,
      required: true,
      min: 1,
      max: 100
    },
    permissions: {
      type: [
        {
          type: Schema.Types.String,
          required: true,
          enum: Object.values(Permission)
        }
      ],
      required: true
    },
    comments: {
      type: [
        {
          type: Schema.Types.String,
          required: true,
          trim: true,
          maxlength: 1000
        }
      ],
      required: true
    },
    status: {
      type: Schema.Types.Boolean,
      default: true
    }
  },
  {
    timestamps: true,
    collection: COLLECTION_NAME,
    versionKey: false
  }
)

apiKeySchema.index({ key: 1, status: 1 })

export const ApiKeyModel = model(DOCUMENT_NAME, apiKeySchema)
