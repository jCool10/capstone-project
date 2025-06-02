"use client"

import React, { useState } from "react"
import Image from "next/image"
import Link from "next/link"
import logo from "@/assets/logo.png"
import { Plus } from "lucide-react"

import UploadModal from "../modals/UploadModal"
import { Button } from "../ui/button"
import { SidebarTrigger } from "../ui/sidebar"
import ActiveWorkspaces from "../workspaces/ActiveWorkspaces"

export function Sidebar() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="col-span-2 border h-full p-2 rounded-2xl ">
      <div className="flex flex-col gap-2 h-full">
        <div className="flex gap-x-2 items-center justify-between">
          <Button
            onClick={() => setIsOpen(true)}
            className="m-auto w-full h-11 gap-x-2 py-1 px-2.5 rounded-xl bg-secondary text-primary justify-center items-center hover:bg-opacity-80 hover:text-secondary transition-all duration-300"
          >
            <Plus size={18} />
            <p className="text-sidebar text-sm font-semibold">New Workspace</p>
          </Button>
        </div>

        <ActiveWorkspaces />
      </div>

      <UploadModal isOpen={isOpen} setIsOpen={setIsOpen} />
    </div>
  )
}
