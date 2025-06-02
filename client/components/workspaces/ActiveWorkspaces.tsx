"use client"

import React, { useState } from "react"
import Link from "next/link"
import { Settings, Square, Upload } from "lucide-react"
import truncate from "truncate"

import { Button } from "../ui/button"

export default function ActiveWorkspaces() {
  const [workspaces, setWorkspaces] = useState<any[]>([
    {
      id: 1,
      name: "Workspace 1",
      slug: "workspace-1",
    },
    {
      id: 2,
      name: "Workspace 2",
      slug: "workspace-2",
    },
  ])
  const [gearHover, setGearHover] = useState({})

  return (
    <div role="list" aria-label="Workspaces" className="flex flex-col gap-y-2">
      {workspaces.map((workspace) => {
        const isActive = true
        // const isHovered = hoverStates[workspace.id]
        return (
          <div
            className="flex justify-between w-full bg-primary/80 text-secondary rounded-xl py-2 px-4 gap-y-2"
            key={workspace.id}
            role="listitem"
          >
            <Link
              href={`/workspace/${workspace.slug}`}
              className=" flex gap-2 text-sm items-center"
            >
              <Square weight={isActive ? "fill" : "regular"} size={24} />
              {workspace.name}
            </Link>

            {/* <Button variant="outline" size={"icon"}> */}

            <Settings size={20} weight="bold" />
            {/* </Button> */}
          </div>
        )
      })}
      {/* {showing && (
        <ManageWorkspace
          hideModal={hideModal}
          providedSlug={selectedWs ? selectedWs.slug : null}
        />
      )} */}
    </div>
  )
}
