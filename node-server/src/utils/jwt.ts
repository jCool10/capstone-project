import jwt from 'jsonwebtoken'

const createTokenPair = (payload: object, privateKey: string) => {
  try {
    const accessToken = jwt.sign(payload, privateKey, {
      algorithm: 'RS256',
      expiresIn: '1 days'
    })

    const refreshToken = jwt.sign(payload, privateKey, {
      algorithm: 'RS256',
      expiresIn: '2 days'
    })

    return {
      accessToken,
      refreshToken
    }
  } catch (error) {
    console.error(`createTokenPair error:: `, error)
  }
}
const verifyToken = (token: string, publicKey: string): any => {
  try {
    return jwt.verify(token, publicKey)
  } catch (error) {
    console.error(`verifyToken error:: `, error)
  }
}

export { createTokenPair, verifyToken }
