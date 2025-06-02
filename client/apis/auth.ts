import axiosInstance, { endpoints } from "@/utils/axios"

interface LoginPayload {
  email: string
  password: string
}

interface RegisterPayload {
  email: string
  password: string
}

export const login = async (payload: LoginPayload) => {
  const response = await axiosInstance.post(endpoints.auth.login, payload)
  return response.data
}

export const register = async (payload: RegisterPayload) => {
  const response = await axiosInstance.post(endpoints.auth.register, payload)
  return response.data
}

export const logout = async () => {
  const response = await axiosInstance.post(endpoints.auth.logout)
  return response.data
}
