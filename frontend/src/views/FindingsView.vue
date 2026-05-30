<!-- src/views/FindingsView.vue -->

<!--
  WHAT THIS PAGE DOES:
  Shows a table of all security findings from the database.
  Each row is one risky file or permission found during the scan.

  HOW IT CONNECTS TO THE BACKEND:
  When the page loads → onMounted() runs →
  api.get("/api/v1/findings") is called →
  FastAPI reads the findings table in PostgreSQL →
  Returns a list of findings →
  Vue displays them as table rows

  BACKEND ENDPOINT:
  GET http://localhost:8000/api/v1/findings
  Returns: [
    {
      id: 1,
      resource_name: "Budget-2025.xlsx",
      finding_type: "anonymous_link",
      severity: "critical",
      risk_score: 9,
      evidence: "File has anonymous edit link...",
      recommended_action: "Remove the anonymous link",
      status: "open"
    }
  ]

  REFERENCES:
  useApi.js    → api.get() — makes the HTTP call with token
  useAuth.js   → logout() — for the nav sign out button
  router/index.js → router.push() — navigation between pages
  FastAPI main.py → GET /api/v1/findings endpoint
  database.py → get_open_findings() — reads PostgreSQL
-->

<template>
  <div class="page">

    <!-- ── Navigation Bar ─────────────────────────────── -->
    <nav class="nav">
      <div class="nav-left">
        <!-- router-link is Vue Router's way of navigating between pages -->
        <!-- It does NOT reload the page — just swaps the component -->
        <router-link to="/dashboard" class="nav-back">
          ← Dashboard
        </router-link>
        <h1 class="nav-title">Security Findings</h1>
      </div>

      <div class="nav-right">
        <!-- Show how many open findings exist -->
        <span v-if="findings.length > 0" class="findings-count">
          {{ findings.length }} finding{{ findings.length === 1 ? '' : 's' }}
        </span>
        <button @click="handleLogout" class="nav-logout">Sign out</button>
      </div>
    </nav>

    <!-- ── Main Content ───────────────────────────────── -->
    <main class="main">

      <!-- Page header -->
      <div class="page-header">
        <h2 class="page-title">Risk Findings</h2>
        <p class="page-sub">
          All security risks found in your Microsoft 365 environment.
          Review each finding and approve fixes in the Approvals page.
        </p>
      </div>

      <!-- Filter bar -->
      <!--
        v-model creates a two-way binding between the input and selectedSeverity
        When the user picks a filter → selectedSeverity updates →
        filteredFindings computed property recalculates →
        Vue re-renders the table automatically
      -->
      <div class="filter-bar">
        <span class="filter-label">Filter by severity:</span>
        <div class="filter-buttons">
          <button
            v-for="level in severityLevels"
            :key="level.value"
            @click="selectedSeverity = level.value"
            :class="['filter-btn', { 'filter-btn--active': selectedSeverity === level.value }]"
            :style="selectedSeverity === level.value ? { borderColor: level.color, color: level.color } : {}"
          >
            {{ level.label }}
          </button>
        </div>
      </div>

      <!-- Loading state -->
      <!--
        v-if shows this div ONLY when isLoading is true
        Once data loads, isLoading becomes false and this disappears
      -->
      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading findings from database...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="error-state">
        <p class="error-title">Could not load findings</p>
        <p class="error-msg">{{ error }}</p>
        <button @click="loadFindings" class="retry-btn">Try again</button>
      </div>

      <!-- Empty state — no findings at all -->
      <div v-else-if="findings.length === 0" class="empty-state">
        <div class="empty-icon" aria-hidden="true">✓</div>
        <p class="empty-title">No findings yet</p>
        <p class="empty-sub">
          Run a governance scan from the Dashboard to find security risks.
        </p>
        <router-link to="/dashboard" class="empty-link">
          Go to Dashboard →
        </router-link>
      </div>

      <!-- Empty state — filtered to nothing -->
      <div v-else-if="filteredFindings.length === 0" class="empty-state">
        <p class="empty-title">No {{ selectedSeverity }} findings</p>
        <p class="empty-sub">Try a different severity filter above.</p>
      </div>

      <!-- Findings table -->
      <!--
        v-else shows this ONLY when all the v-if and v-else-if above are false
        meaning: not loading, no error, has findings, filter has results
      -->
      <div v-else class="findings-list">

        <!--
          v-for loops through filteredFindings array
          For each finding it renders one finding-card div
          :key="finding.id" — Vue needs a unique key to track each item
          When the list updates Vue only re-renders items that changed
        -->
        <div
          v-for="finding in filteredFindings"
          :key="finding.id"
          class="finding-card"
          :class="`finding-card--${finding.severity}`"
        >

          <!-- Card header row -->
          <div class="card-header">

            <!-- Left: file name and type -->
            <div class="card-info">
              <p class="card-filename">{{ finding.resource_name }}</p>
              <p class="card-type">{{ formatFindingType(finding.finding_type) }}</p>
            </div>

            <!-- Right: severity badge and risk score -->
            <div class="card-meta">
              <!--
                :class is Vue's dynamic class binding
                severityClass() returns different class names
                based on the severity value
              -->
              <span :class="['severity-badge', `severity-badge--${finding.severity}`]">
                {{ finding.severity.toUpperCase() }}
              </span>
              <span class="risk-score">
                Risk: {{ finding.risk_score }}/10
              </span>
            </div>

          </div>

          <!-- Evidence — what was actually found -->
          <p class="card-evidence">{{ finding.evidence }}</p>

          <!-- Recommended action -->
          <div class="card-action">
            <span class="action-label">Recommended:</span>
            <span class="action-text">{{ finding.recommended_action }}</span>
          </div>

          <!-- Card footer: status and approve button -->
          <div class="card-footer">
            <span :class="['status-pill', `status-pill--${finding.status}`]">
              {{ finding.status }}
            </span>

            <!--
              Only show approve button if status is open
              router-link navigates to /approvals page
              We pass the finding id as a query param so
              ApprovalsView can highlight that specific finding
            -->
            <router-link
              v-if="finding.status === 'open'"
              :to="{ path: '/approvals', query: { finding_id: finding.id } }"
              class="approve-link"
            >
              Review fix →
            </router-link>

          </div>

        </div>

      </div>

    </main>

  </div>
