import { Response } from 'express'
import { ReasonPhrases, StatusCodes } from 'http-status-codes'

class SuccessResponse {
  [x: string]: any

  constructor({ message = '', status = StatusCodes.OK, data = {} }) {
    this.message = message
    this.status = status
    this.data = data
  }

  send(res: Response, headers = {}) {
    return res.status(this.status).set(headers).json(this)
  }
}

export { SuccessResponse }
