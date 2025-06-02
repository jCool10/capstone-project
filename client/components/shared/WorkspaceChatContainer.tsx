import { useEffect, useState } from "react"
import { useParams } from "next/navigation"

import ChatContainer from "./ChatContainer"

export default function WorkspaceChat({ loading, workspace }: any) {
  const { threadSlug = null } = useParams()
  const [history, setHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(true)

  return <ChatContainer workspace={workspace} knownHistory={history} />
}
