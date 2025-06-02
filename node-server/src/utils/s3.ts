import fs from 'fs'
import { tmpdir } from 'os'
import path from 'path'
import { Readable } from 'stream'
import { configs } from '@/configs'
import { s3 } from '@/configs/s3.config'
import { BadRequestError, NotFoundError } from '@/core/error.response'
import { GetObjectCommand } from '@aws-sdk/client-s3'

export const downloadFile = async ({ key }: { key: string }) => {
  const params = {
    Bucket: configs.s3.bucket,
    Key: key
  }

  const command = new GetObjectCommand(params)
  const { Body } = (await s3.send(command)) as { Body: Readable }

  if (!Body) {
    throw new NotFoundError('File not found')
  }

  const directoryPath = path.join(tmpdir(), key)
  await fs.promises.mkdir(path.dirname(directoryPath), { recursive: true })

  const fileStream = fs.createWriteStream(directoryPath)

  await new Promise((resolve, reject) => {
    Body.pipe(fileStream)
      .on('error', (err) => {
        console.error('Error writing file:', err)
        reject(new BadRequestError('Failed to download the file.'))
      })
      .on('finish', () => {
        console.log(`File has been saved to ${directoryPath}`)
        resolve(directoryPath)
      })
  })

  return directoryPath
}
