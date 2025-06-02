import * as dotenv from 'dotenv'
dotenv.config()

export const configs = {
  app: {
    port: process.env.PORT || 8000,
    env: process.env.NODE_ENV,
    timeShutdown: process.env.TIME_SHUTDOWN || process.env.NODE_ENV === 'production' ? 15000 : 1000
  },
  s3: {
    region: process.env.AWS_REGION,
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID || '',
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || ''
    },
    bucket: process.env.AWS_BUCKET || ''
  },
  openai: {
    apiKey: process.env.OPEN_AI_KEY || ''
  },
  huggingFace: {
    apiKey: process.env.HUGGINGFACEHUB_API_KEY || ''
  },
  redis: {
    url: process.env.REDIS_URL || ''
  },
  mongodb: {
    name: process.env.DB_NAME || '',
    host: process.env.DB_HOST || '',
    port: process.env.DB_PORT || '',
    user: process.env.DB_USER || '',
    password: process.env.DB_USER_PWD || '',
    minPoolSize: parseInt(process.env.DB_MIN_POOL_SIZE || '5'),
    maxPoolSize: parseInt(process.env.DB_MAX_POOL_SIZE || '10'),
    url: process.env.DB_URL || ''
  },
  firebase: {
    credential: JSON.parse(process.env.FIREBASE_CREDENTIAL || '{}')
  },
  tokenInfo: {
    accessTokenValidity: parseInt(process.env.ACCESS_TOKEN_VALIDITY_SEC || '0'),
    refreshTokenValidity: parseInt(process.env.REFRESH_TOKEN_VALIDITY_SEC || '0'),
    issuer: process.env.TOKEN_ISSUER || '',
    audience: process.env.TOKEN_AUDIENCE || ''
  }
}
