import React from "react"

export default function ChatHistory() {
  return (
    <div className="flex flex-col h-full md:mt-0 pb-44 md:pb-40 w-full justify-end items-center">
      <div className="flex flex-col items-center md:items-start md:max-w-[600px] w-full px-4">
        <p className="text-white/60 text-lg font-base py-4">
          Welcome to your new workspace.
        </p>
        {/* {!user || user.role !== "default" ? ( */}
        <p className="w-full items-center text-white/60 text-lg font-base flex flex-col md:flex-row gap-x-1">
          To get started either{" "}
          <span
            className="underline font-medium cursor-pointer"
            // onClick={showModal}
          >
            upload a document
          </span>
          or <b className="font-medium italic">send a chat.</b>
        </p>
        {/* ) : ( */}
        <p className="w-full items-center text-white/60 text-lg font-base flex flex-col md:flex-row gap-x-1">
          To get started <b className="font-medium italic">send a chat.</b>
        </p>
        {/* )} */}
        {/* <WorkspaceChatSuggestions
          suggestions={workspace?.suggestedMessages ?? []}
          sendSuggestion={handleSendSuggestedMessage}
        /> */}
      </div>
      {/* {showing && (
        <ManageWorkspace hideModal={hideModal} providedSlug={workspace.slug} />
      )} */}
    </div>
  )
}
