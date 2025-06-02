"use client"

import { useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { CheckedState } from "@radix-ui/react-checkbox"
import axios from "axios"
import { useForm } from "react-hook-form"
import { z } from "zod"

import ModalWrapper from "."
import FileUploader, { FileWithMetadata } from "../FileUploader"
import { Button } from "../ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "../ui/card"
import { Input } from "../ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"

interface UploadModalProps {
  isOpen: boolean
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>
}

export default function UploadModal({ isOpen, setIsOpen }: UploadModalProps) {
  const [files, setFiles] = useState<FileWithMetadata[]>([])
  const [model, setModel] = useState("openai")
  const [workspaceName, setWorkspaceName] = useState("New workspace")
  const [isLoading, setIsLoading] = useState(false)

  const saveAndEmbed = async () => {
    const selectedFiles = files.filter((file) => file.selected)

    if (selectedFiles.length === 0) {
      return
    }

    setIsLoading(true)
    const formData = new FormData()

    selectedFiles.forEach((file) => {
      formData.append("files", file)
    })

    formData.append("workspaceName", workspaceName)
    formData.append("model", model)

    try {
      const res = await axios.post("http://localhost:5000/api/v1/uploadFiles", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      })
      setIsOpen(false)
    } catch (error) {
      console.error("Upload error:", error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <ModalWrapper isOpen={isOpen} onClose={() => setIsOpen(false)}>
      <Card className="border-none flex flex-col ">
        <CardHeader>
          <CardTitle>New workspace</CardTitle>
        </CardHeader>
        <CardContent className="grid h-fit gap-4 grid-cols-2">
          <div className="col-span-2 flex gap-2">
            <Input
              defaultValue={workspaceName}
              onChange={(event) => {
                setWorkspaceName(event.target.value)
              }}
              type="text"
              id="name"
            />
            <Select
              onValueChange={(value) => {
                setModel(value)
              }}
              defaultValue={model}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Model" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="openai">Open AI</SelectItem>
                <SelectItem value="huggingface">Hugging Face</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="col-span-1 ">
            <CardTitle className="text-lg mb-4">File list</CardTitle>

            <div className="flex flex-col justify-between">
              <div className="h-[40vh] overflow-auto">
                <FileUploader
                  files={files}
                  setFiles={setFiles}
                  dropzoneText={{
                    title: "Click to upload or drag and drop",
                    subtitle: "supports text files, csv's, spreadsheets, and more!",
                  }}
                />
              </div>
            </div>
          </div>

          <div className="col-span-1">{/* Placeholder for additional content */}</div>
        </CardContent>
        <CardFooter>
          <Button onClick={saveAndEmbed} disabled={isLoading || files.filter((f) => f.selected).length === 0}>
            {isLoading ? (
              <>
                <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                Uploading...
              </>
            ) : (
              "Save and Embed"
            )}
          </Button>
        </CardFooter>
      </Card>
    </ModalWrapper>
  )
}
