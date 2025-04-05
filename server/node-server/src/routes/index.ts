import { NotFoundError } from '@/core/error.response'
import { SuccessResponse } from '@/core/success.response'
import { errorHandler } from '@/middlewares/errorHandler.middleware'
import { Application, NextFunction, Request, Response, Router } from 'express'
import { authRouter } from './auth.route'
import { apikey } from '@/utils/auth.util'
export const apiRouter = (app: Application, router: Router) => {
  if (!app || !router) {
    throw new NotFoundError('Router not found')
  }

  app.get('/healthCheck', (req: Request, res: Response) => {
    new SuccessResponse({
      message: 'Health Check',
      data: {
        status: 'OK'
      }
    }).send(res)
  })

  // app.use(apikey)

  // app.use(permission(Permission.USER))

  app.use('/api', router)

  authRouter(router)

  app.use((error: Error, req: Request, res: Response, next: NextFunction) => {
    errorHandler(error, req, res, next)
  })
}
