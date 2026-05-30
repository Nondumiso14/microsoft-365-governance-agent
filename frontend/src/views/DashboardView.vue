<!-- src/views/DashboardView.vue -->

<!--
  ENHANCED DASHBOARD — What was added and why:

  1. USER PROFILE BAR
     Shows logged-in user's name, email, initials avatar.
     Fetched from GET /auth/me on mount.
     Makes the app feel personal and enterprise-grade.

  2. SCAN PROGRESS STEPS
     Instead of just a spinning button — shows exactly what
     the system is doing step by step as it runs.
     Each step lights up as it completes.
     Far more impressive to watch in a demo.

  3. RISK SUMMARY CARDS
     Always visible (not just after scan).
     Show 0 before scan, real numbers after.
     Four cards: Files Scanned, Critical, High, Medium.

  4. QUICK NAVIGATION PANEL
     Three action buttons at the top right.
     Links to Findings and Approvals pages.
     Shows there is a full system behind the dashboard.

  BACKEND CONNECTIONS:
    GET /auth/me          → loads user profile
    GET /api/v1/scan/demo → runs the scan
    Both called via useApi composable with Bearer token
-->

<template>
  <div class="page">

    <!-- ── Top Navigation Bar ─────────────────────────── -->
    <nav class="nav">
      <div class="nav-left">

        <!-- App logo and name -->
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

      <div class="nav-right">

        <!-- Quick navigation buttons -->
        <router-link to="/findings" class="nav-link">
          Findings
          <span v-if="findings.length > 0" class="nav-badge">
            {{ findings.length }}
          </span>
        </router-link>
        <router-link to="/approvals" class="nav-link">
          Approvals
        </router-link>

        <!-- User profile -->
        <!--
          v-if shows profile only when user data is loaded
          user.initials computed from display name
        -->
        <div v-if="user" class="user-profile">
          <div class="user-avatar">{{ userInitials }}</div>
          <div class="user-info">
            <p class="user-name">{{ user.displayName || "User" }}</p>
            <p class="user-email">{{ user.mail || user.userPrincipalName || "" }}</p>
          </div>
        </div>

        <button @click="handleLogout" class="logout-btn">
          Sign out
        </button>

      </div>
    </nav>

    <!-- ── Main Content ───────────────────────────────── -->
    <main class="main">

      <!-- Page header -->
      <div class="page-header">
        <div>
          <h2 class="page-title">Governance Dashboard</h2>
          <p class="page-sub">
            Scan your Microsoft 365 environment for security risks
            <!-- Last scan info — only shows after a scan -->
            <span v-if="lastScanTime" class="last-scan">
              · Last scanned {{ lastScanTime }}
            </span>
          </p>
        </div>

        <!-- Scan trigger button -->
        <button
          @click="runScan"
          :disabled="isScanning"
          class="scan-btn"
          :class="{ 'scan-btn--scanning': isScanning }"
        >
          <template v-if="!isScanning">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" aria-hidden="true">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.35-4.35"/>
            </svg>
            Run Governance Scan
          </template>
          <template v-else>
            <div class="btn-spinner" aria-hidden="true"></div>
            Scanning...
          </template>
        </button>
      </div>

      <!-- ── Risk Summary Cards ──────────────────────── -->
      <!--
        Always visible — shows 0 before scan, real numbers after.
        :class adds highlight border when count > 0
      -->
      <div class="stats-grid">

        <div class="stat-card">
          <div class="stat-icon stat-icon--files" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
          </div>
          <div class="stat-content">
            <p class="stat-label">Files Scanned</p>
            <p class="stat-value">{{ totalFiles }}</p>
          </div>
        </div>

        <div class="stat-card" :class="{ 'stat-card--critical': criticalCount > 0 }">
          <div class="stat-icon stat-icon--critical" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
          <div class="stat-content">
            <p class="stat-label critical">Critical</p>
            <p class="stat-value critical">{{ criticalCount }}</p>
          </div>
        </div>

        <div class="stat-card" :class="{ 'stat-card--high': highCount > 0 }">
          <div class="stat-icon stat-icon--high" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <div class="stat-content">
            <p class="stat-label high">High</p>
            <p class="stat-value high">{{ highCount }}</p>
          </div>
        </div>

        <div class="stat-card" :class="{ 'stat-card--medium': mediumCount > 0 }">
          <div class="stat-icon stat-icon--medium" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <div class="stat-content">
            <p class="stat-label medium">Medium</p>
            <p class="stat-value medium">{{ mediumCount }}</p>
          </div>
        </div>

      </div>

      <!-- ── Scan Progress Panel ─────────────────────── -->
      <!--
        v-if shows this ONLY while scanning or just after scan
        Shows each step lighting up as it completes
        This is the most impressive part of the demo
      -->
      <div v-if="isScanning || scanComplete" class="progress-panel">

        <div class="progress-header">
          <h3 class="progress-title">
            {{ isScanning ? "Scan In Progress" : "Scan Complete" }}
          </h3>
          <span v-if="!isScanning" class="progress-done-badge">✓ Done</span>
        </div>

        <!-- Step list -->
        <!--
          v-for loops through scanSteps array
          Each step has: label, status (pending/active/done)
          :class applies different styles based on status
        -->
        <div class="steps-list">
          <div
            v-for="(step, index) in scanSteps"
            :key="index"
            :class="['step', `step--${step.status}`]"
          >

            <!-- Step indicator -->
            <div class="step-indicator" aria-hidden="true">
              <template v-if="step.status === 'done'">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" stroke-width="3">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </template>
              <template v-else-if="step.status === 'active'">
                <div class="step-spinner"></div>
              </template>
              <template v-else>
                <span class="step-number">{{ index + 1 }}</span>
              </template>
            </div>

            <!-- Step label and detail -->
            <div class="step-content">
              <p class="step-label">{{ step.label }}</p>
              <p v-if="step.detail" class="step-detail">{{ step.detail }}</p>
            </div>

          </div>
        </div>

      </div>

      <!-- ── Error Message ───────────────────────────── -->
      <div v-if="error" class="error-box" role="alert">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" aria-hidden="true">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        {{ error }}
      </div>

      <!-- ── Risk Distribution Bar ───────────────────── -->
      <!--
        Only shows after scan with findings
        Visual bar showing proportion of each severity
      -->
      <div v-if="scanComplete && findings.length > 0" class="risk-bar-section">
        <div class="risk-bar-header">
          <h3 class="risk-bar-title">Risk Distribution</h3>
          <span class="risk-bar-total">{{ findings.length }} total findings</span>
        </div>
        <div class="risk-bar">
          <div
            v-if="criticalCount > 0"
            class="risk-bar-segment risk-bar-segment--critical"
            :style="{ width: pct(criticalCount) }"
            :title="`Critical: ${criticalCount}`"
          ></div>
          <div
            v-if="highCount > 0"
            class="risk-bar-segment risk-bar-segment--high"
            :style="{ width: pct(highCount) }"
            :title="`High: ${highCount}`"
          ></div>
          <div
            v-if="mediumCount > 0"
            class="risk-bar-segment risk-bar-segment--medium"
            :style="{ width: pct(mediumCount) }"
            :title="`Medium: ${mediumCount}`"
          ></div>
          <div
            v-if="lowCount > 0"
            class="risk-bar-segment risk-bar-segment--low"
            :style="{ width: pct(lowCount) }"
            :title="`Low: ${lowCount}`"
          ></div>
        </div>
        <div class="risk-bar-legend">
          <span v-if="criticalCount > 0" class="legend-item">
            <span class="legend-dot legend-dot--critical"></span>
            Critical ({{ criticalCount }})
          </span>
          <span v-if="highCount > 0" class="legend-item">
            <span class="legend-dot legend-dot--high"></span>
            High ({{ highCount }})
          </span>
          <span v-if="mediumCount > 0" class="legend-item">
            <span class="legend-dot legend-dot--medium"></span>
            Medium ({{ mediumCount }})
          </span>
          <span v-if="lowCount > 0" class="legend-item">
            <span class="legend-dot legend-dot--low"></span>
            Low ({{ lowCount }})
          </span>
        </div>
      </div>

      <!-- ── Findings List ───────────────────────────── -->
      <div v-if="findings.length > 0" class="findings-section">

        <div class="findings-header">
          <h3 class="findings-title">Findings ({{ findings.length }})</h3>
          <router-link to="/findings" class="findings-link">
            View all in Findings →
          </router-link>
        </div>

        <div
          v-for="(finding, index) in findings.slice(0, 5)"
          :key="index"
          class="finding-card"
          :class="`finding-card--${finding.severity}`"
        >
          <div class="finding-row">
            <div class="finding-left">
              <span :class="['sev-badge', `sev-badge--${finding.severity}`]">
                {{ finding.severity.toUpperCase() }}
              </span>
              <div>
                <p class="finding-name">{{ finding.resource_name }}</p>
                <p class="finding-evidence">{{ finding.evidence }}</p>
              </div>
            </div>
            <router-link
              to="/approvals"
              class="finding-action"
            >
              Review fix →
            </router-link>
          </div>
        </div>

        <!-- Show more link if more than 5 findings -->
        <div v-if="findings.length > 5" class="show-more">
          <router-link to="/findings" class="show-more-link">
            + {{ findings.length - 5 }} more findings in Findings view
          </router-link>
        </div>

      </div>

      <!-- Empty state — scan ran but no risks found -->
      <div v-if="scanComplete && findings.length === 0" class="empty-state">
        <div class="empty-icon" aria-hidden="true">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none"
               stroke="#22c55e" stroke-width="1.5">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <polyline points="9 12 11 14 15 10"/>
          </svg>
        </div>
        <p class="empty-title">No risks found</p>
        <p class="empty-sub">
          Your OneDrive files appear to be properly secured.
          Try creating a test file with anonymous sharing to see findings.
        </p>
      </div>

      <!-- Pre-scan state — before any scan is run -->
      <div v-if="!isScanning && !scanComplete && !error" class="prescan-state">
        <div class="prescan-content">
          <div class="prescan-icon" aria-hidden="true">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none"
                 stroke="#6366f1" stroke-width="1.5">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.35-4.35"/>
            </svg>
          </div>
          <p class="prescan-title">Ready to scan</p>
          <p class="prescan-sub">
            Click "Run Governance Scan" to analyse your Microsoft 365
            environment for security risks.
          </p>
          <div class="prescan-checks">
            <div class="prescan-check">
              <span class="check-dot check-dot--green"></span>
              Detects anonymous sharing links
            </div>
            <div class="prescan-check">
              <span class="check-dot check-dot--orange"></span>
              Identifies external user access
            </div>
            <div class="prescan-check">
              <span class="check-dot check-dot--yellow"></span>
              Flags organisation-wide exposure
            </div>
            <div class="prescan-check">
              <span class="check-dot check-dot--purple"></span>
              Scores each risk Critical → Low
            </div>
          </div>
        </div>
      </div>

    </main>

  </div>
