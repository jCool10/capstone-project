import React from "react"

export default function PromptInput() {
  return (
    <div className="w-full fixed md:absolute bottom-0 left-0 z-10 md:z-0 flex justify-center items-center">
      {/* <SlashCommands
        showing={showSlashCommand}
        setShowing={setShowSlashCommand}
        sendCommand={sendCommand}
      /> */}
      {/* <AvailableAgents
        showing={showAgents}
        setShowing={setShowAgents}
        sendCommand={sendCommand}
        promptRef={textareaRef}
      /> */}
      <form
        // onSubmit={handleSubmit}
        className="flex flex-col gap-y-1 rounded-t-lg md:w-3/4 w-full mx-auto max-w-xl"
      >
        <div className="flex items-center rounded-lg md:mb-4">
          <div className="w-[600px] bg-main-gradient shadow-2xl border border-white/50 rounded-2xl flex flex-col px-4 overflow-hidden">
            <div className="flex items-center w-full border-b-2 border-gray-500/50">
              <textarea
                // ref={textareaRef}
                // onChange={(e) => {
                //   onChange(e)
                //   watchForSlash(e)
                //   watchForAt(e)
                //   adjustTextArea(e)
                //   setPromptInput(e.target.value)
                // }}
                // onKeyDown={captureEnter}
                // required={true}
                // disabled={inputDisabled}
                // onFocus={() => setFocused(true)}
                // onBlur={(e) => {
                //   setFocused(false)
                //   adjustTextArea(e)
                // }}
                // value={promptInput}
                className="cursor-text max-h-[50vh] md:max-h-[350px] md:min-h-[40px] mx-2 md:mx-0 py-2 w-full text-[16px] md:text-md text-white bg-transparent placeholder:text-white/60 resize-none active:outline-none focus:outline-none flex-grow"
                placeholder={"Send a message"}
              />
              {/* {buttonDisabled ? ( */}
              {/* <StopGenerationButton /> */}
              {/* ) : ( */}
              <>
                <button
                  // ref={formRef}
                  type="submit"
                  className="inline-flex justify-center rounded-2xl cursor-pointer text-white/60 hover:text-white group ml-4"
                  data-tooltip-id="send-prompt"
                  data-tooltip-content="Send prompt message to workspace"
                  aria-label="Send prompt message to workspace"
                >
                  {/* <PaperPlaneRight className="w-7 h-7 my-3" weight="fill" /> */}
                  <span className="sr-only">Send message</span>
                </button>
                {/* <Tooltip
                    id="send-prompt"
                    place="bottom"
                    delayShow={300}
                    className="tooltip !text-xs z-99"
                  /> */}
              </>
              {/* )} */}
            </div>
            {/* <div className="flex justify-between py-3.5">
              <div className="flex gap-x-2">
                <SlashCommandsButton
                  showing={showSlashCommand}
                  setShowSlashCommand={setShowSlashCommand}
                />
                <AvailableAgentsButton
                  showing={showAgents}
                  setShowAgents={setShowAgents}
                />
                <TextSizeButton />
              </div>
              <div className="flex gap-x-2">
                <SpeechToText sendCommand={sendCommand} />
              </div>
            </div> */}
          </div>
        </div>
      </form>
    </div>
  )
}
