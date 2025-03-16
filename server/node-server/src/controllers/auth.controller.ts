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

  signup = async (req: Request, res: Response) => {
    new SuccessResponse({
      message: 'Signup successfully',
      data: await this.authService.signup(req)
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