</template>


<script setup>
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import { useAuth } from "../composables/useAuth"
import { useApi } from "../composables/useApi"

const router = useRouter()
const { logout } = useAuth()
const api = useApi()

// ── State ──────────────────────────────────────────────
const findings   = ref([])
const isScanning = ref(false)
const scanComplete = ref(false)
const error      = ref(null)
const totalFiles = ref(0)
const lastScanTime = ref(null)
const user       = ref(null)

// Scan progress steps
// Each step has a label, detail (shown when active/done), and status
const scanSteps = ref([
  { label: "Connecting to Microsoft 365",   detail: "",                    status: "pending" },
  { label: "Discovering OneDrive files",    detail: "",                    status: "pending" },
  { label: "Reading file permissions",      detail: "",                    status: "pending" },
  { label: "Classifying risk levels",       detail: "",                    status: "pending" },
  { label: "Generating findings report",    detail: "",                    status: "pending" },
])

// ── Computed ───────────────────────────────────────────
const criticalCount = computed(() =>
  findings.value.filter(f => f.severity === "critical").length
)
const highCount = computed(() =>
  findings.value.filter(f => f.severity === "high").length
)
const mediumCount = computed(() =>
  findings.value.filter(f => f.severity === "medium").length
)
const lowCount = computed(() =>
  findings.value.filter(f => f.severity === "low").length
)

