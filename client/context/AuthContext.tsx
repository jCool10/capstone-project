"use client"

import React from "react"

//-----------------------------------------------------------------------------------------------

interface AuthContextType {
  accessToken: string | null
  setAccessToken: (accessToken: string | null) => void
  refreshToken: string | null
  setRefreshToken: (refreshToken: string | null) => void
  isAuthenticated: boolean
  user: any
  setUser: (user: any) => void
}

export const AuthContext = React.createContext<AuthContextType | undefined>(undefined)

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [accessTokenState, setAccessTokenState] = React.useState<string | null>(null)
  const [refreshTokenState, setRefreshTokenState] = React.useState<string | null>(null)
  const [userState, setUserState] = React.useState<any>(null)

  // Handle localStorage in useEffect to prevent hydration mismatch
  React.useEffect(() => {
    setAccessTokenState(localStorage.getItem("accessToken"))
    setRefreshTokenState(localStorage.getItem("refreshToken"))
    setUserState(JSON.parse(localStorage.getItem("user") || "{}"))
  }, [])

  const setAccessToken = (accessToken: string | null) => {
    setAccessTokenState(accessToken)
    if (accessToken) {
      localStorage.setItem("accessToken", accessToken)
    } else {
      localStorage.removeItem("accessToken")
    }
  }

  const setRefreshToken = (refreshToken: string | null) => {
    setRefreshTokenState(refreshToken)
    if (refreshToken) {
      localStorage.setItem("refreshToken", refreshToken)
    } else {
      localStorage.removeItem("refreshToken")
    }
  }

  const setUser = (user: any) => {
    setUserState(user)
    if (user) {
      localStorage.setItem("user", JSON.stringify(user))
    } else {
      localStorage.removeItem("user")
    }
  }

  const isAuthenticated = !!accessTokenState

  return (
    <AuthContext.Provider
      value={{
        accessToken: accessTokenState,
        setAccessToken,
        refreshToken: refreshTokenState,
        setRefreshToken,
        isAuthenticated,
        user: userState,
        setUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = React.useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
