import User from '@/models/user.model'
import jwt from 'jsonwebtoken'
import { configs } from '@/configs'

const createTokens = (user: User, privateKey: string, passphrase?: string) => {
  try {
    // If passphrase is provided, create key object with passphrase
    const keyObject = passphrase ? { key: privateKey, passphrase } : privateKey

    const accessToken = jwt.sign({ user }, keyObject, {
      algorithm: 'RS256',
      expiresIn: configs.tokenInfo.accessTokenValidity
    })

    const refreshToken = jwt.sign({ user }, keyObject, {
      algorithm: 'RS256',
      expiresIn: configs.tokenInfo.refreshTokenValidity
    })

    return {
      accessToken,
      refreshToken
    }
  } catch (error) {
    throw new Error('Failed to create tokens: ' + (error instanceof Error ? error.message : String(error)))
  }
}

const verifyToken = (token: string, publicKey: string) => {
  return jwt.verify(token, publicKey)
}

export { verifyToken, createTokens }
