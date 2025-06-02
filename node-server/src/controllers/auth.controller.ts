import { SuccessResponse } from '@/core/success.response'
import { authService } from '@/services/auth.service'
import { Request, Response } from 'express'

export class authController {
  authService: authService

  constructor() {
    this.authService = new authService()
  }

  login = async (req: Request, res: Response) => {
    new SuccessResponse({
      message: 'Login successfully',
      data: await this.authService.login(req)
    }).send(res)
  }

  register = async (req: Request, res: Response) => {
    new SuccessResponse({
      message: 'Register successfully',
      data: await this.authService.register(req)
    }).send(res)
  }

  logout = async (req: Request, res: Response) => {
    new SuccessResponse({
      message: 'Logout successfully',
      data: await this.authService.logout(req)
    }).send(res)
  }

  refreshToken = async (req: Request, res: Response) => {
    new SuccessResponse({
      message: 'Refresh token successfully',
      data: await this.authService.refreshToken(req)
    }).send(res)
  }
}
