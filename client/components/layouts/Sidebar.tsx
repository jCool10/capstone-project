"use client"

import { useEffect } from "react"
import Link from "next/link"
import { useParams, usePathname } from "next/navigation"
import { IWorkspace } from "@/types"
import { Braces, Code, Cog, Database, Lightbulb, PencilRuler, Plus } from "lucide-react"

import { cn } from "@/lib/utils"
import { useWorkspaces } from "@/hooks/useWorkspaces"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

import { Separator } from "../ui/separator"

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const params = useParams()
  const pathname = usePathname()
  const currentSlug = params?.slug as string
  const { workspaces, refetch } = useWorkspaces()

  // Refetch data when navigating from create page to any other page
  useEffect(() => {
    // Check if running in browser before using sessionStorage
    if (typeof window !== "undefined") {
      const isComingFromCreate = sessionStorage.getItem("createdWorkspace")
      if (isComingFromCreate && pathname !== "/create") {
        refetch()
        sessionStorage.removeItem("createdWorkspace")
      }
    }
  }, [pathname, refetch])

  return (
    <Sidebar className="p-0" collapsible="icon" variant="floating" {...props}>
      <SidebarHeader>
        <AppSidebarHeader />
      </SidebarHeader>
      <Separator />
      <SidebarContent>
        <div className="px-2 py-2">
          <WorkspaceList workspaces={workspaces} currentSlug={currentSlug} />
        </div>
      </SidebarContent>
    </Sidebar>
  )
}

// Extracted workspace list component
function WorkspaceList({ workspaces, currentSlug }: { workspaces?: IWorkspace[]; currentSlug: string }) {
  return (
    <SidebarMenu>
      {workspaces?.length === 0 && (
        <div className="flex items-center justify-center">
          <p className="text-sm text-muted-foreground">No workspaces found</p>
          <Link href="/create" className="h-5 w-5">
            <Plus className="h-3.5 w-3.5" />
          </Link>
        </div>
      )}
      {workspaces?.map((workspace) => (
        <SidebarMenuItem className="cursor-pointer" key={workspace.slug}>
          <SidebarMenuButton
            size="sm"
            className={cn(
              "data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground py-6",
              currentSlug === workspace.slug && "bg-accent"
            )}
            asChild
          >
            <Link href={`/workspace/${workspace.slug}`}>
              <div
                className={cn(
                  "flex aspect-square size-7 items-center justify-center rounded-lg text-white",
                  workspace.model === "gpt-4o" ? "bg-blue-500" : "bg-green-500"
                )}
              >
                {workspace.model === "gpt-4o" ? <Code className="h-4 w-4" /> : <Database className="h-4 w-4" />}
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-medium">{workspace.name}</span>
              </div>
            </Link>
          </SidebarMenuButton>
        </SidebarMenuItem>
      ))}
    </SidebarMenu>
  )
}

const AppSidebarHeader = () => {
  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <SidebarMenuButton
          size="lg"
          className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
          asChild
        >
          <Link href="/create">
            <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
              <Plus className="size-5" />
            </div>
            <div className="grid flex-1 text-left text-sm leading-tight">
              <span className="truncate font-semibold">New workspace</span>
            </div>
          </Link>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
