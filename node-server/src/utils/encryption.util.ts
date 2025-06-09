import crypto from 'crypto'
import { promisify } from 'util'
import { configs } from '@/configs'

export interface KeyPair {
  publicKey: string
  privateKey: string
  keyId: string
  createdAt: Date
  algorithm: 'RSA' | 'EC'
  keySize: number
}

export interface EncryptedData {
  data: string
  keyId: string
  algorithm: string
  iv?: string // For symmetric encryption
}

export interface SignedData {
  data: string
  signature: string
  keyId: string
  algorithm: string
  timestamp: number
}

/**
 * Advanced Asymmetric Encryption Utility for Production
 * Supports RSA and Elliptic Curve Cryptography
 */
export class AsymmetricCrypto {
  private static readonly RSA_KEY_SIZE = 4096 // Production-grade key size
  private static readonly EC_CURVE = 'secp384r1' // NIST P-384 curve
  private static readonly HASH_ALGORITHM = 'SHA-256'
  private static readonly RSA_PADDING = crypto.constants.RSA_PKCS1_OAEP_PADDING
  private static readonly RSA_OAEP_HASH = 'sha256'

  /**
   * Generate a new RSA key pair for production use
   */
  static async generateRSAKeyPair(): Promise<KeyPair> {
    const { generateKeyPair } = crypto
    const generateKeyPairAsync = promisify(generateKeyPair)

    const keyId = crypto.randomUUID()

    const { publicKey, privateKey } = await generateKeyPairAsync('rsa', {
      modulusLength: this.RSA_KEY_SIZE,
      publicKeyEncoding: {
        type: 'spki',
        format: 'pem'
      },
      privateKeyEncoding: {
        type: 'pkcs8',
        format: 'pem',
        cipher: 'aes-256-cbc',
        passphrase: this.deriveKeyPassphrase(keyId)
      }
    })

    return {
      publicKey: publicKey as string,
      privateKey: privateKey as string,
      keyId,
      createdAt: new Date(),
      algorithm: 'RSA',
      keySize: this.RSA_KEY_SIZE
    }
  }

  /**
   * Generate Elliptic Curve key pair (alternative to RSA)
   */
  static async generateECKeyPair(): Promise<KeyPair> {
    const { generateKeyPair } = crypto
    const generateKeyPairAsync = promisify(generateKeyPair)

    const keyId = crypto.randomUUID()

    const { publicKey, privateKey } = await generateKeyPairAsync('ec', {
      namedCurve: this.EC_CURVE,
      publicKeyEncoding: {
        type: 'spki',
        format: 'pem'
      },
      privateKeyEncoding: {
        type: 'pkcs8',
        format: 'pem',
        cipher: 'aes-256-cbc',
        passphrase: this.deriveKeyPassphrase(keyId)
      }
    })

    return {
      publicKey: publicKey as string,
      privateKey: privateKey as string,
      keyId,
      createdAt: new Date(),
      algorithm: 'EC',
      keySize: 384 // P-384 curve
    }
  }

  /**
   * Encrypt data using RSA public key with hybrid encryption
   * For large data, uses AES encryption with RSA-encrypted key
   */
  static async encrypt(data: string, publicKey: string, keyId: string): Promise<EncryptedData> {
    const dataBuffer = Buffer.from(data, 'utf8')

    // For small data (< 190 bytes), use direct RSA encryption
    if (dataBuffer.length <= 190) {
      const encrypted = crypto.publicEncrypt(
        {
          key: publicKey,
          padding: this.RSA_PADDING,
          oaepHash: this.RSA_OAEP_HASH
        },
        dataBuffer
      )

      return {
        data: encrypted.toString('base64'),
        keyId,
        algorithm: 'RSA-OAEP'
      }
    }

    // For large data, use hybrid encryption (AES + RSA)
    const aesKey = crypto.randomBytes(32) // 256-bit AES key
    const iv = crypto.randomBytes(16) // 128-bit IV

    // Encrypt data with AES
    const cipher = crypto.createCipheriv('aes-256-gcm', aesKey, iv)
    cipher.setAAD(Buffer.from(keyId, 'utf8')) // Additional authenticated data

    let encryptedData = cipher.update(data, 'utf8', 'base64')
    encryptedData += cipher.final('base64')
    const authTag = cipher.getAuthTag()

    // Encrypt AES key with RSA
    const encryptedKey = crypto.publicEncrypt(
      {
        key: publicKey,
        padding: this.RSA_PADDING,
        oaepHash: this.RSA_OAEP_HASH
      },
      aesKey
    )

    // Combine encrypted key, IV, auth tag, and encrypted data
    const combined = Buffer.concat([encryptedKey, iv, authTag, Buffer.from(encryptedData, 'base64')])

    return {
      data: combined.toString('base64'),
      keyId,
      algorithm: 'RSA-AES-GCM',
      iv: iv.toString('base64')
    }
  }

