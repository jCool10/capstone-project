import { Schema, model, Types } from 'mongoose'
import User from './user.model'

export const DOCUMENT_NAME = 'UserKeyPair'
export const COLLECTION_NAME = 'userkeyPairs'

export interface IUserKeyPair {
  _id?: Types.ObjectId
  user: Types.ObjectId
  keyId: string
  encryptedPrivateKey: string // Encrypted with master key
  publicKey: string
  algorithm: 'RSA' | 'EC'
  keySize: number
  status: 'active' | 'revoked' | 'decrypt-only'
  version: number
  purpose: 'signing' | 'encryption' | 'both'
  expiresAt?: Date
  createdAt?: Date
  updatedAt?: Date
}

const userKeyPairSchema = new Schema(
  {
    user: {
      type: Schema.Types.ObjectId,
      required: true,
      ref: 'User',
      index: true
    },
    keyId: {
      type: String,
      required: true,
      unique: true,
      index: true
    },
    encryptedPrivateKey: {
      type: String,
      required: true
    },
    publicKey: {
      type: String,
      required: true
    },
    algorithm: {
      type: String,
      enum: ['RSA', 'EC'],
      required: true,
      default: 'RSA'
    },
    keySize: {
      type: Number,
      required: true
    },
    status: {
      type: String,
      enum: ['active', 'revoked', 'decrypt-only'],
      required: true,
      default: 'active'
    },
    version: {
      type: Number,
      required: true,
      default: 1
    },
    purpose: {
      type: String,
      enum: ['signing', 'encryption', 'both'],
      required: true,
      default: 'both'
    },
    expiresAt: {
      type: Date,
      default: () => new Date(Date.now() + 365 * 24 * 60 * 60 * 1000) // 1 year from creation
    }
  },
  {
    timestamps: true,
    collection: COLLECTION_NAME,
    versionKey: false
  }
)

// Compound indexes for efficient queries
userKeyPairSchema.index({ user: 1, status: 1, version: -1 })
userKeyPairSchema.index({ keyId: 1, status: 1 })
userKeyPairSchema.index({ user: 1, purpose: 1, status: 1 })
userKeyPairSchema.index({ expiresAt: 1 }, { expireAfterSeconds: 0 })

export const UserKeyPairModel = model<IUserKeyPair>(DOCUMENT_NAME, userKeyPairSchema)
