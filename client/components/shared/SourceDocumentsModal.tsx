"use client"

import React from "react"
import { FileText, Star, X } from "lucide-react"

import { SourceDocument } from "@/types/index"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"

interface SourceDocumentsModalProps {
  isOpen: boolean
  onClose: () => void
  sourceDocuments: SourceDocument[]
}

export default function SourceDocumentsModal({ isOpen, onClose, sourceDocuments }: SourceDocumentsModalProps) {
  console.log(sourceDocuments)

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Tài liệu liên quan ({sourceDocuments.length})
          </DialogTitle>
          <DialogDescription>Các đoạn văn từ tài liệu được sử dụng để trả lời câu hỏi của bạn</DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[60vh] pr-4">
          <div className="space-y-4">
            {sourceDocuments.map((doc, index) => (
              <Card key={doc.id || index} className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      #{index + 1}
                    </Badge>
                  </div>
                </div>

                <div className="text-sm leading-relaxed">
                  <p className="whitespace-pre-wrap">{doc.text}</p>
                </div>
              </Card>
            ))}

            {sourceDocuments.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>Không có tài liệu liên quan</p>
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="flex justify-end pt-4">
          <Button variant="outline" onClick={onClose}>
            Đóng
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
