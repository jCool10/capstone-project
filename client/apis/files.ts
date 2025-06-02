import axiosInstance, { endpoints } from "@/utils/axios"

import { IMessage, IWorkspace } from "../types"

interface EmbedFilesPayload {
  workspaceName: string
  model: string
  files: File[]
}

export const embedFiles = async (payload: FormData) => {
  const response = await axiosInstance.post(endpoints.files.embed, payload, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  })
  return response.data
}

export const getWorkspaces = async () => {
  const response = await axiosInstance.get<IWorkspace[]>(endpoints.files.workspaces)
  return response.data
}

export const getWorkspace = async (workspaceSlug: string) => {
  const response = await axiosInstance.get<{
    workspace: IWorkspace
    messages: IMessage[]
  }>(endpoints.files.workspace(workspaceSlug))
  return response.data
}

export const queryWorkspace = async (workspaceSlug: string, question: string) => {
  const response = await axiosInstance.post(endpoints.files.query(workspaceSlug), {
    question,
  })
  return response.data
}
