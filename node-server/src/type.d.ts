declare namespace Express {
  interface Request {
    keyStore: keyStore
    user: User
    refreshToken: any
    objKey: any
    apiKey: ApiKey
    accessToken: string
    files: Array<S3Storage>
  }
}
