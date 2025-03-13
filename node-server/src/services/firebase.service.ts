import admin from 'firebase-admin'

import { configs } from '@/configs'
import { Request } from 'express'
import logger from '@/configs/logger.config'

console.log('configs.firebase.credential', configs.firebase.credential)

export class firebaseService {
  constructor() {
    if (!admin.apps.length) {
      admin.initializeApp({
        credential: admin.credential.cert(configs.firebase.credential) // Use the service account credential
      })
    } else {
      logger.info('Firebase Admin SDK already initialized')
    }
  }

  getAccessToken = async () => {
    try {
      const accessToken = await admin.credential.applicationDefault().getAccessToken()
      return accessToken
    } catch (error) {
      logger.error('Error getting access token:', error)
    }
  }
}
