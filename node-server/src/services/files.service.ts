import { Request } from 'express'
import workspaceRepo from '@/repositories/worksapce.repo'
import { downloadFile } from '@/utils/s3'
import messageRepo from '@/repositories/message.repo'
import axios from 'axios'
import { BadRequestError, NotFoundError } from '@/core/error.response'
import { MessageType } from '@/models/message.model'

const LLM_API = 'http://localhost:8080'

class filesService {
  async embedFiles(req: Request) {
    const files = req.files
    const { workspaceName } = req.body
    const { user } = req.user

    if (!files || !workspaceName) {
      throw new BadRequestError('Missing required fields')
    }

    const filePaths = await Promise.all(files.map((file) => downloadFile({ key: file.key })))

    const newWorkspace = await workspaceRepo.create({
      name: workspaceName,
      user: user._id,
      filePaths,
      fileKeys: files.map((file) => file.key)
    })

    if (!newWorkspace) {
      throw new BadRequestError('Failed to create workspace')
    }

    const result = await axios.post(`${LLM_API}/embed`, {
      file_paths: filePaths,
      collection_name: newWorkspace.slug
    })

    if (result.data.success) {
      await workspaceRepo.updateOne({ _id: newWorkspace._id }, { isEmbedded: true })
    } else {
      throw new BadRequestError(result.data.message)
    }

    return {
      slug: newWorkspace.slug
    }
  }

  async reEmbedFiles(req: Request) {
    const { workspaceSlug } = req.body

    const workspace = await workspaceRepo.findBySlug(workspaceSlug)

    if (!workspace) {
      throw new NotFoundError('Workspace not found')
    }

    const result = await axios.post(`${LLM_API}/embed`, {
      file_paths: workspace.filePaths,
      collection_name: workspaceSlug
    })

    if (result.data.success) {
      await workspaceRepo.updateOne({ _id: workspace._id }, { isEmbedded: true })
    } else {
      throw new BadRequestError(result.data.message)
    }

    return {
      workspace,
      filePaths: workspace.filePaths,
      embedding: result.data
    }
  }

  async getWorkspaces(req: Request) {
    const { user } = req.user

    const workspaces = await workspaceRepo.findByUserId(user._id)

    return workspaces
  }

  async getMessages(req: Request) {
    const { workspaceSlug } = req.params
    const messages = await messageRepo.getMessages(workspaceSlug)
    return messages
  }

  async chat(req: Request) {
    const { workspaceId } = req.params
    const { question } = req.body

    return {}
  }

  async getWorkspace(req: Request) {
    const { workspaceSlug } = req.params
    const workspace = await workspaceRepo.findBySlug(workspaceSlug)

    if (!workspace) {
      throw new NotFoundError('Workspace not found')
    }

    const messages = await messageRepo.getMessages(workspaceSlug)

    return {
      workspace,
      messages
    }
  }

  async queryWorkspace(req: Request) {
    const { workspaceSlug } = req.params
    const { question } = req.body
    const messages = await messageRepo.getMessages(workspaceSlug, 3)

    const query = await axios.post(`${LLM_API}/query`, {
      query: question,
      collection_name: workspaceSlug,
      history: messages.flatMap((message) => message.messages.map((msg) => msg.message))
    })

    console.log(query.data)

    const responseData = query.data

    // Extract source documents from Python server response
    const sourceDocuments =
      responseData.data?.docs.map((doc: any) => {
        console.log(doc)
        return doc.text || doc.id || JSON.stringify(doc)
      }) || []

    await messageRepo.findOneAndUpdate(workspaceSlug, question, responseData.data?.response, sourceDocuments)

    // Format response for frontend
    return {
      ...responseData,
      data: {
        response: responseData.data?.response || responseData.message || '',
        sourceDocuments: sourceDocuments
      }
    }
  }
}

export default filesService