/*
 * userInitials — extracts initials from display name
 * "Nondumiso Shange" → "NS"
 * Used in the avatar circle in the nav
 */
const userInitials = computed(() => {
  if (!user.value?.displayName) return "U"
  return user.value.displayName
    .split(" ")
    .map(n => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)
})

// ── Helper functions ───────────────────────────────────

/*
 * pct() — calculates percentage for risk distribution bar
 * e.g. 3 critical out of 10 total → "30%"
 */
const pct = (count) => {
  if (!findings.value.length) return "0%"
  return `${Math.round((count / findings.value.length) * 100)}%`
}

/*
 * activateStep() — sets a step to "active" status
 * with a delay so the user can see each step lighting up
 */
const activateStep = (index, detail = "") => {
  scanSteps.value[index].status = "active"
  scanSteps.value[index].detail = detail
}

/*
 * completeStep() — marks a step as done
 */
const completeStep = (index, detail = "") => {
  scanSteps.value[index].status = "done"
  scanSteps.value[index].detail = detail
}

/*
 * resetSteps() — resets all steps to pending for a new scan
 */
const resetSteps = () => {
  scanSteps.value.forEach(step => {
    step.status = "pending"
    step.detail = ""
  })
}

/*
 * sleep() — pause for N milliseconds
 * Used to create visible step-by-step progress animation
 */
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

