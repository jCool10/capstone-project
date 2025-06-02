import React from "react"
import { isMobile } from "react-device-detect"

import ChatHistory from "./ChatHistory"
import PromptInput from "./PromptInput"
import { SidebarMobileHeader } from "./Sidebar"

export default function ChatContainer({ workspace, knownHistory }: any) {
  return (
    <div
      style={{ height: isMobile ? "100%" : "calc(100% - 32px)" }}
      className="transition-all duration-500 relative md:ml-[2px] md:mr-[16px] md:my-[16px] md:rounded-[16px] bg-main-gradient w-full h-full overflow-y-scroll border-2 border-outline"
    >
      {isMobile && <SidebarMobileHeader />}
      <div className="flex flex-col h-full w-full md:mt-0 mt-[40px]">
        <ChatHistory
        // history={chatHistory}
        // workspace={workspace}
        // sendCommand={sendCommand}
        // updateHistory={setChatHistory}
        // regenerateAssistantMessage={regenerateAssistantMessage}
        />
        <PromptInput
        // submit={handleSubmit}
        // onChange={handleMessageChange}
        // inputDisabled={loadingResponse}
        // buttonDisabled={loadingResponse}
        // sendCommand={sendCommand}
        />
      </div>
    </div>
  )
}
