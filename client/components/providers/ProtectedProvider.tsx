"use client"

import React from "react"
import { redirect } from "next/navigation"
import { useAuth } from "@/context/AuthContext"

export default function ProtectedProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    redirect("/login")
  }

  return <>{children}</>
}
