// src/router/index.js

/*
 * WHAT IS A ROUTER?
 * A router maps URLs to Vue pages (views).
 * Without a router, your app is one page forever.
 * With a router: /dashboard shows Dashboard, /findings shows Findings, etc.
 *
 * NAVIGATION GUARD — beforeEach:
 * This runs before every page navigation.
 * It checks: is the user logged in?
 * If not — redirect them to the login page.
 * This protects dashboard, findings, approvals from being
 * visited without being logged in.
 *
 * CONNECTION TO BACKEND:
 * The router itself does not call the backend.
 * But it uses useAuth().isLoggedIn() to check if a token exists.
 * That token came from the backend's /auth/callback response.
 */

import { createRouter, createWebHistory } from "vue-router"
import { useAuth } from "../composables/useAuth"

// Import all page components
// Each one is a Vue file in the views folder
import LoginView from "../views/LoginView.vue"
import DashboardView from "../views/DashboardView.vue"
import FindingsView from "../views/FindingsView.vue"
import ApprovalsView from "../views/ApprovalsView.vue"
import CallbackView from "../views/CallbackView.vue"


// Define routes — URL path → which Vue component to show
const routes = [
    {
        path: "/",
        name: "Login",
        component: LoginView,
        // meta.requiresAuth = false means anyone can visit this page
        meta: { requiresAuth: false },
    },

    {
      path: "/callback",        // ← ADD THIS ROUTE
        name: "Callback",
        component: CallbackView,
        meta: { requiresAuth: false },
    },
    {
        path: "/dashboard",
        name: "Dashboard",
        component: DashboardView,
        // meta.requiresAuth = true means only logged-in users
        meta: { requiresAuth: true },
    },
    {
        path: "/findings",
        name: "Findings",
        component: FindingsView,
        meta: { requiresAuth: true },
    },
    {
        path: "/approvals",
        name: "Approvals",
        component: ApprovalsView,
        meta: { requiresAuth: true },
    },
]

const router = createRouter({
    // createWebHistory gives clean URLs like /dashboard
    // instead of /#/dashboard
    history: createWebHistory(),
    routes,
})

/*
 * NAVIGATION GUARD
 * Runs before every single page navigation.
 * to   = the page the user is going to
 * from = the page they are coming from
 * next = the function that allows or blocks navigation
 */
router.beforeEach((to, from, next) => {
    const { isLoggedIn } = useAuth()

    // If the page requires auth AND user is not logged in
    if (to.meta.requiresAuth && !isLoggedIn()) {
        // Send them to login page instead
        next({ name: "Login" })
    } else {
        // Allow navigation — user is logged in or page is public
        next()
    }
})

export default router