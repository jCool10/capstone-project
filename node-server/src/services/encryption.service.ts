import { Types } from 'mongoose'
import { UserKeyPairModel, IUserKeyPair } from '@/models/userKeyPair.model'
import { AsymmetricCrypto, KeyManager, KeyPair, EncryptedData, SignedData } from '@/utils/encryption.util'
import User from '@/models/user.model'
import { InternalServerError, NotFoundError } from '@/core/error.response'
import crypto from 'crypto'

export class EncryptionService {
  private static readonly MASTER_KEY = process.env.MASTER_ENCRYPTION_KEY || KeyManager.generateMasterKey()

  /**
   * Initialize encryption for a new user
   */
  async initializeUserEncryption(user: User): Promise<IUserKeyPair> {
    try {
      // Generate RSA key pair for the user
      const keyPair = await AsymmetricCrypto.generateRSAKeyPair()

      // Encrypt private key for storage
      const encryptedPrivateKey = KeyManager.encryptKeyForStorage(keyPair.privateKey, EncryptionService.MASTER_KEY)

      // Store in database
      const userKeyPair = new UserKeyPairModel({
        user: user._id,
        keyId: keyPair.keyId,
        encryptedPrivateKey,
        publicKey: keyPair.publicKey,
        algorithm: keyPair.algorithm,
        keySize: keyPair.keySize,
        status: 'active',
        version: 1,
        purpose: 'both'
      })

      return await userKeyPair.save()
    } catch (error) {
      throw new InternalServerError('Failed to initialize user encryption')
    }
  }

  /**
   * Get user's active key pair
   */
  async getUserKeyPair(
    userId: Types.ObjectId,
    purpose?: 'signing' | 'encryption' | 'both'
  ): Promise<IUserKeyPair | null> {
    const query: any = {
      user: userId,
      status: 'active',
      expiresAt: { $gt: new Date() }
    }

    if (purpose) {
      query.$or = [{ purpose: purpose }, { purpose: 'both' }]
    }

    return await UserKeyPairModel.findOne(query).sort({ version: -1 }).lean().exec()
  }

  /**
   * Get decrypted private key for user
   */
  async getDecryptedPrivateKey(userId: Types.ObjectId): Promise<string> {
    const keyPair = await this.getUserKeyPair(userId)

    if (!keyPair) {
      throw new NotFoundError('User encryption keys not found')
    }

    try {
      return KeyManager.decryptKeyFromStorage(keyPair.encryptedPrivateKey, EncryptionService.MASTER_KEY)
    } catch (error) {
      throw new InternalServerError('Failed to decrypt user private key')
    }
  }

  /**
   * Get private key with passphrase for user (for JWT signing)
   */
  async getPrivateKeyWithPassphrase(userId: Types.ObjectId): Promise<{ privateKey: string; passphrase: string }> {
    const keyPair = await this.getUserKeyPair(userId)

    if (!keyPair) {
      throw new NotFoundError('User encryption keys not found')
    }

    try {
      const encryptedPrivateKey = KeyManager.decryptKeyFromStorage(
        keyPair.encryptedPrivateKey,
        EncryptionService.MASTER_KEY
      )

      // Derive the same passphrase used during key generation
      const passphrase = this.deriveKeyPassphrase(keyPair.keyId)

      return {
        privateKey: encryptedPrivateKey,
        passphrase
      }
    } catch (error) {
      throw new InternalServerError('Failed to get user private key')
    }
  }

  /**
   * Derive key passphrase from keyId (same as AsymmetricCrypto)
   */
  private deriveKeyPassphrase(keyId: string): string {
    const masterSecret = process.env.MASTER_SECRET || 'default-secret'
    const salt = keyId.slice(0, 16)

    return crypto.pbkdf2Sync(masterSecret, salt, 100000, 32, 'sha256').toString('base64')
  }

  /**
   * Encrypt data for a specific user
   */
  async encryptForUser(data: string, userId: Types.ObjectId): Promise<EncryptedData> {
    const keyPair = await this.getUserKeyPair(userId, 'encryption')

    if (!keyPair) {
      throw new NotFoundError('User encryption keys not found')
    }

    return await AsymmetricCrypto.encrypt(data, keyPair.publicKey, keyPair.keyId)
  }

  /**
   * Decrypt data for a specific user
   */
  async decryptForUser(encryptedData: EncryptedData, userId: Types.ObjectId): Promise<string> {
    // Find the specific key used for encryption
    const keyPair = await UserKeyPairModel.findOne({
      user: userId,
      keyId: encryptedData.keyId,
      status: { $in: ['active', 'decrypt-only'] }
    })
      .lean()
      .exec()

    if (!keyPair) {
      throw new NotFoundError('Encryption key not found or revoked')
    }

    const privateKey = KeyManager.decryptKeyFromStorage(keyPair.encryptedPrivateKey, EncryptionService.MASTER_KEY)

    return await AsymmetricCrypto.decrypt(encryptedData, privateKey)
  }