// ── User profile loading ───────────────────────────────
/*
 * loadUser() — fetches the current user's profile
 *
 * BACKEND CONNECTION:
 *   GET http://localhost:8000/auth/me
 *   Returns: { authenticated: true, ... }
 *
 * NOTE: /auth/me currently returns basic auth status.
 * When the full user profile endpoint is added it will
 * return displayName, mail, jobTitle etc.
 * For now we show a placeholder name from sessionStorage.
 */
const loadUser = async () => {
  try {
    const data = await api.get("/auth/me")
    if (data.authenticated) {
      // Placeholder — replace with real profile when /auth/me returns it
      user.value = {
        displayName: "Nondumiso Shange",
        mail: "nondumiso@kion.co.za",
      }
    }
  } catch (err) {
    // Non-critical — user profile is cosmetic only
    console.warn("Could not load user profile:", err)
  }
}

// ── Scan function ──────────────────────────────────────
/*
 * runScan() — runs the OneDrive governance scan
 *
 * WHAT IT DOES:
 *   1. Resets all state
 *   2. Animates through the 5 progress steps with delays
 *   3. Calls the real backend scan endpoint
 *   4. Displays findings when complete
 *
 * BACKEND CONNECTION:
 *   GET http://localhost:8000/api/v1/scan/demo
 *   Returns: { message, findings[], total_files_scanned }
 *
 * WHY THE DELAYS?
 *   The scan itself is fast (2-3 seconds).
 *   The step delays make the process visible and understandable.
 *   Without them all steps flash instantly — hard to follow.
 */
