import {
  ConflictError,
  ForbiddenError,
  InternalServerError,
  NotFoundError,
  UnauthorizedError
} from '@/core/error.response'
import User, { UserModel } from '@/models/user.model'
import { comparePassword, hashPassword } from '@/utils/bcrypt'
import { Request } from 'express'
import crypto from 'crypto'
import { createTokens } from '@/utils/jwt'
import { getDataByField } from '@/utils'
import { keyStoreService } from './keyStore,service'
import userRepo from '@/repositories/user.repo'
import keystoreRepo from '@/repositories/keystore.repo'
import CommunicationKey from '@/utils/communicationKey'

export class authService {
  KeyStoreService: keyStoreService

  constructor() {
    this.KeyStoreService = new keyStoreService()
  }

  login = async (req: Request) => {
    const { email, password } = req.body

    const user = await userRepo.findByEmail(email)

    if (!user) {
      throw new UnauthorizedError('User not found')
    }

    const match = await comparePassword(password, user.password)

    if (!match) {
      throw new UnauthorizedError('Invalid password')
    }

    const comKey = new CommunicationKey(true)

    await keystoreRepo.create(user, comKey.publicKey)

    const tokens = await createTokens(user, comKey.privateKey)

    const userData = getDataByField({ fields: ['email', 'name', '_id'], object: user })

    return { user: userData, tokens }
  }

  register = async (req: Request) => {
    const { email, password, name } = req.body

    const isFoundedUser = await userRepo.findByEmail(email)

    if (isFoundedUser) {
      throw new ConflictError('User already exists')
    }

    const passwordHash = await hashPassword(password)

    const comKey = new CommunicationKey(true)

    const { user: createdUser } = await userRepo.create(
      {
        email,
        password: passwordHash,
        name
      } as User,
      comKey.publicKey
    )

    const tokens = await createTokens(createdUser, comKey.privateKey)

    const userData = getDataByField({ fields: ['email', 'name', '_id'], object: createdUser })

    return { user: userData, tokens }
  }

  logout = async (req: Request) => {
    await keystoreRepo.remove(req.keyStore._id)
    return {}
  }

  refreshToken = async (req: Request) => {
    const { user, refreshToken, keyStore } = req
    const { id, email, name } = user

    if (keyStore.refreshTokensUsed.includes(refreshToken)) {
      await keystoreRepo.remove(keyStore._id)
      throw new ForbiddenError('Something wrong happen!! Pls re-login')
    }

    if (refreshToken !== keyStore.refreshToken) throw new UnauthorizedError('User not authorized')

    const foundUser = await userRepo.findByEmail(email)

    if (!foundUser) throw new NotFoundError('User not found')

    const comKey = new CommunicationKey(true)

    // Create new tokens with new key
    const tokens = await createTokens({ _id: id.toString(), email, name } as User, comKey.privateKey)

    if (!tokens) throw new InternalServerError('Failed to create token')

    // Update keyStore with new keys and add old refreshToken to used list
    const updatedKeyStore = {
      ...keyStore,
      publicKey: comKey.publicKey,
      refreshToken: tokens.refreshToken,
      refreshTokensUsed: [...keyStore.refreshTokensUsed, refreshToken]
    }

    // Save the updated keyStore
    await keystoreRepo.updateOne({ _id: keyStore._id }, updatedKeyStore)

    return {
      user: { _id: id, email, name },
      tokens
    }
  }
}