</template>


<script setup>
/*
 * IMPORTS EXPLAINED:
 *
 * ref()      — creates reactive variables
 *              when .value changes → template updates automatically
 *
 * computed() — creates values that recalculate when dependencies change
 *              filteredFindings recalculates when findings or selectedSeverity change
 *
 * onMounted()— runs once when this page first appears on screen
 *              we use it to load findings from the backend
 *
 * useRouter()— gives us the router object for programmatic navigation
 *              router.push('/login') sends user to the login page
 *
 * useAuth()  — our composable from src/composables/useAuth.js
 *              gives us the logout function
 *
 * useApi()   — our composable from src/composables/useApi.js
 *              gives us api.get() which calls FastAPI with the token
 */
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import { useAuth } from "../composables/useAuth"
import { useApi } from "../composables/useApi"

const router = useRouter()
const { logout } = useAuth()
const api = useApi()

// ── Reactive state ────────────────────────────────────────
// ref() creates reactive variables
// When .value changes — the template updates instantly

const findings = ref([])           // all findings from the database
const isLoading = ref(false)       // true while fetching from backend
const error = ref(null)            // holds error message if fetch fails
const selectedSeverity = ref("all") // current severity filter

// Severity filter button definitions
const severityLevels = [
  { value: "all",      label: "All",      color: "#6b7280" },
  { value: "critical", label: "Critical", color: "#ef4444" },
  { value: "high",     label: "High",     color: "#f97316" },
  { value: "medium",   label: "Medium",   color: "#eab308" },
  { value: "low",      label: "Low",      color: "#22c55e" },
]

