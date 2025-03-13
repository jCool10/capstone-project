'use strict'

import express, { Application } from 'express'
import bodyParser from 'body-parser'
import compression from 'compression'
import cors from 'cors'
import helmet from 'helmet'
import morgan from 'morgan'
import expressWinston from 'express-winston'
import multer from 'multer'
import { rateLimit } from 'express-rate-limit'
import Redis from 'ioredis'
import { configs } from '.'
import logger from './logger.config'

const url = configs.redis.url

const FILE_LIMIT = '3GB'
const upload = multer({ dest: 'uploads/' })

export default (app: Application) => {
  app.use(morgan('dev'))
  app.use(bodyParser.text({ limit: FILE_LIMIT }))
  app.use(bodyParser.json({ limit: FILE_LIMIT }))
  app.use(bodyParser.json())
  app.use(
    bodyParser.urlencoded({
      limit: FILE_LIMIT,
      extended: true
    })
  )
  app.use(
    compression({
      level: 6,
      threshold: 100 * 1024,
      filter: (req) => {
        return !req.headers['x-no-compress']
      }
    })
  )
  app.use(helmet())
  app.use(express.json())
  app.use(express.urlencoded({ extended: true }))

  app.post('/upload', upload.single('file'), (req, res) => {
    console.log('Upload File', req.file)
  })

  const whiteList = ['http://localhost:3000']
  app.use(
    cors({
      origin: whiteList,
      credentials: true
    })
  )

  app.use(
    expressWinston.logger({
      winstonInstance: logger,
      statusLevels: true
    })
  )

  return app
}
