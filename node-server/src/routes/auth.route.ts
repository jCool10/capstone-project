import { authController } from '@/controllers/auth.controller'
import catchAsync from '@/helpers/cathAsync'
import { authentication } from '@/utils/auth.util'
import { Router } from 'express'

export const authRouter = (router: Router) => {
  const AuthController = new authController()

  router.use('/auth', router)

  // Public routes (no authentication required)
  router.post('/register', catchAsync(AuthController.register))
  router.post('/login', catchAsync(AuthController.login))

  // Protected routes (authentication required)
  router.use(authentication)

  router.post('/logout', catchAsync(AuthController.logout))
  router.post('/refresh-token', catchAsync(AuthController.refreshToken))

  // Encryption and security routes
  router.post('/rotate-keys', catchAsync(AuthController.rotateKeys))
  router.get('/public-key/:userId', catchAsync(AuthController.getPublicKey))
  router.post('/encrypt', catchAsync(AuthController.encryptData))
  router.post('/decrypt', catchAsync(AuthController.decryptData))
}
