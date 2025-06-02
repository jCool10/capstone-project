import User, { UserModel } from '@/models/user.model'
import KeystoreRepo from '@/repositories/keystore.repo'
import { Types } from 'mongoose'

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

async function create(user: User, publicKey: string) {
  const createdUser = await UserModel.create(user)

  const keystore = await KeystoreRepo.create(createdUser, publicKey)
  return {
    user: createdUser,
    keystore
  }
}

async function update(user: User, publicKey: string) {
  await UserModel.updateOne({ _id: user._id }, { $set: { ...user } })
    .lean()
    .exec()
  const keystore = await KeystoreRepo.create(user, publicKey)
  return { user, keystore }
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
