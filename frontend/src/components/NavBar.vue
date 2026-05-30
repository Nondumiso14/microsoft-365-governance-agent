<!-- src/components/NavBar.vue -->

<!--
  WHAT THIS COMPONENT IS:
  The top navigation bar shared across all protected pages.
  Dashboard, Findings, and Approvals all use the same nav.

  WHY A SEPARATE COMPONENT?
  Without this — every page has its own nav HTML and CSS.
  One style change means updating three files.
  With this — change the nav once, all pages update.

  HOW TO USE IT IN ANY PAGE:
    import NavBar from "../components/NavBar.vue"

    <NavBar
      :user="user"
      :findings-count="findings.length"
      @logout="handleLogout"
    />

  PROPS:
    user          — object  — user profile { displayName, mail }
    findingsCount — number  — shows red badge on Findings link

  EMITS:
    logout — when the Sign out button is clicked
             parent page handles the actual logout logic

  WHY EMITS INSTEAD OF CALLING LOGOUT HERE?
    Each page might need to do different things on logout.
    NavBar should not know about routing or token clearing.
    It just says "the user wants to log out" — the parent decides what to do.
-->

<template>
  <nav class="nav" role="navigation" aria-label="Main navigation">

    <!-- Left: app brand -->
    <div class="nav-left">
      <div class="app-brand">
        <div class="brand-icon" aria-hidden="true">
          <svg width="20" height="20" viewBox="0 0 21 21">
            <rect x="1" y="1" width="9" height="9" fill="#f25022"/>
            <rect x="11" y="1" width="9" height="9" fill="#7fba00"/>
            <rect x="1" y="11" width="9" height="9" fill="#00a4ef"/>
            <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
          </svg>
        </div>
        <span class="brand-name">M365 Governance Agent</span>
      </div>
    </div>

    <!-- Right: navigation links + user profile + logout -->
    <div class="nav-right">

      <!-- Navigation links -->
      <div class="nav-links">
        <router-link to="/dashboard" class="nav-link" active-class="nav-link--active">
          Dashboard
        </router-link>

        <router-link to="/findings" class="nav-link" active-class="nav-link--active">
          Findings
          <!--
            v-if only shows the badge when findingsCount > 0
            The count comes from the parent page as a prop
          -->
          <span v-if="findingsCount > 0" class="nav-badge" aria-label="{{ findingsCount }} findings">
            {{ findingsCount }}
          </span>
        </router-link>

        <router-link to="/approvals" class="nav-link" active-class="nav-link--active">
          Approvals
        </router-link>
      </div>

      <!-- Divider -->
      <div class="nav-divider" aria-hidden="true"></div>

      <!-- User profile -->
      <!--
        v-if only shows when user prop is provided
        Displays avatar with initials, name, and email
      -->
      <div v-if="user" class="user-profile">
        <div class="user-avatar" aria-hidden="true">{{ initials }}</div>
        <div class="user-info">
          <p class="user-name">{{ user.displayName || "User" }}</p>
          <p class="user-email">{{ user.mail || user.userPrincipalName || "" }}</p>
        </div>
      </div>

      <!-- Logout button -->
      <!--
        @click emits the "logout" event to the parent
        Parent handles: await logout() then router.push("/")
      -->
      <button
        @click="$emit('logout')"
        class="logout-btn"
        aria-label="Sign out"
      >
        Sign out
      </button>

    </div>

  </nav>
</template>


<script setup>
import { computed } from "vue"

/*
 * Props — data passed in from the parent page
 */
const props = defineProps({
  user: {
    type: Object,
    default: null,
  },
  findingsCount: {
    type: Number,
    default: 0,
  },
})

/*
 * Emits — events this component can send to its parent
 * Parent listens with: <NavBar @logout="handleLogout" />
 */
defineEmits(["logout"])

/*
 * initials — computed from user display name
 * "Nondumiso Shange" → "NS"
 */
const initials = computed(() => {
  if (!props.user?.displayName) return "U"
  return props.user.displayName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)
})
</script>


<style scoped>
.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  height: 56px;
  border-bottom: 1px solid #1f1f23;
  background: #0a0a0b;
  position: sticky;
  top: 0;
  z-index: 100;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ── Left side ────────────────────────────────────────── */

.nav-left { display: flex; align-items: center; }

.app-brand { display: flex; align-items: center; gap: 10px; }

.brand-icon {
  width: 32px;
  height: 32px;
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.brand-name {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
}

/* ── Right side ───────────────────────────────────────── */

.nav-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ── Navigation links ─────────────────────────────────── */

.nav-links { display: flex; align-items: center; gap: 2px; }

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #6b7280;
  text-decoration: none;
  padding: 5px 12px;
  border-radius: 6px;
  transition: all 0.15s;
  position: relative;
}

.nav-link:hover { color: #ffffff; background: rgba(255,255,255,.05); }

/* Active state — current page link highlighted */
.nav-link--active {
  color: #ffffff;
  background: rgba(99,102,241,.12);
}

.nav-badge {
  background: #ef4444;
  color: #ffffff;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 10px;
  line-height: 1.4;
}

/* ── Divider ──────────────────────────────────────────── */

.nav-divider {
  width: 1px;
  height: 24px;
  background: #27272a;
  margin: 0 8px;
}

/* ── User profile ─────────────────────────────────────── */

.user-profile {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 10px;
  border-radius: 8px;
  background: rgba(255,255,255,.04);
  border: 1px solid #27272a;
}

.user-avatar {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: #ffffff;
  flex-shrink: 0;
}

.user-info { display: flex; flex-direction: column; gap: 1px; }

.user-name  { font-size: 12px; font-weight: 500; color: #ffffff; line-height: 1; }
.user-email { font-size: 10px; color: #6b7280; line-height: 1; }

/* ── Logout button ────────────────────────────────────── */

.logout-btn {
  font-size: 12px;
  color: #6b7280;
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 6px;
  transition: all 0.15s;
  margin-left: 4px;
}

.logout-btn:hover {
  color: #ffffff;
  background: rgba(255,255,255,.05);
}

/* ── Responsive ───────────────────────────────────────── */

@media (max-width: 768px) {
  .user-info { display: none; }
  .nav-divider { display: none; }
  .brand-name { display: none; }
}
</style>