"use client"

import React from "react"
import { AlertTriangle, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

interface ReEmbedDialogProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  isLoading?: boolean
  workspaceName?: string
}

export default function ReEmbedDialog({
  isOpen,
  onClose,
  onConfirm,
  isLoading = false,
  workspaceName,
}: ReEmbedDialogProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5" />
            Nhúng lại workspace
          </DialogTitle>
          <DialogDescription>Bạn có chắc chắn muốn nhúng lại workspace "{workspaceName}"?</DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <div className="flex items-start gap-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-yellow-800 mb-1">Lưu ý:</p>
              <ul className="text-yellow-700 space-y-1">
                <li>• Quá trình này có thể mất vài phút</li>
                <li>• Tất cả tài liệu sẽ được xử lý lại</li>
                <li>• Bạn không thể chat trong lúc đang xử lý</li>
              </ul>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose} disabled={isLoading}>
            Hủy
          </Button>
          <Button type="submit" onClick={onConfirm} disabled={isLoading}>
            {isLoading ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Đang xử lý...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                Nhúng lại
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
