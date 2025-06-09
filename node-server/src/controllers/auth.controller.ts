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

  rotateKeys = async (req: Request, res: Response) => {
    new SuccessResponse({
      message: 'Keys rotated successfully',
      data: await this.authService.rotateKeys(req)
    }).send(res)
  }

  getPublicKey = async (req: Request, res: Response) => {
    new SuccessResponse({
      message: 'Public key retrieved successfully',
      data: await this.authService.getPublicKey(req)
    }).send(res)
  }

  encryptData = async (req: Request, res: Response) => {
    new SuccessResponse({
      message: 'Data encrypted successfully',
      data: await this.authService.encryptData(req)
    }).send(res)
  }

  decryptData = async (req: Request, res: Response) => {
    new SuccessResponse({
      message: 'Data decrypted successfully',
      data: await this.authService.decryptData(req)
    }).send(res)
  }
}
