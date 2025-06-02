import "@/styles/globals.css"
import { Metadata, Viewport } from "next"
import Link from "next/link"
import { redirect } from "next/navigation"
import { useAuth } from "@/context/AuthContext"
import { QueryClient } from "@tanstack/react-query"

import { siteConfig } from "@/config/site"
import { fontSans } from "@/lib/fonts"
import { cn } from "@/lib/utils"
import { SidebarProvider } from "@/components/ui/sidebar"
import { Header } from "@/components/layouts/Header"
import { AppSidebar } from "@/components/layouts/Sidebar"
import { ProfileDropdown } from "@/components/layouts/profile-dropdown"
import Providers from "@/components/providers"
import ProtectedProvider from "@/components/providers/ProtectedProvider"
import { ThemeToggle } from "@/components/theme-toggle"

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "white" },
    { media: "(prefers-color-scheme: dark)", color: "black" },
  ],
}

export const metadata: Metadata = {
  title: {
    default: siteConfig.name,
    template: `%s - ${siteConfig.name}`,
  },
  description: siteConfig.description,
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon-16x16.png",
    apple: "/apple-touch-icon.png",
  },
}

interface RootLayoutProps {
  children: React.ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <>
      <html lang="en" suppressHydrationWarning>
        <head />
        <body className={cn("min-h-screen w-full bg-background font-sans antialiased", fontSans.variable)}>
          <Providers>
            <SidebarProvider>
              <AppSidebar />
              <main
                className={cn(
                  "ml-auto w-full max-w-full",
                  "peer-data-[state=collapsed]:w-[calc(100%-var(--sidebar-width-icon)-1rem)]",
                  "peer-data-[state=expanded]:w-[calc(100%-var(--sidebar-width))]",
                  "transition-[width] duration-200 ease-linear",
                  "flex h-svh flex-col",
                  "group-data-[scroll-locked=1]/body:h-full",
                  "group-data-[scroll-locked=1]/body:has-[main.fixed-main]:h-svh"
                )}
              >
                <Header>
                  <Link href="/">
                    <h1 className="text-2xl font-bold">Chat anything</h1>
                  </Link>
                </Header>
                {children}
              </main>
            </SidebarProvider>
          </Providers>
        </body>
      </html>
    </>
  )
}
