'use strict'

import { createServer } from 'http'
import express from 'express'

import expressConfig from './configs/express.config'
import logger from './configs/logger.config'
import { configs } from './configs'
import { apiRouter } from './routes'

import { instanceMongoDb } from './configs/mongoose.config'

instanceMongoDb.connect()

const PORT = configs.app.port

const app = express()
const router = express.Router()
const server = createServer(app)

expressConfig(app)

apiRouter(app, router)

server.listen(PORT, () => {
  logger.info(`Express server listening on ${PORT}, in ${app.get('env')} mode`)
})