  /**
   * Decrypt data using RSA private key
   */
  static async decrypt(encryptedData: EncryptedData, privateKey: string): Promise<string> {
    const { data, algorithm, keyId } = encryptedData
    const passphrase = this.deriveKeyPassphrase(keyId)

    if (algorithm === 'RSA-OAEP') {
      // Direct RSA decryption
      const decrypted = crypto.privateDecrypt(
        {
          key: privateKey,
          passphrase,
          padding: this.RSA_PADDING,
          oaepHash: this.RSA_OAEP_HASH
        },
        Buffer.from(data, 'base64')
      )

      return decrypted.toString('utf8')
    }

    if (algorithm === 'RSA-AES-GCM') {
      // Hybrid decryption
      const combined = Buffer.from(data, 'base64')

      // Extract components
      const encryptedKey = combined.subarray(0, 512) // RSA-4096 encrypted key size
      const iv = combined.subarray(512, 528) // 16 bytes IV
      const authTag = combined.subarray(528, 544) // 16 bytes auth tag
      const encryptedPayload = combined.subarray(544)

      // Decrypt AES key with RSA
      const aesKey = crypto.privateDecrypt(
        {
          key: privateKey,
          passphrase,
          padding: this.RSA_PADDING,
          oaepHash: this.RSA_OAEP_HASH
        },
        encryptedKey
      )

      // Decrypt data with AES
      const decipher = crypto.createDecipheriv('aes-256-gcm', aesKey, iv)
      decipher.setAAD(Buffer.from(keyId, 'utf8'))
      decipher.setAuthTag(authTag)

      const decryptedBuffer = decipher.update(encryptedPayload)
      const finalBuffer = decipher.final()
      const decrypted = Buffer.concat([decryptedBuffer, finalBuffer]).toString('utf8')

      return decrypted
    }

    throw new Error(`Unsupported algorithm: ${algorithm}`)
  }

  /**
   * Sign data with private key
   */
  static async sign(data: string, privateKey: string, keyId: string): Promise<SignedData> {
    const passphrase = this.deriveKeyPassphrase(keyId)

    const signature = crypto.sign(this.HASH_ALGORITHM, Buffer.from(data, 'utf8'), {
      key: privateKey,
      passphrase
    })

    return {
      data,
      signature: signature.toString('base64'),
      keyId,
      algorithm: `${this.HASH_ALGORITHM}-RSA`,
      timestamp: Date.now()
    }
  }

  /**
   * Verify signature with public key
   */
  static async verify(signedData: SignedData, publicKey: string): Promise<boolean> {
    try {
      return crypto.verify(
        this.HASH_ALGORITHM,
        Buffer.from(signedData.data, 'utf8'),
        publicKey,
        Buffer.from(signedData.signature, 'base64')
      )
    } catch (error) {
      return false
    }
  }

  /**
   * Generate key exchange parameters for Diffie-Hellman
   */
  static generateKeyExchange() {
    const dh = crypto.createDiffieHellman(2048)
    dh.generateKeys()

    return {
      publicKey: dh.getPublicKey('base64'),
      privateKey: dh.getPrivateKey('base64'),
      prime: dh.getPrime('base64'),
      generator: dh.getGenerator('base64')
    }
  }