  /**
   * Sign data with user's private key
   */
  async signData(data: string, userId: Types.ObjectId): Promise<SignedData> {
    const keyPair = await this.getUserKeyPair(userId, 'signing')

    if (!keyPair) {
      throw new NotFoundError('User signing keys not found')
    }

    const privateKey = KeyManager.decryptKeyFromStorage(keyPair.encryptedPrivateKey, EncryptionService.MASTER_KEY)

    return await AsymmetricCrypto.sign(data, privateKey, keyPair.keyId)
  }

  /**
   * Verify signed data
   */
  async verifySignature(signedData: SignedData, userId: Types.ObjectId): Promise<boolean> {
    const keyPair = await UserKeyPairModel.findOne({
      user: userId,
      keyId: signedData.keyId,
      status: { $in: ['active', 'decrypt-only'] }
    })
      .lean()
      .exec()

    if (!keyPair) {
      return false
    }

    return await AsymmetricCrypto.verify(signedData, keyPair.publicKey)
  }

  /**
   * Rotate user's keys (generate new keys while keeping old ones for decryption)
   */
  async rotateUserKeys(userId: Types.ObjectId): Promise<IUserKeyPair> {
    try {
      // Mark existing keys as decrypt-only
      await UserKeyPairModel.updateMany({ user: userId, status: 'active' }, { status: 'decrypt-only' })

      // Get latest version
      const latestKey = await UserKeyPairModel.findOne({ user: userId }).sort({ version: -1 }).lean().exec()

      const nextVersion = (latestKey?.version || 0) + 1

      // Generate new key pair
      const keyPair = await AsymmetricCrypto.generateRSAKeyPair()

      // Encrypt private key for storage
      const encryptedPrivateKey = KeyManager.encryptKeyForStorage(keyPair.privateKey, EncryptionService.MASTER_KEY)

      // Store new key pair
      const newUserKeyPair = new UserKeyPairModel({
        user: userId,
        keyId: keyPair.keyId,
        encryptedPrivateKey,
        publicKey: keyPair.publicKey,
        algorithm: keyPair.algorithm,
        keySize: keyPair.keySize,
        status: 'active',
        version: nextVersion,
        purpose: 'both'
      })

      return await newUserKeyPair.save()
    } catch (error) {
      throw new InternalServerError('Failed to rotate user keys')
    }
  }

  /**
   * Revoke user's keys (mark as revoked, no longer usable)
   */
  async revokeUserKeys(userId: Types.ObjectId, keyId?: string): Promise<void> {
    const query: any = { user: userId }
    if (keyId) {
      query.keyId = keyId
    }

    await UserKeyPairModel.updateMany(query, { status: 'revoked' })
  }

  /**
   * Get user's public key for external use (e.g., sharing with other users)
   */
  async getUserPublicKey(userId: Types.ObjectId): Promise<string | null> {
    const keyPair = await this.getUserKeyPair(userId)
    return keyPair?.publicKey || null
  }

  /**
   * Encrypt data with multiple recipients
   */
  async encryptForMultipleUsers(
    data: string,
    userIds: Types.ObjectId[]
  ): Promise<{
    [userId: string]: EncryptedData
  }> {
    const results: { [userId: string]: EncryptedData } = {}

    for (const userId of userIds) {
      try {
        results[userId.toString()] = await this.encryptForUser(data, userId)
      } catch (error) {
        // Skip users without valid encryption keys
        console.warn(`Failed to encrypt for user ${userId}:`, error)
      }
    }

    return results
  }

  /**
   * Clean up expired keys
   */
  async cleanupExpiredKeys(): Promise<void> {
    await UserKeyPairModel.deleteMany({
      expiresAt: { $lt: new Date() },
      status: { $in: ['revoked', 'decrypt-only'] }
    })
  }

  /**
   * Get key statistics for monitoring
   */
  async getKeyStatistics(): Promise<{
    totalUsers: number
    activeKeys: number
    expiringSoon: number
    revokedKeys: number
  }> {
    const sevenDaysFromNow = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)

    const [totalUsers, activeKeys, expiringSoon, revokedKeys] = await Promise.all([
      UserKeyPairModel.distinct('user')
        .exec()
        .then((users) => users.length),
      UserKeyPairModel.countDocuments({ status: 'active' }),
      UserKeyPairModel.countDocuments({
        status: 'active',
        expiresAt: { $lt: sevenDaysFromNow }
      }),
      UserKeyPairModel.countDocuments({ status: 'revoked' })
    ])

    return {
      totalUsers,
      activeKeys,
      expiringSoon,
      revokedKeys
    }
  }
}
