"use client"

import { useCallback } from "react"
import { CloudUpload, FileText, Trash2 } from "lucide-react"
import { useDropzone } from "react-dropzone"
import { v4 } from "uuid"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export interface FileWithMetadata extends File {
  id: string
  preview: string
  selected: boolean
  embedded: boolean
}

interface FileUploaderProps {
  files: FileWithMetadata[]
  setFiles: (files: FileWithMetadata[]) => void
  showFileList?: boolean
  className?: string
  dropzoneText?: {
    title: string
    subtitle: string
    dragActive?: string
  }
}

export default function FileUploader({
  files,
  setFiles,
  showFileList = true,
  className = "",
  dropzoneText = {
    title: "Drag & drop files here",
    subtitle: "or click to browse your device",
    dragActive: "Drop the files here",
  },
}: FileUploaderProps) {
  const onDrop = useCallback(
    (acceptedFiles: Array<File>) => {
      setFiles([
        ...files,
        ...acceptedFiles.map((file: File) =>
          Object.assign(file, {
            id: v4(),
            preview: URL.createObjectURL(file),
            selected: true,
            embedded: false,
          })
        ),
      ])
    },
    [files, setFiles]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop })

  const handleSelectAll = () => {
    const allSelected = files.every((file) => file.selected)
    const updatedFiles = files.map((file) => ({
      ...file,
      selected: !allSelected,
    }))
    setFiles(updatedFiles)
  }

  const deleteFile = (fileId: string) => {
    setFiles(files.filter((file) => file.id !== fileId))
  }

  const totalSize = files.reduce((acc, file) => acc + file.size, 0)
  const formatFileSize = (size: number) => {
    if (size < 1000) return `${size} B`
    if (size < 1000000) return `${(size / 1000).toFixed(2)} KB`
    return `${(size / 1000000).toFixed(2)} MB`
  }

  return (
    <div className={`w-full ${className}`}>
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-6 transition-colors w-full ${
          isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/30"
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center justify-center text-center">
          <CloudUpload size={36} className="text-muted-foreground mb-2" />
          <p className="font-medium">{isDragActive ? dropzoneText.dragActive : dropzoneText.title}</p>
          <p className="text-sm text-muted-foreground mt-1">{dropzoneText.subtitle}</p>
          <p className="text-xs text-muted-foreground mt-3">Supports text files, PDFs, CSVs, spreadsheets, and more</p>
        </div>
      </div>

      {showFileList && files.length > 0 && (
        <div className="mt-6 w-full">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-sm font-medium">Selected Documents</h3>
            <div className="flex items-center gap-4">
              <div className="text-xs text-muted-foreground">
                {files.length} files ({formatFileSize(totalSize)})
              </div>
              <Button variant="ghost" size="sm" onClick={handleSelectAll} className="h-8 text-xs">
                {files.every((file) => file.selected) ? "Unselect All" : "Select All"}
              </Button>
            </div>
          </div>

          <div className="border rounded-md overflow-hidden w-full">
            <Table className="w-full table-fixed">
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]">
                    <Checkbox
                      checked={files.length > 0 && files.every((file) => file.selected)}
                      onClick={handleSelectAll}
                    />
                  </TableHead>
                  <TableHead className="w-[calc(100%-320px)]">Document Name</TableHead>
                  <TableHead className="w-[100px]">Type</TableHead>
                  <TableHead className="w-[100px]">Size</TableHead>
                  <TableHead className="w-[70px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {files.map((file) => {
                  const fileExt = file.name.split(".").pop()?.toLowerCase() || ""

                  return (
                    <TableRow key={file.id}>
                      <TableCell>
                        <Checkbox
                          checked={file.selected}
                          onClick={() => {
                            const updatedFiles = files.map((f) =>
                              f.id === file.id ? { ...f, selected: !f.selected } : f
                            )
                            setFiles(updatedFiles)
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 overflow-hidden">
                          <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                          <span className="truncate">{file.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="uppercase text-xs text-muted-foreground">{fileExt}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">{formatFileSize(file.size)}</TableCell>
                      <TableCell>
                        <Button
                          onClick={() => deleteFile(file.id)}
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 size={14} />
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </div>
  )
}
