import { useContext } from "react"
import { login as loginApi, logout as logoutApi } from "@/apis/auth"
import { AuthContext } from "@/context/AuthContext"
import { useMutation } from "@tanstack/react-query"

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }

  const { mutateAsync: login } = useMutation({
    mutationFn: loginApi,
    onSuccess: (data) => {
      context.setAccessToken(data.tokens.accessToken)
      context.setRefreshToken(data.tokens.refreshToken)
      context.setUser(data.user)
    },
  })

  const { mutateAsync: logout } = useMutation({
    mutationFn: logoutApi,
    onSuccess: () => {
      context.setAccessToken(null)
      context.setRefreshToken(null)
      context.setUser(null)
    },
  })

  return {
    ...context,
    login,
    logout,
  }
}
