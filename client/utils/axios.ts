"use client"

import { useRouter } from "next/navigation"
import axios from "axios"

import { config } from "@/config/global-config"

//----------------------------------------------------------------------

const axiosInstance = axios.create({ baseURL: config.api.baseURL })

// Track if a refresh is already in progress
let isRefreshing = false
// Store pending requests that should be retried after token refresh
let pendingRequests: Array<{
  resolve: (value: unknown) => void
  reject: (reason?: any) => void
  config: any
}> = []

axiosInstance.interceptors.request.use(
  (config) => {
    const accessToken = localStorage.getItem("accessToken")
    const refreshToken = localStorage.getItem("refreshToken")
    const user = JSON.parse(localStorage.getItem("user") || "{}")

    if (config.url?.includes("login") || config.url?.includes("register")) {
      return config
    }

    if (accessToken) {
      config.headers["Authorization"] = accessToken
    }

    if (refreshToken) {
      config.headers["refresh-token"] = refreshToken
    }

    if (user && user._id) {
      config.headers["client-id"] = user._id
    }

    return config
  },
  (error) => Promise.reject(error)
)

axiosInstance.interceptors.response.use(
  (res) => res.data,
  async (error) => {
    const originalRequest = error.config

    // Prevent infinite loops
    if (originalRequest._retry) {
      return Promise.reject(error)
    }

    if (error.response && error.response.status === 401 && error.response.data.message === "Unauthorized") {
      localStorage.removeItem("accessToken")
      localStorage.removeItem("refreshToken")
      localStorage.removeItem("user")

      if (typeof window !== "undefined") {
        window.location.href = "/login"
      }

      return Promise.reject(error)
    }

    // Handle token expiration
    if (error.response && (error.response.data.message === "jwt expired" || error.response.status === 401)) {
      if (!isRefreshing) {
        isRefreshing = true
        originalRequest._retry = true

        try {
          const result = await refreshTokenRequest()

          if (result && result.tokens) {
            // Update tokens in localStorage
            localStorage.setItem("accessToken", result.tokens.accessToken)
            localStorage.setItem("refreshToken", result.tokens.refreshToken)

            // Update the original request with new token
            originalRequest.headers["Authorization"] = result.tokens.accessToken
            originalRequest.headers["refresh-token"] = result.tokens.refreshToken

            // Process pending requests with new token
            processQueue(null, result.tokens)

            // Retry the original request with new token
            return axiosInstance(originalRequest)
          }
        } catch (refreshError) {
          // Process queue with error
          processQueue(refreshError, null)

          // Clear user data and redirect to login
          localStorage.removeItem("accessToken")
          localStorage.removeItem("refreshToken")
          localStorage.removeItem("user")

          if (typeof window !== "undefined") {
            window.location.href = "/login"
          }

          return Promise.reject(refreshError)
        } finally {
          isRefreshing = false
        }
      } else {
        // Queue the request if refresh is already in progress
        return new Promise((resolve, reject) => {
          pendingRequests.push({
            resolve,
            reject,
            config: originalRequest,
          })
        })
      }
    }

    return Promise.reject((error.response && error.response.data) || "Something went wrong")
  }
)

// Process queued requests after token refresh
function processQueue(error: any, token: any | null) {
  pendingRequests.forEach((request) => {
    if (error) {
      request.reject(error)
    } else if (token) {
      // Update token in pending request
      request.config.headers["Authorization"] = token.accessToken
      request.config.headers["refresh-token"] = token.refreshToken
      request.resolve(axiosInstance(request.config))
    }
  })

  // Clear the queue
  pendingRequests = []
}

export default axiosInstance

const refreshTokenRequest = async () => {
  try {
    const response = await axios.post(
      `${config.api.baseURL}${endpoints.auth.refreshToken}`,
      {},
      {
        headers: {
          "refresh-token": localStorage.getItem("refreshToken"),
          "client-id": JSON.parse(localStorage.getItem("user") || "{}")._id,
        },
      }
    )
    return response.data.data
  } catch (error) {
    throw error
  }
}

const VERSION_PREFIX = "api"

export const endpoints = {
  auth: {
    login: `${VERSION_PREFIX}/login`,
    register: `${VERSION_PREFIX}/register`,
    logout: `${VERSION_PREFIX}/logout`,
    refreshToken: `${VERSION_PREFIX}/refresh-token`,
  },
  files: {
    embed: `${VERSION_PREFIX}/files/embed`,
    workspaces: `${VERSION_PREFIX}/files/workspaces`,
    workspace: (workspaceSlug: string) => `${VERSION_PREFIX}/files/workspace/${workspaceSlug}`,
    query: (workspaceSlug: string) => `${VERSION_PREFIX}/files/workspace/${workspaceSlug}/query`,
    messages: (workspaceSlug: string) => `${VERSION_PREFIX}/files/workspace/${workspaceSlug}/messages`,
  },
}
