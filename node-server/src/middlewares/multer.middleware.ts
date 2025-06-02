import { configs } from '@/configs'
import { s3 } from '@/configs/s3.config'
import multer from 'multer'
import multerS3 from 'multer-s3'

const storage = multerS3({
  s3,
  bucket: configs.s3.bucket,
  metadata: (req, file, cb) => {
    console.log('file', file)
    cb(null, { fieldName: file.fieldname })
  },
  key: (req, file, cb) => {
    console.log('file', file)

    cb(null, `${Date.now()}-${file.originalname}`)
  }
})

export const upload = multer({ storage })
