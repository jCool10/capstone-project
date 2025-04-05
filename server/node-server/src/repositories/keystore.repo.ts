import { KeystoreModel } from '@/models/keyStore.model'
import { Types } from 'mongoose'
import User from '@/models/user.model'

async function findforKey(client: User, key: string) {
  return KeystoreModel.findOne({
    client: client,
    primaryKey: key,
    status: true
  })
    .lean()
    .exec()
}

async function remove(id: Types.ObjectId) {
  return KeystoreModel.findByIdAndDelete(id).lean().exec()
}

async function removeAllForClient(client: User) {
  return KeystoreModel.deleteMany({ client: client }).exec()
}

async function find(client: User, primaryKey: string, secondaryKey: string) {
  return KeystoreModel.findOne({
    client: client,
    primaryKey: primaryKey,
    secondaryKey: secondaryKey
  })
    .lean()
    .exec()
}

async function create(client: User, publicKey: string, privateKey: string) {
  const now = new Date()
  const keystore = await KeystoreModel.create({
    client: client,
    publicKey: publicKey,
    privateKey: privateKey,
    createdAt: now,
    updatedAt: now
  })
  return keystore.toObject()
}

export default {
  findforKey,
  remove,
  removeAllForClient,
  find,
  create
}
