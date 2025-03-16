import { NotFoundError, UnauthorizedError } from '@/core/error.response'
import catchAsync from '@/helpers/cathAsync'
import { KeyTokenModel } from '@/models/keyStore.model'
import { keyStoreService } from '@/services/keyStore,service'
import { NextFunction, Request, Response } from 'express'
import Mongoose from 'mongoose'
import { verifyToken } from './jwt'

const parseToken = (token: any) => JSON.parse(Buffer.from(token.split('.')[1], 'base64').toString())

export const authentication = catchAsync(async (req: Request, res: Response, next: NextFunction) => {
  const accessToken = req.headers['authorization'] as string
  const refreshToken = req.headers['refreshtoken'] as string

  const parsedObject = parseToken(accessToken || refreshToken)

  if (!parsedObject.id) {
    throw new UnauthorizedError('Unauthorized')
  }

  const keyStore = await KeyTokenModel.findOne({ user: new Mongoose.Types.ObjectId(parsedObject.id) }).lean()

  if (!keyStore) {
    throw new NotFoundError('Key not found')
  }

  if (refreshToken) {
    const decodedUser = verifyToken(refreshToken, keyStore.publicKey)

    if (!decodedUser) {
      throw new UnauthorizedError('Unauthorized')
    }

    if (parsedObject.id !== decodedUser.id) {
      throw new UnauthorizedError('Unauthorized')
    }

    req.refreshToken = refreshToken
    req.user = decodedUser
    req.keyStore = keyStore

    return next()
  }

  if (!accessToken) {
    throw new UnauthorizedError('Unauthorized')
  }

  const decodedUser = verifyToken(accessToken, keyStore.publicKey)

  req.user = decodedUser
  req.keyStore = keyStore

  return next()
})
