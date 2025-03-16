import { authController } from '@/controllers/auth.controller'
import catchAsync from '@/helpers/cathAsync'
import { authentication } from '@/utils/auth.util'
import { Router } from 'express'

export const authRouter = (router: Router) => {
  const AuthController = new authController()

  router.use('/auth', router)

  router.post('/login', catchAsync(AuthController.login))
  router.post('/signup', catchAsync(AuthController.signup))

  router.use(authentication)

  router.post('/logout', catchAsync(AuthController.logout))
  router.post('/refresh-token', catchAsync(AuthController.refreshToken))
}
