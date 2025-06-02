'use strict'

import { S3Client } from '@aws-sdk/client-s3'

import { configs } from '.'

export const s3 = new S3Client({
  region: configs.s3.region,
  credentials: {
    accessKeyId: configs.s3.credentials.accessKeyId,
    secretAccessKey: configs.s3.credentials.secretAccessKey
  }
})
