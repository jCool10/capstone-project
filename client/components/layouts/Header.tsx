"use client"

import React from "react"
import Link from "next/link"
import { redirect } from "next/navigation"
import { useAuth } from "@/context/AuthContext"
import { Plus } from "lucide-react"

import { cn } from "@/lib/utils"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { ProfileDropdown } from "@/components/layouts/profile-dropdown"
import { ThemeToggle } from "@/components/theme-toggle"

import { Button } from "../ui/button"

interface HeaderProps extends React.HTMLAttributes<HTMLElement> {
  fixed?: boolean
  ref?: React.Ref<HTMLElement>
}

export const Header = ({ className, fixed, children, ...props }: HeaderProps) => {
  const [offset, setOffset] = React.useState(0)
  const [mounted, setMounted] = React.useState(false)
  const { isAuthenticated } = useAuth()
  React.useEffect(() => {
    setMounted(true)
    const onScroll = () => {
      setOffset(document.body.scrollTop || document.documentElement.scrollTop)
    }

    // Add scroll listener to the body
    document.addEventListener("scroll", onScroll, { passive: true })

    // Clean up the event listener on unmount
    return () => document.removeEventListener("scroll", onScroll)
  }, [])

  // Safely handle shadow class during SSR
  const shadowClass = mounted && offset > 10 && fixed ? "shadow" : "shadow-none"

  return (
    <header
      className={cn(
        "flex h-16 items-center gap-3 bg-background p-4 sm:gap-4",
        fixed && "header-fixed peer/header fixed z-50 w-[inherit] rounded-md",
        shadowClass,
        className
      )}
      {...props}
    >
      {/* <SidebarTrigger variant="outline" className="scale-125 sm:scale-100" /> */}
      {/* <Separator orientation="vertical" className="h-6" /> */}
      {children}
      <div className="ml-auto flex items-center space-x-4">
        <ThemeToggle />

        {isAuthenticated ? (
          <ProfileDropdown />
        ) : (
          <Link href="/login">
            <Button variant="outline">Login</Button>
          </Link>
        )}
      </div>
    </header>
  )
}

Header.displayName = "Header"
