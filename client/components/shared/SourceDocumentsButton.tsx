"use client"

import React from "react"
import { FileText } from "lucide-react"

import { SourceDocument } from "@/types/index"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

interface SourceDocumentsButtonProps {
  sourceDocuments: SourceDocument[]
  onClick: () => void
}

export default function SourceDocumentsButton({ sourceDocuments, onClick }: SourceDocumentsButtonProps) {
  if (!sourceDocuments || sourceDocuments.length === 0) {
    return null
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={onClick}
      className="h-auto p-2 mt-2 text-xs text-muted-foreground hover:text-foreground flex items-center gap-1.5"
    >
      <FileText className="h-3 w-3" />
      <span>Tài liệu liên quan</span>
      <Badge variant="secondary" className="h-4 px-1.5 text-xs">
        {sourceDocuments.length}
      </Badge>
    </Button>
  )
}