// ── Computed property ─────────────────────────────────────
/*
 * computed() creates a value that recalculates automatically
 * when its dependencies change.
 *
 * filteredFindings depends on:
 *   - findings.value        (the full list)
 *   - selectedSeverity.value (the current filter)
 *
 * When either changes → filteredFindings recalculates →
 * Vue re-renders the table with the new filtered list
 *
 * EXAMPLE:
 *   selectedSeverity = "critical"
 *   filteredFindings = findings filtered to only critical ones
 *
 *   selectedSeverity = "all"
 *   filteredFindings = all findings unchanged
 */
const filteredFindings = computed(() => {
  if (selectedSeverity.value === "all") {
    return findings.value
  }
  return findings.value.filter(
    f => f.severity === selectedSeverity.value
  )
})

// ── API call ──────────────────────────────────────────────
/*
 * loadFindings() fetches findings from FastAPI.
 *
 * BACKEND CONNECTION:
 *   GET http://localhost:8000/api/v1/findings
 *
 * useApi().get() automatically:
 *   1. Reads the token from useAuth
 *   2. Adds Authorization: Bearer TOKEN to the request header
 *   3. FastAPI receives the request and verifies the token
 *   4. FastAPI queries PostgreSQL findings table
 *   5. Returns JSON list of findings
 *
 * REFERENCES:
 *   src/composables/useApi.js → get()
 *   src/api/main.py           → GET /api/v1/findings endpoint
 *   src/memory/database.py    → get_open_findings()
 */
const loadFindings = async () => {
  isLoading.value = true
  error.value = null

  try {
    // api.get() adds the Bearer token automatically
    const data = await api.get("/api/v1/findings")

    // Store in reactive ref — template updates immediately
    findings.value = data

  } catch (err) {
    error.value = "Failed to load findings. Please try again."
    console.error("Findings load error:", err)

  } finally {
    // This runs whether success or failure
    // Always stop the loading spinner
    isLoading.value = false
  }
}

// ── Helper functions ──────────────────────────────────────

/*
 * formatFindingType() converts the raw database value to readable text.
 *
 * EXAMPLE:
 *   "anonymous_link"      → "Anonymous Link"
 *   "external_user_access"→ "External User Access"
 *
 * replace(/_/g, " ") replaces ALL underscores with spaces
 * replace(/\b\w/g, ...) capitalises the first letter of each word
 */
const formatFindingType = (type) => {
  return type
    .replace(/_/g, " ")
    .replace(/\b\w/g, char => char.toUpperCase())
}

/*
 * handleLogout() logs out and navigates back to login.
 *
 * await logout() — clears the token (calls /auth/logout on backend)
 * router.push() — navigates to the login page without page reload
 */
const handleLogout = async () => {
  await logout()
  router.push({ name: "Login" })
}

// ── Lifecycle hook ────────────────────────────────────────
/*
 * onMounted() runs once when this page first appears.
 * We load findings immediately so the user does not
 * have to click anything to see them.
 */
onMounted(() => {
  loadFindings()
})
</script>


<style scoped>
/*
 * scoped = styles only apply to this component
 * Cannot accidentally affect other Vue pages
 */

