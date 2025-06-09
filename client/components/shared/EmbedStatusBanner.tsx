"use client"

import React from "react"
import { IWorkspace } from "@/types"
import { AlertTriangle, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

interface EmbedStatusBannerProps {
  workspace: IWorkspace
  onReEmbed: () => void
  isLoading?: boolean
}

export default function EmbedStatusBanner({ workspace, onReEmbed, isLoading = false }: EmbedStatusBannerProps) {
  // Only show if workspace is not embedded
  if (workspace.isEmbedded) {
    return null
  }

  return (
    <Card className="mx-4 mt-2 border-orange-200 bg-orange-50 text-orange-800 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-start gap-3 flex-1">
          <AlertTriangle className="h-5 w-5 mt-0.5 text-orange-600" />
          <div className="flex-1">
            <strong className="text-orange-900">Workspace chưa được nhúng!</strong>
            <p className="text-sm mt-1 text-orange-700">
              Các tài liệu trong workspace này chưa được xử lý. Bạn cần nhúng lại để có thể chat với tài liệu.
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={onReEmbed}
          disabled={isLoading}
          className="ml-4 bg-white hover:bg-orange-100 border-orange-300 text-orange-800"
        >
          {isLoading ? (
            <>
              <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
              Đang xử lý...
            </>
          ) : (
            <>
              <RefreshCw className="h-3 w-3 mr-1" />
              Nhúng lại
            </>
          )}
        </Button>
      </div>
    </Card>
  )
}
