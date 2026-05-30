

import axios from "axios"
import { useAuth } from "./useAuth"

// The backend base URL — all requests start here
// Change this one line when deploying to production
const BACKEND_URL = "http://localhost:8000"

export function useApi() {
    const { token, logout } = useAuth()

    /*
     * createClient()
     * Creates a fresh axios instance with the current token attached.
     *
     * Why create it fresh each time instead of once at the top?
     * Because the token might not exist when the file loads.
     * By the time a Vue page calls api.get(), the user is logged in
     * and the token is available.
     */
    const createClient = () => {
        return axios.create({
            baseURL: BACKEND_URL,

            headers: {
                // THIS IS THE KEY LINE
                // Every request to FastAPI includes this header
                // FastAPI reads it to know who is calling
                "Authorization": `Bearer ${token.value}`,
                "Content-Type": "application/json",
            },

            // Wait 30 seconds before giving up on a request
            timeout: 30000,
        })
    }

    /*
     * get(endpoint)
     * Makes a GET request to the backend.
     * Use GET when you are READING data — not changing anything.
     *
     * EXAMPLE:
     * const { data } = await api.get("/api/v1/findings")
     * data is now the list of findings from FastAPI
     *
     * CONNECTION: GET http://localhost:8000/api/v1/findings
     *             ↓
     *             FastAPI queries PostgreSQL
     *             ↓
     *             Returns JSON list of findings
     */
    const get = async (endpoint) => {
        try {
            const client = createClient()
            const response = await client.get(endpoint)
            return response.data

        } catch (error) {
            // Handle specific HTTP error codes
            if (error.response?.status === 401) {
                // 401 = token expired or invalid
                // Log the user out and send them back to login
                console.warn("Token expired — logging out")
                await logout()
                window.location.href = "/"
            }

            if (error.response?.status === 500) {
                // 500 = server error — log it for debugging
                console.error("Backend error:", error.response.data)
            }

            // Re-throw so the calling Vue page can handle it too
            throw error
        }
    }

    /*
     * post(endpoint, body)
     * Makes a POST request to the backend.
     * Use POST when you are SENDING data or TRIGGERING an action.
     *
     * EXAMPLE — starting a scan:
     * const result = await api.post("/api/v1/scan", { site: "Project Atlas" })
     *
     * EXAMPLE — approving a fix:
     * const result = await api.post("/api/v1/approve", { finding_id: 5 })
     *
     * CONNECTION: POST http://localhost:8000/api/v1/approve
     *             body: { finding_id: 5 }
     *             ↓
     *             FastAPI runs the approved Graph write action
     *             ↓
     *             Returns success/failure
     */
    const post = async (endpoint, body = {}) => {
        try {
            const client = createClient()
            const response = await client.post(endpoint, body)
            return response.data

        } catch (error) {
            if (error.response?.status === 401) {
                await logout()
                window.location.href = "/"
            }
            throw error
        }
    }

    return { get, post }
}


