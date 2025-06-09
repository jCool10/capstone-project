"use client"

import { useCallback, useState } from "react"
import { useRouter } from "next/navigation"
import { embedFiles } from "@/apis/files"
import { useAuth } from "@/context/AuthContext"
import { middleTruncate } from "@/utils"
import { useMutation } from "@tanstack/react-query"
import { Folder } from "lucide-react"
import { v4 } from "uuid"

import { toast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import FileUploader, { FileWithMetadata } from "@/components/FileUploader"

export default function CreatePage() {
  const { isAuthenticated } = useAuth()
  const router = useRouter()

  if (!isAuthenticated) {
    router.push("/login")
    return null
  }

  const [files, setFiles] = useState<FileWithMetadata[]>([])
  const [workspaceName, setWorkspaceName] = useState("New workspace")
  const [isLoading, setIsLoading] = useState(false)

  const embedFilesMutation = useMutation({
    mutationFn: embedFiles,
  })

  const saveAndEmbed = async () => {
    const selectedFiles = files.filter((file) => file.selected)

    if (selectedFiles.length === 0) {
      toast({
        title: "No files selected",
        description: "Please select at least one file to create a workspace",
        variant: "destructive",
      })
      return
    }

    if (!workspaceName.trim()) {
      toast({
        title: "Workspace name required",
        description: "Please enter a name for your workspace",
        variant: "destructive",
      })
      return
    }

    setIsLoading(true)
    const formData = new FormData()

    selectedFiles.forEach((file) => {
      formData.append("files", file)
    })

    formData.append("workspaceName", workspaceName)

    embedFilesMutation.mutate(formData, {
      onSuccess: (data) => {
        if (typeof window !== "undefined") {
          sessionStorage.setItem("createdWorkspace", "true")
        }

        toast({
          title: "Workspace created",
          description: "Workspace created successfully",
        })

        router.push(`/workspace/${data.slug}`)
      },
      onError: (error) => {
        console.log(error)
        setIsLoading(false)
        toast({
          title: "Workspace creation failed",
          description: error.message,
          variant: "destructive",
        })
      },
    })
  }

  return (
    <div className="w-full max-w-4xl min-w-[320px] mx-auto p-4">
      <Card className="border shadow-sm w-full">
        <CardHeader className="bg-muted/30 pb-4">
          <CardTitle className="flex items-center gap-2">
            <Folder className="h-5 w-5 text-primary" />
            Create New Workspace
          </CardTitle>
        </CardHeader>

        <CardContent className="pt-6 px-6">
          <div className="space-y-6">
            {/* Workspace Name Section */}
            <div>
              <label htmlFor="workspace-name" className="text-sm font-medium mb-2 block">
                Workspace Name
              </label>
              <Input
                id="workspace-name"
                placeholder="Enter workspace name"
                value={workspaceName}
                onChange={(event) => setWorkspaceName(event.target.value)}
                className="max-w-md"
              />
            </div>

            {/* Upload Section */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-sm font-medium">Upload Documents</h3>
              </div>

              <FileUploader
                files={files}
                setFiles={setFiles}
                dropzoneText={{
                  title: "Drag & drop files here",
                  subtitle: "or click to browse your device",
                  dragActive: "Drop the files here",
                }}
              />
            </div>
          </div>
        </CardContent>

        <CardFooter className="bg-muted/30 px-6 py-4 flex justify-end">
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => router.push("/")}>
              Cancel
            </Button>
            <Button
              onClick={saveAndEmbed}
              disabled={isLoading || files.filter((f) => f.selected).length === 0}
              className="min-w-[120px]"
            >
              {isLoading ? (
                <>
                  <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Creating...
                </>
              ) : (
                "Create Workspace"
              )}
            </Button>
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}
