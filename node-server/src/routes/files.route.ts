import { Router } from 'express'
import { filesController } from '@/controllers/files.controller'
import catchAsync from '@/helpers/cathAsync'
import { upload } from '@/middlewares/multer.middleware'

export const filesRouter = (router: Router) => {
  const FilesController = new filesController()

  router.use('/files', router)

  router.post('/embed', upload.array('files', 10), catchAsync(FilesController.embedFiles))
  router.get('/workspaces', catchAsync(FilesController.getWorkspaces))
  router.get('/workspace/:workspaceSlug', catchAsync(FilesController.getWorkspace))
  router.post('/workspace/:workspaceSlug/query', catchAsync(FilesController.queryWorkspace))
}
