import { NotFoundError, UnauthorizedError, ForbiddenError } from '@/core/error.response'
import catchAsync from '@/helpers/cathAsync'
import { KeystoreModel } from '@/models/keyStore.model'
import { keyStoreService } from '@/services/keyStore,service'
import { NextFunction, Request, Response } from 'express'
import mongoose from 'mongoose'
import { verifyToken } from './jwt'
import { ApiKeyModel } from '@/models/apiKey.model'

export const authentication = catchAsync(async (req: Request, res: Response, next: NextFunction) => {
  const accessToken = req.headers['authorization'] as string
  const refreshToken = req.headers['refresh-token'] as string
  const clientId = req.headers['client-id'] as string

  if (!accessToken && !refreshToken) {
    throw new UnauthorizedError('Unauthorized')
  }

  const keyStore = await KeystoreModel.findOne({ client: new mongoose.Types.ObjectId(clientId) }).lean()

  if (!keyStore) {
    throw new NotFoundError('Key not found')
  }

  if (refreshToken) {
    const decodedUser = verifyToken(refreshToken, keyStore.publicKey)

    if (!decodedUser) {
      throw new UnauthorizedError('Unauthorized')
    }

    req.user = decodedUser
    req.keyStore = keyStore

    return next()
  }

  const decodedUser = verifyToken(accessToken, keyStore.publicKey)

  if (!decodedUser) {
    throw new UnauthorizedError('Unauthorized')
  }

  req.user = decodedUser
  req.keyStore = keyStore

  return next()
})

export const apikey = catchAsync(async (req: Request, res: Response, next: NextFunction) => {
  const key = req.headers['x-api-key']?.toString()

  if (!key) {
    throw new UnauthorizedError('Unauthorized')
  }

  const apiKey = await ApiKeyModel.findOne({ key, status: true }).lean().exec()

  if (!apiKey) {
    throw new UnauthorizedError('Unauthorized')
  }

  req.apiKey = apiKey

  return next()
})

// export const permission = (permission: string) => {
//   return (req: Request, res: Response, next: NextFunction) => {
//     if (!req.apiKey?.permissions) {
//       throw new ForbiddenError('Permission Denied')
//     }

//     const exists = req.apiKey.permissions.find((entry: string) => entry === permission)

//     if (!exists) {
//       throw new ForbiddenError('Permission Denied')
//     }

//     return next()
//   }
// }