:global(*) { margin: 0; padding: 0; box-sizing: border-box; }
:global(html), :global(body), :global(#app) { height: 100%; }

.page {
  min-height: 100vh;
  background: #030303;
  color: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ── Nav ──────────────────────────────────────────────── */

.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  border-bottom: 1px solid #1f1f23;
  background: #0a0a0b;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.nav-back {
  font-size: 13px;
  color: #6b7280;
  text-decoration: none;
  transition: color 0.15s;
}

.nav-back:hover { color: #ffffff; }

.nav-title {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.findings-count {
  font-size: 12px;
  color: #6b7280;
  background: #1f1f23;
  padding: 4px 10px;
  border-radius: 20px;
}

.nav-logout {
  font-size: 13px;
  color: #6b7280;
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.15s;
}

.nav-logout:hover { color: #ffffff; }

/* ── Main ─────────────────────────────────────────────── */

.main {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 24px;
}

.page-header { margin-bottom: 28px; }
.page-title { font-size: 26px; font-weight: 600; margin-bottom: 6px; }
.page-sub { font-size: 14px; color: #6b7280; line-height: 1.5; }

/* ── Filter bar ───────────────────────────────────────── */

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.filter-label { font-size: 13px; color: #6b7280; }

.filter-buttons { display: flex; gap: 8px; flex-wrap: wrap; }

.filter-btn {
  padding: 5px 14px;
  font-size: 12px;
  background: transparent;
  border: 1px solid #27272a;
  border-radius: 20px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s;
}

.filter-btn:hover { border-color: #52525b; color: #ffffff; }
.filter-btn--active { font-weight: 500; }

/* ── Loading / Error / Empty states ──────────────────── */

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 60px 0;
  color: #6b7280;
  font-size: 14px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #27272a;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.error-state {
  text-align: center;
  padding: 60px 0;
}

.error-title { font-size: 16px; font-weight: 500; color: #ef4444; margin-bottom: 6px; }
.error-msg { font-size: 13px; color: #6b7280; margin-bottom: 16px; }

.retry-btn {
  padding: 8px 18px;
  background: transparent;
  border: 1px solid #27272a;
  border-radius: 8px;
  color: #ffffff;
  font-size: 13px;
  cursor: pointer;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
}

.empty-icon {
  font-size: 40px;
  color: #22c55e;
  margin-bottom: 16px;
}

.empty-title { font-size: 18px; font-weight: 500; margin-bottom: 8px; }
.empty-sub { font-size: 14px; color: #6b7280; margin-bottom: 20px; }

.empty-link {
  font-size: 14px;
  color: #6366f1;
  text-decoration: none;
}

.empty-link:hover { text-decoration: underline; }

/* ── Finding cards ────────────────────────────────────── */

.findings-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.finding-card {
  background: #0f0f11;
  border: 1px solid #1f1f23;
  border-radius: 12px;
  padding: 20px;
  border-left-width: 3px;
}

/* Left border colour matches severity */
.finding-card--critical { border-left-color: #ef4444; }
.finding-card--high     { border-left-color: #f97316; }
.finding-card--medium   { border-left-color: #eab308; }
.finding-card--low      { border-left-color: #22c55e; }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 12px;
}

.card-filename {
  font-size: 15px;
  font-weight: 500;
  color: #ffffff;
  margin-bottom: 3px;
}

.card-type {
  font-size: 12px;
  color: #6b7280;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

/* ── Severity badges ──────────────────────────────────── */

.severity-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 20px;
  letter-spacing: 0.05em;
}

.severity-badge--critical { background: rgba(239,68,68,.15); color: #f87171; }
.severity-badge--high     { background: rgba(249,115,22,.15); color: #fb923c; }
.severity-badge--medium   { background: rgba(234,179,8,.15);  color: #fbbf24; }
.severity-badge--low      { background: rgba(34,197,94,.15);  color: #4ade80; }

.risk-score {
  font-size: 12px;
  color: #52525b;
  white-space: nowrap;
}

.card-evidence {
  font-size: 13px;
  color: #9ca3af;
  line-height: 1.6;
  margin-bottom: 12px;
}

.card-action {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 14px;
  line-height: 1.5;
}

.action-label {
  font-weight: 500;
  color: #52525b;
  margin-right: 6px;
}

.action-text { color: #9ca3af; }

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* ── Status pills ─────────────────────────────────────── */

.status-pill {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 500;
}

.status-pill--open          { background: rgba(99,102,241,.15); color: #818cf8; }
.status-pill--resolved      { background: rgba(34,197,94,.15);  color: #4ade80; }
.status-pill--in_progress   { background: rgba(234,179,8,.15);  color: #fbbf24; }
.status-pill--accepted_risk { background: rgba(107,114,128,.15);color: #9ca3af; }

.approve-link {
  font-size: 13px;
  color: #6366f1;
  text-decoration: none;
  transition: color 0.15s;
}

.approve-link:hover { color: #818cf8; }
</style>