const runScan = async () => {
  isScanning.value  = true
  scanComplete.value = false
  error.value       = null
  findings.value    = []
  totalFiles.value  = 0
  resetSteps()

  try {
    // Step 1 — Connecting
    activateStep(0, "Authenticating with Microsoft 365...")
    await sleep(800)
    completeStep(0, "Connected")

    // Step 2 — Discovering files
    activateStep(1, "Reading OneDrive root and subfolders...")
    await sleep(600)

    // Step 3 — Reading permissions (run actual API call here)
    activateStep(2, "Checking sharing links and user access...")

    // REAL API CALL — happens during step 3
    const result = await api.get("/api/v1/scan/demo")
    completeStep(1, `${result.total_files_scanned || "—"} files found`)
    completeStep(2, "Permissions analysed")

    // Step 4 — Classifying
    activateStep(3, "Applying risk scoring rules...")
    await sleep(500)
    completeStep(3, `${result.findings?.length || 0} risks identified`)

    // Step 5 — Report
    activateStep(4, "Building findings report...")
    await sleep(400)
    completeStep(4, "Report ready")

    // Update state with results
    findings.value    = result.findings || []
    totalFiles.value  = result.total_files_scanned || findings.value.length
    lastScanTime      = "just now"

    // Store last scan time as readable string
    const now = new Date()
    lastScanTime.value = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })

    scanComplete.value = true

  } catch (err) {
    error.value = "Scan failed. Make sure you are logged in and try again."
    console.error("Scan error:", err)
    resetSteps()
  } finally {
    isScanning.value = false
  }
}

// ── Logout ─────────────────────────────────────────────
const handleLogout = async () => {
  await logout()
  router.push({ name: "Login" })
}

// ── On mount ───────────────────────────────────────────
/*
 * onMounted runs once when this page first appears.
 * Load the user profile so the nav shows their name.
 */
onMounted(() => {
  loadUser()
})
</script>


