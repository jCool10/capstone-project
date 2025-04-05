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

    const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
      modulusLength: 4096,
      publicKeyEncoding: {
        type: 'pkcs1',
        format: 'pem'
      },
      privateKeyEncoding: {
        type: 'pkcs1',
        format: 'pem'
      }
    })

    const keystore = await keystoreRepo.create(user, publicKey, privateKey)

    const tokens = createTokens(user, keystore.privateKey)

    const userData = getDataByField({ fields: ['email', 'name', '_id'], object: user })

    return { user: userData, tokens }
  }

  signup = async (req: Request) => {
    const { email, password, name } = req.body

    const isFoundedUser = await userRepo.findByEmail(email)

    if (isFoundedUser) {
      throw new ConflictError('User already exists')
    }

    const passwordHash = await hashPassword(password)

    const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
      modulusLength: 4096,
      publicKeyEncoding: {
        type: 'pkcs1',
        format: 'pem'
      },
      privateKeyEncoding: {
        type: 'pkcs1',
        format: 'pem'
      }
    })

    const { user: createdUser, keystore } = await userRepo.create(
      {
        email,
        password: passwordHash,
        name
      } as User,
      publicKey,
      privateKey
    )

    const tokens = createTokens({ email, name, id: createdUser._id.toString() }, keystore.privateKey)

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

    if (!foundUser) throw new NotFoundError('Shop not found')

    const tokens = createTokens({ id: id.toString(), email, name }, keyStore.privateKey)

    if (!tokens) throw new InternalServerError('Failed to create token')

    // update keyStore
    keyStore.refreshTokensUsed.push(refreshToken)

    return { user, tokens }
  }
}
