declare module 'pdfjs-dist/build/pdf' {
  const content: any
  export = content
}

declare namespace Express {
  interface Request {
    keyStore: any
    user: any
    refreshToken: string
    objKey: Record<string, unknown>

    keyStore: object
    user: {
      userId: string
    }
    refreshToken: string | string[]

    // apikey: {
    //   key: string
    //   status: boolean
    //   permissions: Array<string>
    // }
    // keyStore: object
    // user: {
    //   userId: string
    // }
    // refreshToken: string | string[]
  }

  interface Request {
    files: Array<S3Storage>
    file: S3Storage
    model: string
    workspaceName: string
  }
}
