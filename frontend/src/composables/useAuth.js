// src/composables/useAuth.js
import { ref } from "vue"

const BACKEND_URL = "http://localhost:8000"
const SESSION_KEY = "m365_token"

// Read from sessionStorage so token survives page refresh
const token = ref(sessionStorage.getItem(SESSION_KEY) || null)
const currentUser = ref(null)

export function useAuth() {

  const login = () => {
    window.location.href = `${BACKEND_URL}/auth/login`
  }

  const setToken = (newToken) => {
    token.value = newToken
    sessionStorage.setItem(SESSION_KEY, newToken)
  }

  const logout = async () => {
    try {
      await fetch(`${BACKEND_URL}/auth/logout`)
    } catch (e) {
      console.error("Logout error:", e)
    } finally {
      token.value = null
      currentUser.value = null
      sessionStorage.removeItem(SESSION_KEY)
    }
  }

  const isLoggedIn = () => token.value !== null

  return {
    token,
    currentUser,
    login,
    setToken,
    logout,
    isLoggedIn,
  }
} 