  /**
   * Compute shared secret from key exchange
   */
  static computeSharedSecret(privateKey: string, otherPublicKey: string, prime: string, generator: string): string {
    const dh = crypto.createDiffieHellman(Buffer.from(prime, 'base64'), Buffer.from(generator, 'base64'))
    dh.setPrivateKey(Buffer.from(privateKey, 'base64'))

    return dh.computeSecret(Buffer.from(otherPublicKey, 'base64'), null, 'base64')
  }

  /**
   * Derive key passphrase from keyId and system secrets
   */
  private static deriveKeyPassphrase(keyId: string): string {
    const masterSecret = process.env.MASTER_SECRET || 'default-secret'
    const salt = keyId.slice(0, 16) // Use part of keyId as salt

    return crypto.pbkdf2Sync(masterSecret, salt, 100000, 32, 'sha256').toString('base64')
  }

  /**
   * Rotate key pair (generate new keys while keeping old ones for decryption)
   */
  static async rotateKeys(oldKeyPair: KeyPair): Promise<KeyPair> {
    const newKeyPair = oldKeyPair.algorithm === 'RSA' ? await this.generateRSAKeyPair() : await this.generateECKeyPair()

    // In production, you would store both keys with different statuses
    // Old keys: status = 'decrypt-only'
    // New keys: status = 'active'

    return newKeyPair
  }

  /**
   * Hash sensitive data for comparison without storing plaintext
   */
  static hashSensitiveData(data: string, salt?: string): string {
    const actualSalt = salt || crypto.randomBytes(16).toString('base64')
    const hash = crypto.pbkdf2Sync(data, actualSalt, 100000, 64, 'sha256')
    return `${actualSalt}:${hash.toString('base64')}`
  }

  /**
   * Verify hashed sensitive data
   */
  static verifySensitiveData(data: string, hashedData: string): boolean {
    const [salt, hash] = hashedData.split(':')
    const newHash = crypto.pbkdf2Sync(data, salt, 100000, 64, 'sha256')
    return hash === newHash.toString('base64')
  }
}

/**
 * Utility for managing encryption keys in production
 */
export class KeyManager {
  /**
   * Generate master key for application-level encryption
   */
  static generateMasterKey(): string {
    return crypto.randomBytes(32).toString('base64') // 256-bit key
  }

  /**
   * Derive application-specific keys from master key
   */
  static deriveApplicationKey(masterKey: string, purpose: string, salt?: string): string {
    const actualSalt = salt || crypto.randomBytes(16).toString('base64')
    const derivedKey = crypto.pbkdf2Sync(masterKey, `${purpose}:${actualSalt}`, 100000, 32, 'sha256')
    return derivedKey.toString('base64')
  }

  /**
   * Encrypt key material for storage
   */
  static encryptKeyForStorage(keyData: string, masterKey: string): string {
    const iv = crypto.randomBytes(16)
    const key = Buffer.from(masterKey, 'base64')
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv)

    let encrypted = cipher.update(keyData, 'utf8', 'base64')
    encrypted += cipher.final('base64')
    const authTag = cipher.getAuthTag()

    const combined = Buffer.concat([iv, authTag, Buffer.from(encrypted, 'base64')])
    return combined.toString('base64')
  }

  /**
   * Decrypt key material from storage
   */
  static decryptKeyFromStorage(encryptedKey: string, masterKey: string): string {
    const combined = Buffer.from(encryptedKey, 'base64')
    const iv = combined.subarray(0, 16)
    const authTag = combined.subarray(16, 32)
    const encrypted = combined.subarray(32)

    const key = Buffer.from(masterKey, 'base64')
    const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv)
    decipher.setAuthTag(authTag)

    const decryptedBuffer = decipher.update(encrypted)
    const finalBuffer = decipher.final()
    const decrypted = Buffer.concat([decryptedBuffer, finalBuffer]).toString('utf8')

    return decrypted
  }
}
