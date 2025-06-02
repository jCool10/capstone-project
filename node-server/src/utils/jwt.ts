import User from '@/models/user.model'
import jwt from 'jsonwebtoken'
import { configs } from '@/configs'

const createTokens = async (user: User, privateKey: string) => {
  const accessToken = jwt.sign({ user }, privateKey, {
    algorithm: 'RS256',
    expiresIn: configs.tokenInfo.accessTokenValidity
  })

  const refreshToken = jwt.sign({ user }, privateKey, {
    algorithm: 'RS256',
    expiresIn: configs.tokenInfo.refreshTokenValidity
  })

  return {
    accessToken,
    refreshToken
  }
}

const verifyToken = (token: string, publicKey: string) => {
  return jwt.verify(token, publicKey)
}

export { verifyToken, createTokens }
