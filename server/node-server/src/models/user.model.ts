'use strict'

import { Schema, model, Types } from 'mongoose'

const DOCUMENT_NAME = 'User'
const COLLECTION_NAME = 'Users'

export default interface User {
  _id: Types.ObjectId
  name: string
  email: string
  password: string

  verified?: boolean
  status?: boolean
  createdAt?: Date
  updatedAt?: Date
}

const userSchema = new Schema<User>(
  {
    name: {
      type: Schema.Types.String,
      trim: true,
      maxlength: 200,
      required: true
    },
    email: {
      type: Schema.Types.String,
      unique: true,
      trim: true,
      select: false,
      required: true
    },
    password: {
      type: Schema.Types.String,
      select: false,
      required: true
    },
    verified: {
      type: Schema.Types.Boolean,
      default: false
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

userSchema.index({ _id: 1, status: 1 })
userSchema.index({ status: 1 })

export const UserModel = model(DOCUMENT_NAME, userSchema)
