import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { config } from '@/config/global-config'

export interface FileWithMetadata extends File {
  selected?: boolean
}

interface UploadFilesParams {
  files: FileWithMetadata[]
  workspaceSlug: string
}

export const useFileUpload = (workspaceSlug: string) => {
  const [isUploading, setIsUploading] = useState(false)
  const queryClient = useQueryClient()

  const { mutateAsync: uploadFiles, ...uploadMutation } = useMutation({
    mutationFn: async ({ files }: UploadFilesParams) => {
      const selectedFiles = files.filter(file => file.selected)
      if (selectedFiles.length === 0) {
        throw new Error('No files selected')
      }

      setIsUploading(true)
      const formData = new FormData()

      selectedFiles.forEach(file => {
        formData.append('files', file)
      })

      formData.append('workspaceSlug', workspaceSlug)

      try {
        const response = await axios.post(`${config.api.baseURL}/api/v1/files/upload/${workspaceSlug}`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        return response.data
      } finally {
        setIsUploading(false)
      }
    },
    onSuccess: () => {
      // Invalidate workspace query to refetch data
      queryClient.invalidateQueries({
        queryKey: ['workspace', workspaceSlug]
      })
    }
  })

  return {
    isUploading,
    uploadFiles,
    ...uploadMutation
  }
} 