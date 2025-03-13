import {
  ConflictError,
  ForbiddenError,
  InternalServerError,
  NotFoundError,
  UnauthorizedError
} from '@/core/error.response'
import { UserModel } from '@/models/user.model'
import { comparePassword, hashPassword } from '@/utils/bcrypt'
import { Request } from 'express'
import crypto from 'crypto'
import { createTokenPair } from '@/utils/jwt'
import { getDataByField } from '@/utils'
import { keyStoreService } from './keyStore,service'

export class authService {
  KeyStoreService: keyStoreService

  constructor() {
    this.KeyStoreService = new keyStoreService()
  }

  login = async (req: Request) => {
    const { email, password } = req.body

    const user = await UserModel.findOne({ email }).lean()

    if (!user) {
      throw new NotFoundError('User not found')
    }

    const matchPassword = await comparePassword(password, user.password)

    if (!matchPassword) {
      throw new UnauthorizedError('Password is incorrect')
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

    const token = createTokenPair({ email, name: user.name, id: user._id.toString() }, privateKey)

    if (!token) {
      throw new InternalServerError('Failed to create token')
    }

    await this.KeyStoreService.createKeyTokenPair(
      { user: user._id.toString() },
      publicKey,
      privateKey,
      token.refreshToken
    )

    return {
      user: getDataByField({ fields: ['email', 'name'], object: user }),
      token
    }
  }

  signup = async (req: Request) => {
    const { email, password, name } = req.body

    const isFoundedUser = await UserModel.find({ email }).lean()

    if (isFoundedUser) {
      throw new ConflictError('User already exists')
    }

    const passwordHash = await hashPassword(password)

    const newUser = await UserModel.create({
      email,
      password: passwordHash,
      name
    })

    if (!newUser) {
      throw new InternalServerError('Failed to create user')
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

    const token = createTokenPair({ email, name, id: newUser._id.toString() }, privateKey)

    if (!token) {
      throw new InternalServerError('Failed to create token')
    }

    await this.KeyStoreService.createKeyTokenPair({ user: newUser._id }, publicKey, privateKey, token.refreshToken)

    return {
      user: getDataByField({ fields: ['email', 'name'], object: newUser }),
      token
    }
  }

  logout = async (req: Request) => {
    const keyStore = req.keyStore
    const delKey = await this.KeyStoreService.deleteOne(keyStore._id)

    return delKey
  }

  refreshToken = async (req: Request) => {
    const { user, refreshToken, keyStore } = req
    const { id, email, name } = user

    if (keyStore.refreshTokensUsed.includes(refreshToken)) {
      await this.KeyStoreService.findByIdAndDelete({ id })
      throw new ForbiddenError('Something wrong happen!! Pls re-login')
    }

    // console.log('keyStore:: ', keyStore)

    if (refreshToken !== keyStore.refreshToken) throw new UnauthorizedError('User not authorized')

    const foundUser = await UserModel.findOne({ email }).lean()

    if (!foundUser) throw new NotFoundError('Shop not found')

    const tokens = createTokenPair({ id: id.toString(), email, name }, keyStore.privateKey)

    if (!tokens) throw new InternalServerError('Failed to create token')

    // update keyStore
    keyStore.refreshTokensUsed.push(refreshToken)

    console.log('keyStore:: ', keyStore)

    return { user, tokens }
  }
}
