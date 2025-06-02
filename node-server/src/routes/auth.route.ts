import { authController } from '@/controllers/auth.controller'
import catchAsync from '@/helpers/cathAsync'
import { authentication } from '@/utils/auth.util'
import { Router } from 'express'

export const authRouter = (router: Router) => {
  const AuthController = new authController()

  router.use('/auth', router)

  router.post('/register', catchAsync(AuthController.register))
  router.post('/login', catchAsync(AuthController.login))

  router.use(authentication)

  router.post('/logout', catchAsync(AuthController.logout))
  router.post('/refresh-token', catchAsync(AuthController.refreshToken))
}
