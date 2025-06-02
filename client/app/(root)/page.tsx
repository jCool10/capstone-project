"use client"

import React from "react"
import Link from "next/link"
import { Bot, BrainCircuit, FileText, MessageSquare, Plus, Sparkles, Zap } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"

const features = [
  {
    icon: <MessageSquare className="h-8 w-8" />,
    title: "Chat Thông Minh",
    description: "Trao đổi với AI như trò chuyện với con người, nhận câu trả lời tự nhiên và hữu ích.",
  },
  {
    icon: <FileText className="h-8 w-8" />,
    title: "Phân Tích Tài Liệu",
    description: "Tải lên tài liệu và nhận phân tích, tóm tắt và trích xuất thông tin quan trọng.",
  },
  {
    icon: <BrainCircuit className="h-8 w-8" />,
    title: "Giải Quyết Vấn Đề",
    description: "Nhận hỗ trợ với các bài toán phức tạp, lập trình, và giải thuật.",
  },
  {
    icon: <Zap className="h-8 w-8" />,
    title: "Phản Hồi Nhanh",
    description: "Phản hồi ngay lập tức với thông tin chính xác, tiết kiệm thời gian nghiên cứu.",
  },
]

const sampleWorkspaces = [
  {
    id: "data-analysis",
    name: "Phân Tích Dữ Liệu",
    description: "Phân tích & trực quan hóa dữ liệu",
  },
  {
    id: "code-assistant",
    name: "Trợ Lý Lập Trình",
    description: "Viết code & debug",
  },
  {
    id: "writing-helper",
    name: "Hỗ Trợ Viết",
    description: "Soạn & chỉnh sửa văn bản",
  },
]

export default function HomePage() {
  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col">
      <div className="flex flex-col items-center justify-center bg-gradient-to-b from-primary/10 to-background px-4 py-20 text-center">
        <Sparkles className="mb-6 h-16 w-16 text-primary" />
        <h1 className="mb-4 text-4xl font-bold tracking-tight sm:text-5xl">Chào mừng đến với AI Assistant</h1>
        <p className="mb-8 max-w-[42rem] text-muted-foreground sm:text-xl">
          Trải nghiệm sức mạnh của trí tuệ nhân tạo thông qua cuộc trò chuyện tự nhiên. Đặt câu hỏi, nhận phân tích, và
          giải quyết vấn đề với AI có khả năng hiểu ngữ cảnh.
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <Button asChild size="lg">
            <Link href="/create">
              <Plus className="mr-2 h-4 w-4" />
              Tạo Workspace Mới
            </Link>
          </Button>
        </div>
      </div>

      <div className="container mx-auto px-4 py-16">
        <h2 className="mb-12 text-center text-3xl font-bold">Tính Năng Chính</h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((feature, index) => (
            <Card key={index} className="transition-all hover:shadow-lg">
              <CardHeader className="flex flex-row items-center gap-4">
                <div className="rounded-lg bg-primary/10 p-3 text-primary">{feature.icon}</div>
                <CardTitle>{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
