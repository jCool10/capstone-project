// components/ModalWrapper.js
import React from "react"
import { X } from "lucide-react"

import { Button } from "../ui/button"

interface ModalWrapperProps {
  isOpen: boolean
  children: React.ReactNode
  onClose: () => void
}

const ModalWrapper = ({ isOpen, children, onClose }: ModalWrapperProps) => {
  if (!isOpen) return null

  return (
    <div className="bg-background backdrop-blur-sm fixed top-0 left-0  w-screen h-screen flex items-center justify-center z-30">
      <div className=" rounded-lg container shadow-lg relative">
        <Button
          variant="secondary"
          className="absolute top-3 right-3 "
          size="icon"
          onClick={onClose}
        >
          <X size={16} />
        </Button>
        {children}
      </div>
    </div>
  )
}

export default ModalWrapper
