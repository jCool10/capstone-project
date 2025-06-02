import path from 'path'
import { readFile } from 'fs'
import { promisify } from 'util'
import { sign, verify } from 'jsonwebtoken'
import { InternalServerError } from './error.response'
// import { InternalError, BadTokenError, TokenExpiredError } from './ApiError'

/*
 * issuer      — Software organization who issues the token.
 * subject     — Intended user of the token.
 * audience    — Basically identity of the intended recipient of the token.
 * expiresIn   — Expiration time after which the token will be invalid.
 * algorithm   — Encryption algorithm to be used to protect the token.
 */

export class JwtPayload {
  aud: string
  sub: string
  iss: string
  iat: number
  exp: number

  constructor(issuer: string, audience: string, subject: string, validity: number) {
    this.iss = issuer
    this.aud = audience
    this.sub = subject
    this.iat = Math.floor(Date.now() / 1000)
    this.exp = this.iat + validity
  }
}

async function readPublicKey() {
  return promisify(readFile)(path.join(__dirname, '../../storage/comkey/ipc-pub.pem'), 'utf8')
}

async function readPrivateKey() {
  return promisify(readFile)(path.join(__dirname, '../../storage/comkey/ipc-priv.pem'), 'utf8')
}

/**
 * This method encodes the payload and returns the token
 */
async function encode(payload: JwtPayload) {
  const cert = await readPrivateKey()
  if (!cert) throw new InternalServerError('Token generation failure')
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-expect-error
  return promisify(sign)({ ...payload }, cert, { algorithm: 'RS256' })
}

/**
 * This method checks the token and returns the decoded data when token is valid in all respect
 */
async function validate(token: string): Promise<JwtPayload> {
  const cert = await readPublicKey()
  try {
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    return (await promisify(verify)(token, cert)) as JwtPayload
  } catch (e: any) {
    if (e && e.name === 'TokenExpiredError') throw new InternalServerError('Token expired')
    // throws error if the token has not been encrypted by the private key
    throw new InternalServerError('Invalid token')
  }
}

/**
 * Returns the decoded payload if the signature is valid even if it is expired
 */
async function decode(token: string): Promise<JwtPayload> {
  const cert = await readPublicKey()
  try {
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    return (await promisify(verify)(token, cert, {
      ignoreExpiration: true
    })) as JwtPayload
  } catch (e) {
    throw new InternalServerError('Invalid token')
  }
}

export default {
  encode,
  validate,
  decode
}
