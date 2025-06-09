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

async function create(client: User, publicKey: string, signature?: string, keyId?: string) {
  const filter = { client: client }
  const update: any = { publicKey: publicKey }
  if (signature) update.signature = signature
  if (keyId) update.keyId = keyId
  const options = { upsert: true, new: true }
  return KeystoreModel.findOneAndUpdate(filter, update, options)
}

async function updateOne(filter: object, update: object) {
  return KeystoreModel.updateOne(filter, update, { new: true }).exec()
}

export default {
  findforKey,
  remove,
  removeAllForClient,
  find,
  create,
  updateOne
}
