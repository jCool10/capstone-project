import User, { UserModel } from '@/models/user.model'
import KeystoreRepo from '@/repositories/keystore.repo'
import { Types } from 'mongoose'
import { InternalServerError } from '@/core/error.response'

async function exists(id: Types.ObjectId) {
  const user = await UserModel.exists({ _id: id, status: true })
  return user !== null && user !== undefined
}

async function findPrivateProfileById(id: Types.ObjectId) {
  return UserModel.findOne({ _id: id, status: true }).select('+email').lean<User>().exec()
}

// contains critical information of the user
async function findById(id: Types.ObjectId) {
  return UserModel.findOne({ _id: id, status: true }).select('+email +password').lean().exec()
}

async function findByEmail(email: string) {
  return UserModel.findOne({ email: email }).select('+email +password').lean().exec()
}

async function findFieldsById(id: Types.ObjectId, ...fields: string[]) {
  return UserModel.findOne({ _id: id, status: true }, [...fields])
    .lean()
    .exec()
}

async function findPublicProfileById(id: Types.ObjectId) {
  return UserModel.findOne({ _id: id, status: true }).lean().exec()
}

async function create(user: User, accessTokenKey: string, refreshTokenKey: string) {
  const now = new Date()

  user.createdAt = user.updatedAt = now
  const createdUser = await UserModel.create(user)

  const keystore = await KeystoreRepo.create(createdUser, accessTokenKey, refreshTokenKey)
  return {
    user: createdUser,
    keystore: keystore
  }
}

async function update(user: User, accessTokenKey: string, refreshTokenKey: string) {
  user.updatedAt = new Date()
  await UserModel.updateOne({ _id: user._id }, { $set: { ...user } })
    .lean()
    .exec()
  const keystore = await KeystoreRepo.create(user, accessTokenKey, refreshTokenKey)
  return { user: user, keystore: keystore }
}

async function updateInfo(user: User) {
  user.updatedAt = new Date()
  return UserModel.updateOne({ _id: user._id }, { $set: { ...user } })
    .lean()
    .exec()
}

export default {
  exists,
  findPrivateProfileById,
  findById,
  findByEmail,
  findFieldsById,
  findPublicProfileById,
  create,
  update,
  updateInfo
}
