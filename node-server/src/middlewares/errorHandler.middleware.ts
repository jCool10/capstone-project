import { NextFunction, Request, Response } from 'express'

const errorHandler = (error: any, req: Request, res: Response, next: NextFunction) => {
  const statusCode = error.status || 500

  return res.status(statusCode).json({
    status: statusCode,
    message: error.message || 'Internal Server Error',
    errors: error.errors || [],
    stack: error.stack
  })
}

export { errorHandler }
