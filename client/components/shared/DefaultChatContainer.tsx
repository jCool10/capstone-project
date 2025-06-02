"use client"

import React, { useState } from "react"
import { isMobile } from "react-device-detect"

import ChatBubble from "./ChatBubble"

export default function DefaultChatContainer() {
  const [fetchedMessages, setFetchedMessages] = useState<any[]>([
    { user: "", response: "Hello there! How can I help you today?" },
    {
      user: "I need help with my account",
      response: "Sure! What's your email?",
    },
  ])
  const [mockMsgs, setMockMessages] = useState<any[]>([])

  return (
    <div
      style={{ height: isMobile ? "100%" : "calc(100% - 32px)" }}
      className="transition-all duration-500 relative md:ml-[2px] md:mr-[16px] md:rounded-[16px]  w-full h-full overflow-y-scroll border-2 border-outline"
    >
      {fetchedMessages.length === 0
        ? mockMsgs.map((content, i) => {
            return <React.Fragment key={i}>{content}</React.Fragment>
          })
        : fetchedMessages.map((fetchedMessage, i) => {
            return (
              <React.Fragment key={i}>
                <ChatBubble
                  message={fetchedMessage.user === "" ? fetchedMessage.response : fetchedMessage.user}
                  type={fetchedMessage.user === "" ? "response" : "user"}
                />
              </React.Fragment>
            )
          })}
    </div>
  )
}
