import filesService from '@/services/files.service'
import { Request, Response } from 'express'
import { SuccessResponse } from '@/core/success.response'

export class filesController {
  filesService: filesService

  constructor() {
    this.filesService = new filesService()
  }

  embedFiles = async (req: Request, res: Response) => {
    new SuccessResponse({
      message: 'Files embedded successfully',
      data: await this.filesService.embedFiles(req)
    }).send(res)
  }

  getWorkspaces = async (req: Request, res: Response) => {
    new SuccessResponse({
      message: 'Workspaces fetched successfully',
      data: await this.filesService.getWorkspaces(req)
    }).send(res)
  }

  getWorkspace = async (req: Request, res: Response) => {
    new SuccessResponse({
      message: 'Workspace fetched successfully',
      data: await this.filesService.getWorkspace(req)
    }).send(res)
  }

  queryWorkspace = async (req: Request, res: Response) => {
    new SuccessResponse({
      message: 'Workspace queried successfully',
      data: await this.filesService.queryWorkspace(req)
    }).send(res)
  }
}
