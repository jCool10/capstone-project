"use client"

import React, { Fragment, useEffect, useRef, useState } from "react"
import { useParams } from "next/navigation"
import { getWorkspace, queryWorkspace } from "@/apis/files"
import { IMessage, IWorkspace } from "@/types"
import { useMutation, useQuery } from "@tanstack/react-query"
import { Bot, Edit, FileText, Info, Plus, Send, Sparkles, Upload, User } from "lucide-react"

import { cn } from "@/lib/utils"
import { useToast } from "@/hooks/use-toast"
import { Avatar } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import FileUploader, { FileWithMetadata } from "@/components/FileUploader"

// Extend workspace type for this component
interface ExtendedWorkspace extends IWorkspace {
  isEmbedded?: boolean
  filePaths?: string[]
  createdAt?: string
  _id?: string
}

export default function WorkspacePage() {
  const { slug } = useParams()
  const [messages, setMessages] = useState<IMessage[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [showRightPanel, setShowRightPanel] = useState(false)
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [uploadFiles, setUploadFiles] = useState<FileWithMetadata[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()

  // Load workspace data
  const { data: workspace, refetch } = useQuery({
    queryKey: ["workspace", slug],
    queryFn: () => getWorkspace(slug as string),
  })

  // Access workspace with extended type
  const workspaceData = workspace?.workspace as ExtendedWorkspace

  const { mutate: queryWorkspaceMutation } = useMutation({
    mutationFn: (question: string) => queryWorkspace(slug as string, question),
    onSuccess: (data) => {
      console.log(data)
      setMessages((prev) => [
        ...prev,
        {
          content: data.data.response,
          role: "assistant",
          workspaceSlug: slug as string,
        },
      ])
    },
  })

  // File upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const response = await fetch(`/api/files/upload/${slug}`, {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.message || "Lỗi khi tải file")
      }

      return response.json()
    },
    onSuccess: () => {
      setShowUploadDialog(false)
      setUploadFiles([])
      refetch()
      toast({
        title: "Thành công",
        description: "File đã được thêm vào workspace",
      })
    },
    onError: (error: Error) => {
      toast({
        title: "Lỗi",
        description: error.message,
        variant: "destructive",
      })
    },
  })

  useEffect(() => {
    if (workspace) {
      setMessages(workspace.messages)
    }
  }, [workspace])

  // Scroll to bottom when messages change
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }

  // Auto scroll to bottom when new messages arrive
  useEffect(() => {
    // Add a small timeout to ensure DOM is updated
    const timeoutId = setTimeout(() => {
      scrollToBottom()
    }, 100)

    return () => clearTimeout(timeoutId)
  }, [messages, isLoading])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: IMessage = {
      content: input,
      role: "user",
      workspaceSlug: slug as string,
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    queryWorkspaceMutation(input)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleUpload = async () => {
    const selectedFiles = uploadFiles.filter((file) => file.selected)

    if (selectedFiles.length === 0) {
      toast({
        title: "Chưa chọn file",
        description: "Vui lòng chọn ít nhất một file để tải lên",
        variant: "destructive",
      })
      return
    }

    setIsUploading(true)
    try {
      const formData = new FormData()

      selectedFiles.forEach((file) => {
        formData.append("files", file)
      })

      formData.append("workspaceSlug", slug as string)

      uploadMutation.mutate(formData)
    } catch (error) {
      console.error("Error uploading files:", error)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col border border-outline rounded-xl overflow-hidden shadow-sm mx-4 my-2 relative">
      {/* Header */}
      <div className="px-4 py-3 border-b bg-muted/30 flex justify-between items-center">
        <h2 className="text-lg font-medium">Workspace: {workspace?.workspace?.name || slug}</h2>
        <div className="flex gap-2">
          <Button
            variant={showRightPanel ? "secondary" : "ghost"}
            size="icon"
            onClick={() => setShowRightPanel(!showRightPanel)}
            className="rounded-full"
            aria-label="Toggle Information Panel"
          >
            <Info className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {/* Main Content Area - Flexbox container */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Area - Flex grow with ratio */}
        <div
          className={cn(
            "transition-all duration-300 ease-in-out overflow-hidden",
            showRightPanel ? "w-[60%]" : "w-full"
          )}
        >
          <ScrollArea className="h-full">
            <div className="space-y-6 p-4 max-w-3xl mx-auto">
              {messages.length === 0 && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <Sparkles className="mx-auto h-12 w-12 text-primary/50" />
                    <h3 className="mt-4 text-xl font-medium">Chào mừng đến với AI Chat!</h3>
                    <p className="mt-2 text-sm text-muted-foreground">
                      Bắt đầu cuộc trò chuyện bằng cách gửi tin nhắn hoặc tải lên tài liệu của bạn.
                    </p>
                  </div>
                </div>
              )}

              {messages.map((message) => (
                <div key={message._id} className="flex items-start gap-4 flex-row">
                  <Avatar
                    className={cn("h-8 w-8 shrink-0", message.role === "assistant" ? "bg-muted" : "bg-primary/10")}
                  >
                    {message.role === "assistant" ? <Bot className="h-5 w-5" /> : <User className="h-5 w-5" />}
                  </Avatar>
                  <div className="flex-1">
                    <div className="font-medium mb-1">{message.role === "assistant" ? "AI Assistant" : "You"}</div>
                    <Card
                      className={cn(
                        "p-3 w-fit max-w-full",
                        message.role === "assistant" ? "bg-muted" : "bg-primary text-primary-foreground"
                      )}
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    </Card>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex items-start gap-4">
                  <Avatar className="h-8 w-8 bg-muted shrink-0">
                    <Bot className="h-5 w-5" />
                  </Avatar>
                  <div className="flex-1">
                    <div className="font-medium mb-1">AI Assistant</div>
                    <Card className="p-3 bg-muted w-fit">
                      <div className="flex gap-1">
                        <div className="h-2 w-2 animate-bounce rounded-full bg-primary"></div>
                        <div className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:0.2s]"></div>
                        <div className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:0.4s]"></div>
                      </div>
                    </Card>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
        </div>

        {/* Right Panel - Conditionally rendered */}
        {showRightPanel && (
          <div className="w-[40%] border-l h-full bg-background overflow-hidden">
            <div className="flex justify-between items-center p-3 border-b bg-muted/30">
              <h3 className="text-base font-medium">Thông tin workspace</h3>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowUploadDialog(true)}
                className="rounded-full h-8 w-8"
              >
                <Edit className="h-4 w-4" />
              </Button>
            </div>

            <ScrollArea className="h-[calc(100%-3.5rem)]">
              <div className="p-4 space-y-6">
                {/* Workspace Info Section */}
                <div>
                  <h4 className="text-sm font-medium mb-3">Chi tiết workspace</h4>
                  <div className="space-y-4">
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Tên</p>
                      <p className="text-sm font-medium">{workspaceData?.name}</p>
                    </div>

                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Trạng thái</p>
                      <Badge
                        variant={workspaceData?.isEmbedded ? "outline" : "destructive"}
                        className={workspaceData?.isEmbedded ? "bg-green-100 text-green-800 border-green-300" : ""}
                      >
                        {workspaceData?.isEmbedded ? "Đã nhúng" : "Chưa nhúng"}
                      </Badge>
                    </div>

                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Ngày tạo</p>
                      <p className="text-sm">
                        {workspaceData?.createdAt
                          ? new Date(workspaceData.createdAt as string).toLocaleString()
                          : "Không có thông tin"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Files Section */}
                <div className="pt-2 border-t">
                  <div className="flex justify-between items-center mb-3">
                    <h4 className="text-sm font-medium">Tài liệu</h4>
                    <Button variant="outline" size="sm" onClick={() => setShowUploadDialog(true)} className="h-7">
                      <Plus className="h-3 w-3 mr-1" />
                      Thêm tài liệu
                    </Button>
                  </div>

                  {workspaceData?.filePaths &&
                  Array.isArray(workspaceData.filePaths) &&
                  workspaceData.filePaths.length > 0 ? (
                    <div className="space-y-3">
                      <p className="text-sm text-muted-foreground mb-1">
                        Tổng số {workspaceData.filePaths.length} tài liệu
                      </p>
                      <div className="space-y-2 max-h-80 overflow-y-auto pr-2">
                        {workspaceData.filePaths.map((filePath: string, index: number) => {
                          const fileName = filePath.split("/").pop() || filePath
                          const fileExt = fileName.split(".").pop()?.toLowerCase() || ""

                          return (
                            <div
                              key={index}
                              className="flex items-start gap-2 p-2 rounded-md hover:bg-muted/50 transition-colors"
                            >
                              <div className="h-8 w-8 rounded-md bg-muted flex items-center justify-center flex-shrink-0">
                                <FileText className="h-4 w-4 text-foreground/70" />
                              </div>
                              <div className="overflow-hidden flex-1">
                                <p className="text-sm font-medium truncate">{fileName}</p>
                                <p className="text-xs text-muted-foreground">{fileExt.toUpperCase()}</p>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-6 text-center">
                      <FileText className="h-8 w-8 mb-2 text-muted-foreground" />
                      <p className="text-sm text-muted-foreground">Không có tài liệu nào</p>
                      <Button variant="outline" size="sm" onClick={() => setShowUploadDialog(true)} className="mt-3">
                        <Upload className="h-3 w-3 mr-1" />
                        Thêm tài liệu
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </ScrollArea>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t bg-background p-4">
        <div className="max-w-3xl mx-auto flex items-center gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Nhập tin nhắn của bạn..."
            className="flex-1"
          />
          <Button onClick={handleSend} disabled={!input.trim() || isLoading} className="shrink-0">
            <Send className="h-4 w-4 mr-1" />
            Gửi
          </Button>
        </div>
      </div>

      {/* File Upload Dialog */}
      <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Thêm file vào workspace</DialogTitle>
            <DialogDescription>
              Chọn file để thêm vào workspace hiện tại. Bạn có thể chọn nhiều file cùng lúc.
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <FileUploader
              files={uploadFiles}
              setFiles={setUploadFiles}
              dropzoneText={{
                title: "Kéo thả file vào đây hoặc nhấn để chọn",
                subtitle: "Hỗ trợ: PDF, DOCX, TXT, và các định dạng văn bản khác",
                dragActive: "Thả file vào đây",
              }}
              className="w-full max-w-4xl min-w-[320px] mx-auto p-4"
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setShowUploadDialog(false)}>
              Hủy
            </Button>
            <Button
              type="submit"
              onClick={handleUpload}
              disabled={uploadFiles.filter((f) => f.selected).length === 0 || isUploading}
            >
              {isUploading ? (
                <>
                  <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Đang tải lên...
                </>
              ) : (
                "Tải lên"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
