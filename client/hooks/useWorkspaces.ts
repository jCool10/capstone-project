import { getWorkspace, getWorkspaces, queryWorkspace } from "@/apis/files"
import { IMessages, IWorkspace } from "@/types"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { useAuth } from "@/hooks/useAuth"

export const useWorkspaces = () => {
  const { isAuthenticated } = useAuth()

  console.log(isAuthenticated)

  const { data: workspaces, ...workspacesQuery } = useQuery({
    queryKey: ["workspaces"],
    queryFn: getWorkspaces,
    enabled: isAuthenticated,
  })

  return {
    workspaces: workspaces as IWorkspace[],
    ...workspacesQuery,
  }
}

export const useWorkspace = (slug: string) => {
  const queryClient = useQueryClient()

  const { data: workspace, ...workspaceQuery } = useQuery({
    queryKey: ["workspace", slug],
    queryFn: () => getWorkspace(slug),
    enabled: !!slug,
  })

  const { mutateAsync: query, ...queryMutation } = useMutation({
    mutationFn: (question: string) => queryWorkspace(slug, question),
    onSuccess: (data) => {
      // Update messages in cache
      queryClient.setQueryData(["workspace", slug], (old: any) => ({
        ...old,
        messages: [
          ...(old?.messages || []),
          {
            content: data.data.response,
            role: "assistant",
            workspaceSlug: slug,
          } as IMessages,
        ],
      }))
    },
  })

  return {
    workspace: workspace?.workspace as IWorkspace,
    query,
    ...workspaceQuery,
    ...queryMutation,
  }
}
