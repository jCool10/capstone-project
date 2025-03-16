import { KeyTokenModel } from '@/models/keyStore.model'

export class keyStoreService {
  async createKeyTokenPair(payload: object, publicKey: string, privateKey: string, refreshToken: string) {
    const filter = payload
    const update = { publicKey, privateKey, refreshToken, refreshTokenUsed: [] }
    const options = { upsert: true, new: true }

    const tokens = await KeyTokenModel.findOneAndUpdate(filter, update, options)

    if (!tokens) {
      throw new Error('Failed to create tokens')
    }

    return tokens
  }

  async updateOne(payload: object, update: object) {
    return await KeyTokenModel.updateOne(payload, update, { new: true, upsert: true })
  }

  async deleteOne(payload: object) {
    return await KeyTokenModel.deleteOne(payload)
  }

  async findByIdAndDelete(payload: object) {
    return await KeyTokenModel.findByIdAndDelete(payload)
  }

  async findOne(payload: object) {
    return await KeyTokenModel.findOne(payload)
  }
}