<style scoped>
:global(*) { margin: 0; padding: 0; box-sizing: border-box; }
:global(html), :global(body), :global(#app) { height: 100%; }

.page {
  min-height: 100vh;
  background: #030303;
  color: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ── Navigation ───────────────────────────────────────── */

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
  z-index: 10;
}

.nav-left { display: flex; align-items: center; gap: 24px; }

.app-brand { display: flex; align-items: center; gap: 10px; }
.brand-icon {
  width: 32px; height: 32px;
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
}
.brand-name { font-size: 14px; font-weight: 600; color: #ffffff; }

.nav-right { display: flex; align-items: center; gap: 16px; }

.nav-link {
  font-size: 13px;
  color: #6b7280;
  text-decoration: none;
  padding: 5px 10px;
  border-radius: 6px;
  transition: all 0.15s;
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
}
.nav-link:hover { color: #ffffff; background: rgba(255,255,255,.05); }

.nav-badge {
  background: #ef4444;
  color: #ffffff;
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 10px;
}

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
  width: 30px; height: 30px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; color: #ffffff;
  flex-shrink: 0;
}

.user-info { display: flex; flex-direction: column; gap: 1px; }
.user-name  { font-size: 12px; font-weight: 500; color: #ffffff; line-height: 1; }
.user-email { font-size: 10px; color: #6b7280; line-height: 1; }

.logout-btn {
  font-size: 12px;
  color: #6b7280;
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px 8px;
  border-radius: 6px;
  transition: color 0.15s;
}
.logout-btn:hover { color: #ffffff; }

/* ── Main ─────────────────────────────────────────────── */

.main {
  max-width: 1100px;
  margin: 0 auto;
  padding: 36px 28px 60px;
}

/* ── Page header ──────────────────────────────────────── */

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 28px;
  gap: 16px;
}

.page-title {
  font-size: 26px;
  font-weight: 600;
  margin-bottom: 4px;
}

.page-sub {
  font-size: 13px;
  color: #6b7280;
}

.last-scan { color: #52525b; font-size: 12px; }

/* ── Scan button ──────────────────────────────────────── */

.scan-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 11px 22px;
  background: #6366f1;
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s;
  white-space: nowrap;
  flex-shrink: 0;
}
.scan-btn:hover:not(:disabled) { background: #4f46e5; }
.scan-btn:active:not(:disabled) { transform: scale(0.97); }
.scan-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.scan-btn--scanning { background: #3730a3; }

.btn-spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* ── Stats grid ───────────────────────────────────────── */

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}

.stat-card {
  background: #0f0f11;
  border: 1px solid #1f1f23;
  border-radius: 12px;
  padding: 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  transition: border-color 0.2s;
}

.stat-card--critical { border-color: rgba(239,68,68,.4); }
.stat-card--high     { border-color: rgba(249,115,22,.4); }
.stat-card--medium   { border-color: rgba(234,179,8,.4); }

.stat-icon {
  width: 38px; height: 38px;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.stat-icon--files    { background: rgba(99,102,241,.15); color: #818cf8; }
.stat-icon--critical { background: rgba(239,68,68,.15);  color: #f87171; }
.stat-icon--high     { background: rgba(249,115,22,.15); color: #fb923c; }
.stat-icon--medium   { background: rgba(234,179,8,.15);  color: #fbbf24; }

.stat-content { display: flex; flex-direction: column; gap: 3px; }

.stat-label {
  font-size: 12px;
  color: #6b7280;
}
.stat-label.critical { color: #f87171; }
.stat-label.high     { color: #fb923c; }
.stat-label.medium   { color: #fbbf24; }

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #ffffff;
  line-height: 1;
}
.stat-value.critical { color: #f87171; }
.stat-value.high     { color: #fb923c; }
.stat-value.medium   { color: #fbbf24; }

/* ── Scan progress panel ──────────────────────────────── */

.progress-panel {
  background: #0f0f11;
  border: 1px solid #27272a;
  border-radius: 14px;
  padding: 22px 24px;
  margin-bottom: 24px;
}

.progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.progress-title { font-size: 14px; font-weight: 600; color: #ffffff; }

.progress-done-badge {
  font-size: 12px;
  font-weight: 500;
  color: #4ade80;
  background: rgba(34,197,94,.1);
  padding: 3px 10px;
  border-radius: 20px;
  border: 1px solid rgba(34,197,94,.2);
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.step {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  transition: background 0.2s;
}

.step--pending { opacity: 0.35; }
.step--active  { background: rgba(99,102,241,.08); opacity: 1; }
.step--done    { opacity: 0.7; }

.step-indicator {
  width: 24px; height: 24px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 600;
}

.step--pending .step-indicator {
  background: #1f1f23;
  color: #52525b;
}
.step--active .step-indicator {
  background: rgba(99,102,241,.2);
  color: #6366f1;
}
.step--done .step-indicator {
  background: rgba(34,197,94,.15);
  color: #4ade80;
}

.step-spinner {
  width: 12px; height: 12px;
  border: 2px solid rgba(99,102,241,.3);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.step-content { display: flex; flex-direction: column; gap: 2px; }
.step-label  { font-size: 13px; font-weight: 500; color: #ffffff; }
.step-detail { font-size: 11px; color: #6b7280; }
.step-number { font-size: 11px; }

/* ── Error box ────────────────────────────────────────── */

.error-box {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(239,68,68,.08);
  border: 1px solid rgba(239,68,68,.25);
  border-radius: 10px;
  padding: 14px 16px;
  font-size: 13px;
  color: #f87171;
  margin-bottom: 24px;
}

/* ── Risk distribution bar ────────────────────────────── */

.risk-bar-section { margin-bottom: 28px; }

.risk-bar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.risk-bar-title { font-size: 14px; font-weight: 600; }
.risk-bar-total { font-size: 12px; color: #6b7280; }

.risk-bar {
  height: 8px;
  background: #1f1f23;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  margin-bottom: 10px;
}

.risk-bar-segment { height: 100%; transition: width 0.5s ease; }
.risk-bar-segment--critical { background: #ef4444; }
.risk-bar-segment--high     { background: #f97316; }
.risk-bar-segment--medium   { background: #eab308; }
.risk-bar-segment--low      { background: #22c55e; }

.risk-bar-legend { display: flex; gap: 16px; flex-wrap: wrap; }

.legend-item {
  display: flex; align-items: center;
  gap: 6px; font-size: 12px; color: #6b7280;
}

.legend-dot {
  width: 8px; height: 8px;
  border-radius: 50%; flex-shrink: 0;
}
.legend-dot--critical { background: #ef4444; }
.legend-dot--high     { background: #f97316; }
.legend-dot--medium   { background: #eab308; }
.legend-dot--low      { background: #22c55e; }

/* ── Findings list ────────────────────────────────────── */

.findings-section { margin-top: 4px; }

.findings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.findings-title { font-size: 16px; font-weight: 600; }

.findings-link {
  font-size: 13px;
  color: #6366f1;
  text-decoration: none;
  transition: color 0.15s;
}
.findings-link:hover { color: #818cf8; }

.finding-card {
  background: #0f0f11;
  border: 1px solid #1f1f23;
  border-left-width: 3px;
  border-radius: 10px;
  padding: 14px 18px;
  margin-bottom: 10px;
}
.finding-card--critical { border-left-color: #ef4444; }
.finding-card--high     { border-left-color: #f97316; }
.finding-card--medium   { border-left-color: #eab308; }
.finding-card--low      { border-left-color: #22c55e; }

.finding-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.finding-left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.finding-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.finding-evidence {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.finding-action {
  font-size: 12px;
  color: #6366f1;
  text-decoration: none;
  white-space: nowrap;
  transition: color 0.15s;
  flex-shrink: 0;
}
.finding-action:hover { color: #818cf8; }

.sev-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 4px;
  letter-spacing: .05em;
  flex-shrink: 0;
  margin-top: 2px;
}
.sev-badge--critical { background: rgba(239,68,68,.15); color: #f87171; }
.sev-badge--high     { background: rgba(249,115,22,.15); color: #fb923c; }
.sev-badge--medium   { background: rgba(234,179,8,.15);  color: #fbbf24; }
.sev-badge--low      { background: rgba(34,197,94,.15);  color: #4ade80; }

.show-more { text-align: center; padding: 12px; }
.show-more-link {
  font-size: 13px;
  color: #52525b;
  text-decoration: none;
  transition: color 0.15s;
}
.show-more-link:hover { color: #9ca3af; }

/* ── Empty state ──────────────────────────────────────── */

.empty-state {
  text-align: center;
  padding: 60px 0;
}
.empty-icon { margin-bottom: 16px; }
.empty-title { font-size: 18px; font-weight: 500; color: #22c55e; margin-bottom: 8px; }
.empty-sub { font-size: 13px; color: #6b7280; line-height: 1.6; max-width: 400px; margin: 0 auto; }

/* ── Pre-scan state ───────────────────────────────────── */

.prescan-state {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.prescan-content {
  text-align: center;
  max-width: 420px;
}

.prescan-icon { margin-bottom: 16px; }
.prescan-title { font-size: 18px; font-weight: 500; margin-bottom: 8px; }
.prescan-sub { font-size: 13px; color: #6b7280; line-height: 1.6; margin-bottom: 24px; }

.prescan-checks {
  display: flex;
  flex-direction: column;
  gap: 10px;
  text-align: left;
  background: #0f0f11;
  border: 1px solid #1f1f23;
  border-radius: 12px;
  padding: 18px 20px;
}

.prescan-check {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #9ca3af;
}

.check-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.check-dot--green  { background: #22c55e; }
.check-dot--orange { background: #f97316; }
.check-dot--yellow { background: #eab308; }
.check-dot--purple { background: #6366f1; }

/* ── Responsive ───────────────────────────────────────── */

@media (max-width: 768px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .user-info { display: none; }
  .page-header { flex-direction: column; align-items: flex-start; }
}
</style>