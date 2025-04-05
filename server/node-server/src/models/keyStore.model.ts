'use strict'

import { Schema, model, Types } from 'mongoose'
import User from './user.model'

export const DOCUMENT_NAME = 'Keystore'
export const COLLECTION_NAME = 'keystores'

export default interface Keystore {
  _id: Types.ObjectId
  client: User
  publicKey: string
  privateKey: string
  status?: boolean
  createdAt?: Date
  updatedAt?: Date
}

const keyTokenSchema = new Schema(
  {
    client: {
      type: Schema.Types.ObjectId,
      required: true,
      ref: 'User'
    },
    publicKey: {
      type: Schema.Types.String,
      required: true,
      trim: true
    },
    privateKey: {
      type: Schema.Types.String,
      required: true,
      trim: true
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

keyTokenSchema.index({ client: 1 })
keyTokenSchema.index({ client: 1, publicKey: 1, status: 1 })
keyTokenSchema.index({ client: 1, privateKey: 1, status: 1 })

export const KeystoreModel = model(DOCUMENT_NAME, keyTokenSchema)
