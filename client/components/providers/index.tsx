"use client"

import React, { useState } from "react"
import { AuthProvider } from "@/context/AuthContext"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ThemeProvider } from "next-themes"

import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"

interface Props {
  children: React.ReactNode
}

export default function Providers({ children }: Props) {
  const [queryClient] = useState(() => new QueryClient())

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
        </ThemeProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}
