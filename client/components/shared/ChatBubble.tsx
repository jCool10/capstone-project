import React from "react"
import { UserIcon } from "lucide-react"

export default function ChatBubble({ message, type }: any) {
  const isUser = type === "user"

  return (
    <div className={`flex justify-center items-end w-full `}>
      <div className={`py-8 px-4 w-full flex gap-x-5 md:max-w-[80%] flex-col`}>
        <div className="flex gap-x-5">
          <UserIcon />

          <span className={`whitespace-pre-line  font-normal text-sm md:text-sm flex flex-col gap-y-1 mt-2`}>
            {message}
          </span>
        </div>
      </div>
    </div>
  )
}
