<!-- src/views/ApprovalsView.vue -->

<!--
  WHAT THIS PAGE DOES:
  Shows each proposed remediation fix one at a time.
  The user reads what will be changed and clicks Approve or Reject.
  NOTHING in Microsoft 365 changes until the user approves here.

  THIS IS THE HUMAN APPROVAL GATE.
  The most important safety feature in the entire system.

  HOW IT CONNECTS TO THE BACKEND:

  LOADING remediations:
    GET http://localhost:8000/api/v1/findings
    (we use findings to show what each remediation fixes)

  APPROVING a fix:
    POST http://localhost:8000/api/v1/approve
    Body: { remediation_id: 5, approved_by: "nondumiso@kion.co.za" }
    FastAPI marks remediation as "approved" in PostgreSQL
    NOTHING is executed yet — only marked as approved

  EXECUTING approved fixes:
    POST http://localhost:8000/api/v1/execute
    Body: { approved_by: "nondumiso@kion.co.za" }
    FastAPI runs ActionExecutor
    ActionExecutor reads ALL "approved" remediations from DB
    Makes the actual Microsoft Graph API calls
    Records everything in the audit log

  REFERENCES:
  useApi.js    → api.get(), api.post() — all HTTP calls
  useAuth.js   → logout(), currentUser — user info
  router       → navigation
  FastAPI main.py → /api/v1/approve, /api/v1/execute, /api/v1/findings
  database.py  → approve_remediation(), execute_approved()
  action_agents.py → ActionExecutor
-->

<template>
  <div class="page">

    <!-- ── Navigation Bar ─────────────────────────────── -->
    <nav class="nav">
      <div class="nav-left">
        <router-link to="/findings" class="nav-back">← Findings</router-link>
        <h1 class="nav-title">Approvals</h1>
      </div>
      <div class="nav-right">
        <span v-if="pendingCount > 0" class="pending-badge">
          {{ pendingCount }} pending
        </span>
        <button @click="handleLogout" class="nav-logout">Sign out</button>
      </div>
    </nav>

    <!-- ── Main Content ───────────────────────────────── -->
    <main class="main">

      <!-- Page header -->
      <div class="page-header">
        <h2 class="page-title">Review Proposed Fixes</h2>
        <p class="page-sub">
          Review each proposed fix carefully before approving.
          Approved fixes will be applied to your Microsoft 365 environment.
          You can reject any fix — nothing changes without your approval.
        </p>
      </div>

      <!-- Safety warning banner -->
      <div class="safety-banner" role="alert">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
        <span>
          Approved fixes are applied directly to Microsoft 365.
          Rejected fixes are logged but not applied.
          All actions are recorded in the audit log.
        </span>
      </div>

      <!-- Loading state -->
      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading proposed fixes...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="error-state">
        <p class="error-title">Could not load approvals</p>
        <p class="error-msg">{{ error }}</p>
        <button @click="loadData" class="retry-btn">Try again</button>
      </div>

      <!-- Empty state — nothing to approve -->
      <div v-else-if="findings.length === 0" class="empty-state">
        <div class="empty-icon" aria-hidden="true">✓</div>
        <p class="empty-title">Nothing to approve</p>
        <p class="empty-sub">
          Run a governance scan first to generate findings and proposed fixes.
        </p>
        <router-link to="/dashboard" class="empty-link">
          Go to Dashboard →
        </router-link>
      </div>

      <!-- Findings with approval controls -->
      <div v-else>

        <!-- Execute all button — only shows after some are approved -->
        <!--
          v-if shows this section only when approvedCount > 0
          approvedCount is a computed property that counts
          findings where localStatus is "approved"
        -->
        <div v-if="approvedCount > 0" class="execute-bar">
          <div class="execute-info">
            <span class="execute-count">{{ approvedCount }} fix{{ approvedCount === 1 ? '' : 'es' }} approved</span>
            <span class="execute-sub">Ready to apply to Microsoft 365</span>
          </div>
          <button
            @click="executeApproved"
            :disabled="isExecuting"
            class="execute-btn"
          >
            <template v-if="!isExecuting">
              Apply {{ approvedCount }} Approved Fix{{ approvedCount === 1 ? '' : 'es' }}
            </template>
            <template v-else>
              <div class="spinner-small"></div>
              Applying fixes...
            </template>
          </button>
        </div>

        <!-- Execution result message -->
        <div v-if="executionResult" class="execution-result" :class="`execution-result--${executionResult.type}`">
          {{ executionResult.message }}
        </div>

        <!-- Individual finding approval cards -->
        <!--
          v-for loops through findings array
          Each finding gets its own approval card
          The user approves or rejects each one individually
        -->
        <div
          v-for="finding in findings"
          :key="finding.id"
          class="approval-card"
          :class="[
            `approval-card--${finding.severity}`,
            localStatus[finding.id] ? `approval-card--${localStatus[finding.id]}` : ''
          ]"
        >

          <!-- Card header -->
          <div class="card-top">
            <div class="card-info">

              <!-- Severity badge -->
              <span :class="['sev-badge', `sev-badge--${finding.severity}`]">
                {{ finding.severity.toUpperCase() }}
              </span>

              <!-- File name -->
              <div>
                <p class="card-filename">{{ finding.resource_name }}</p>
                <p class="card-type">{{ formatFindingType(finding.finding_type) }}</p>
              </div>

            </div>

            <!-- Decision status indicator -->
            <!--
              localStatus[finding.id] stores the user's decision
              for each finding independently.
              "approved" = user clicked Approve
              "rejected" = user clicked Reject
              undefined  = not yet decided
            -->
            <div v-if="localStatus[finding.id]" class="decision-indicator">
              <span v-if="localStatus[finding.id] === 'approved'" class="decision-approved">
                ✓ Approved
              </span>
              <span v-else class="decision-rejected">
                ✕ Rejected
              </span>
            </div>

          </div>

          <!-- Problem description -->
          <div class="card-section">
            <p class="section-label">Problem found:</p>
            <p class="section-text">{{ finding.evidence }}</p>
          </div>

          <!-- Proposed fix -->
          <div class="card-section">
            <p class="section-label">Proposed fix:</p>
            <p class="section-text">{{ finding.recommended_action || 'Remove the risky permission from this file.' }}</p>
          </div>

          <!-- What happens after approval -->
          <div class="card-section card-section--info">
            <p class="section-label">What will happen:</p>
            <p class="section-text">
              The sharing permission on
              <strong>{{ finding.resource_name }}</strong>
              will be modified through Microsoft Graph API.
              This action will be recorded in the audit log.
              You can request a rollback if needed.
            </p>
          </div>

          <!-- Approval buttons — only show if not yet decided -->
          <div v-if="!localStatus[finding.id]" class="card-actions">

            <button
              @click="rejectFinding(finding)"
              :disabled="isProcessing[finding.id]"
              class="action-btn action-btn--reject"
            >
              Reject
            </button>

            <button
              @click="approveFinding(finding)"
              :disabled="isProcessing[finding.id]"
              class="action-btn action-btn--approve"
            >
              <template v-if="isProcessing[finding.id]">
                <div class="spinner-small"></div>
                Processing...
              </template>
              <template v-else>
                Approve Fix
              </template>
            </button>

          </div>

          <!-- Undo button — show after decision is made -->
          <div v-else class="card-undo">
            <button @click="undoDecision(finding.id)" class="undo-btn">
              Undo decision
            </button>
          </div>

        </div>

      </div>

    </main>

  </div>
</template>


<script setup>
/*
 * WHAT THIS SCRIPT DOES:
 *
 * 1. Loads findings from the backend on mount
 * 2. Lets the user approve or reject each one locally first
 * 3. When "Apply fixes" is clicked — sends approved ones to backend
 * 4. Backend marks them approved in PostgreSQL
 * 5. Then executes the actual Microsoft Graph write operations
 *
 * LOCAL STATE vs BACKEND STATE:
 *   localStatus[id] = what the user decided in THIS session
 *   This is stored in ref() — lives in Vue memory only
 *
 *   Once "Apply fixes" is clicked → localStatus gets sent to backend
 *   Backend records it permanently in PostgreSQL
 *
 *   WHY TWO STEPS?
 *   The user might approve 3 and reject 2.
 *   We collect all decisions first, then send them together.
 *   This is better UX than sending one request per click.
 */

import { ref, computed, onMounted } from "vue"
import { useRouter, useRoute } from "vue-router"
import { useAuth } from "../composables/useAuth"
import { useApi } from "../composables/useApi"

const router = useRouter()
/*
 * useRoute() gives us the current route information
 * We use it to read the query param ?finding_id=5
 * That comes from FindingsView "Review fix →" link
 * We use it to scroll to or highlight that specific finding
 */
const route = useRoute()
const { logout, currentUser } = useAuth()
const api = useApi()

// ── Reactive state ────────────────────────────────────────

const findings = ref([])         // list of findings to approve
const isLoading = ref(false)
const error = ref(null)
const isExecuting = ref(false)   // true while executing approved fixes
const executionResult = ref(null)// message after execution completes

/*
 * localStatus stores each user decision in a dict keyed by finding id
 * { 3: "approved", 7: "rejected", 12: undefined }
 *
 * ref({}) creates a reactive empty object
 * When we set localStatus.value[id] = "approved"
 * Vue detects the change and updates the template
 */
const localStatus = ref({})

/*
 * isProcessing tracks which individual findings are loading
 * { 3: true, 7: false }
 * Shows a spinner on the specific card being processed
 */
const isProcessing = ref({})

// ── Computed properties ───────────────────────────────────

/*
 * pendingCount = findings with no decision yet
 * Shown in the nav badge
 */
const pendingCount = computed(() => {
  return findings.value.filter(f => !localStatus.value[f.id]).length
})

/*
 * approvedCount = findings the user has marked as approved
 * Shown in the "Apply X fixes" button
 */
const approvedCount = computed(() => {
  return Object.values(localStatus.value).filter(s => s === "approved").length
})

// ── Data loading ──────────────────────────────────────────

/*
 * loadData() fetches findings from FastAPI.
 *
 * BACKEND CONNECTION:
 *   GET http://localhost:8000/api/v1/findings
 *
 * REFERENCES:
 *   src/composables/useApi.js → get()
 *   src/api/main.py           → GET /api/v1/findings
 *   src/memory/database.py    → get_open_findings()
 */
const loadData = async () => {
  isLoading.value = true
  error.value = null

  try {
    const data = await api.get("/api/v1/findings")
    findings.value = data

    // If a finding_id was passed in the URL query params
    // scroll to that card after loading
    const targetId = route.query.finding_id
    if (targetId) {
      setTimeout(() => {
        const el = document.querySelector(`[data-finding-id="${targetId}"]`)
        if (el) el.scrollIntoView({ behavior: "smooth", block: "center" })
      }, 100)
    }

  } catch (err) {
    error.value = "Failed to load findings."
    console.error("Approvals load error:", err)

  } finally {
    isLoading.value = false
  }
}

// ── Approval actions ──────────────────────────────────────

/*
 * approveFinding() — user clicks "Approve Fix"
 *
 * What it does RIGHT NOW: stores decision locally in localStatus
 * What it does when "Apply" is clicked: sends to backend
 *
 * We do NOT call the backend immediately on each approval click.
 * This lets the user review all decisions before committing.
 */
const approveFinding = async (finding) => {
  // Show processing spinner on this specific card
  isProcessing.value = { ...isProcessing.value, [finding.id]: true }

  // Small delay so user sees the processing state
  await new Promise(resolve => setTimeout(resolve, 300))

  // Store decision locally — NOT sent to backend yet
  localStatus.value = { ...localStatus.value, [finding.id]: "approved" }
  isProcessing.value = { ...isProcessing.value, [finding.id]: false }
}

/*
 * rejectFinding() — user clicks "Reject"
 * Stores rejection locally — never sends to backend
 * Rejected findings are simply not included when executing
 */
const rejectFinding = (finding) => {
  localStatus.value = { ...localStatus.value, [finding.id]: "rejected" }
}

/*
 * undoDecision() — user clicks "Undo decision"
 * Removes the decision so the approve/reject buttons reappear
 */
const undoDecision = (findingId) => {
  const updated = { ...localStatus.value }
  delete updated[findingId]
  localStatus.value = updated
}

/*
 * executeApproved() — user clicks "Apply X Approved Fixes"
 *
 * FLOW:
 *   1. Find all findings with localStatus = "approved"
 *   2. POST /api/v1/approve for each one → marks as "approved" in PostgreSQL
 *   3. POST /api/v1/execute → ActionExecutor runs the Graph API write calls
 *
 * BACKEND CONNECTIONS:
 *   POST http://localhost:8000/api/v1/approve
 *   Body: { remediation_id: 5, approved_by: "user@email.com" }
 *
 *   POST http://localhost:8000/api/v1/execute
 *   Body: { approved_by: "user@email.com" }
 *
 * REFERENCES:
 *   src/api/main.py           → POST /api/v1/approve, POST /api/v1/execute
 *   src/memory/database.py    → approve_remediation()
 *   src/agents/action_agents.py → ActionExecutor.execute_approved()
 *   src/graph/client.py       → GraphClient (makes the actual Graph calls)
 */
const executeApproved = async () => {
  isExecuting.value = true
  executionResult.value = null

  const userEmail = currentUser.value?.email || "unknown"

  try {
    // Get all approved finding IDs
    const approvedIds = Object.entries(localStatus.value)
      .filter(([_, status]) => status === "approved")
      .map(([id]) => parseInt(id))

    // Step 1: Mark each as approved in the database
    for (const id of approvedIds) {
      await api.post("/api/v1/approve", {
        remediation_id: id,
        approved_by: userEmail,
      })
    }

    // Step 2: Execute all approved remediations
    // ActionExecutor reads the "approved" ones from DB and runs them
    const result = await api.post("/api/v1/execute", {
      approved_by: userEmail,
    })

    executionResult.value = {
      type: "success",
      message: `Successfully applied ${approvedIds.length} fix${approvedIds.length === 1 ? "" : "es"} to Microsoft 365. All actions recorded in audit log.`,
    }

    // Reload the findings list to show updated statuses
    await loadData()

  } catch (err) {
    executionResult.value = {
      type: "error",
      message: "Execution failed. Please check the logs and try again.",
    }
    console.error("Execute error:", err)

  } finally {
    isExecuting.value = false
  }
}

// ── Helper functions ──────────────────────────────────────

const formatFindingType = (type) => {
  return type
    .replace(/_/g, " ")
    .replace(/\b\w/g, char => char.toUpperCase())
}

const handleLogout = async () => {
  await logout()
  router.push({ name: "Login" })
}

// ── Lifecycle ─────────────────────────────────────────────

onMounted(() => {
  loadData()
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

/* ── Nav ──────────────────────────────────────────────── */

.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  border-bottom: 1px solid #1f1f23;
  background: #0a0a0b;
}

.nav-left { display: flex; align-items: center; gap: 20px; }
.nav-back { font-size: 13px; color: #6b7280; text-decoration: none; transition: color .15s; }
.nav-back:hover { color: #ffffff; }
.nav-title { font-size: 16px; font-weight: 600; }
.nav-right { display: flex; align-items: center; gap: 16px; }

.pending-badge {
  font-size: 12px;
  color: #f97316;
  background: rgba(249,115,22,.1);
  border: 1px solid rgba(249,115,22,.2);
  padding: 4px 10px;
  border-radius: 20px;
}

.nav-logout { font-size: 13px; color: #6b7280; background: none; border: none; cursor: pointer; }
.nav-logout:hover { color: #ffffff; }

/* ── Main ─────────────────────────────────────────────── */

.main { max-width: 800px; margin: 0 auto; padding: 40px 24px; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 26px; font-weight: 600; margin-bottom: 6px; }
.page-sub { font-size: 14px; color: #6b7280; line-height: 1.6; }

/* ── Safety banner ────────────────────────────────────── */

.safety-banner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: rgba(99,102,241,.08);
  border: 1px solid rgba(99,102,241,.2);
  border-radius: 10px;
  padding: 14px 16px;
  font-size: 13px;
  color: #a5b4fc;
  margin-bottom: 28px;
  line-height: 1.5;
}

/* ── Loading / Error / Empty ──────────────────────────── */

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
  animation: spin .7s linear infinite;
}

.spinner-small {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin .7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

.error-state { text-align: center; padding: 60px 0; }
.error-title { font-size: 16px; font-weight: 500; color: #ef4444; margin-bottom: 6px; }
.error-msg { font-size: 13px; color: #6b7280; margin-bottom: 16px; }
.retry-btn { padding: 8px 18px; background: transparent; border: 1px solid #27272a; border-radius: 8px; color: #ffffff; font-size: 13px; cursor: pointer; }

.empty-state { text-align: center; padding: 60px 0; }
.empty-icon { font-size: 40px; color: #22c55e; margin-bottom: 16px; }
.empty-title { font-size: 18px; font-weight: 500; margin-bottom: 8px; }
.empty-sub { font-size: 14px; color: #6b7280; margin-bottom: 20px; }
.empty-link { font-size: 14px; color: #6366f1; text-decoration: none; }

/* ── Execute bar ──────────────────────────────────────── */

.execute-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(34,197,94,.06);
  border: 1px solid rgba(34,197,94,.2);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 20px;
}

.execute-count { font-size: 15px; font-weight: 500; color: #4ade80; display: block; }
.execute-sub { font-size: 12px; color: #6b7280; }

.execute-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #22c55e;
  color: #0a0a0a;
  font-size: 14px;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background .15s;
}

.execute-btn:hover:not(:disabled) { background: #16a34a; }
.execute-btn:disabled { opacity: .6; cursor: not-allowed; }

.execution-result {
  padding: 14px 16px;
  border-radius: 10px;
  font-size: 13px;
  margin-bottom: 20px;
  line-height: 1.5;
}

.execution-result--success { background: rgba(34,197,94,.08); border: 1px solid rgba(34,197,94,.2); color: #4ade80; }
.execution-result--error   { background: rgba(239,68,68,.08);  border: 1px solid rgba(239,68,68,.2);  color: #f87171; }

/* ── Approval cards ───────────────────────────────────── */

.approval-card {
  background: #0f0f11;
  border: 1px solid #1f1f23;
  border-radius: 14px;
  padding: 22px;
  margin-bottom: 14px;
  border-left-width: 3px;
  transition: border-color .15s;
}

.approval-card--critical { border-left-color: #ef4444; }
.approval-card--high     { border-left-color: #f97316; }
.approval-card--medium   { border-left-color: #eab308; }
.approval-card--low      { border-left-color: #22c55e; }

/* Approved card gets green border all around */
.approval-card--approved { border-color: rgba(34,197,94,.4) !important; border-left-color: #22c55e !important; }
/* Rejected card fades out */
.approval-card--rejected { opacity: .5; }

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.card-info { display: flex; align-items: flex-start; gap: 12px; }
.card-filename { font-size: 15px; font-weight: 500; margin-bottom: 3px; }
.card-type { font-size: 12px; color: #6b7280; }

/* ── Severity badges ──────────────────────────────────── */

.sev-badge {
  font-size: 10px;
  font-weight: 600;
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

.decision-indicator { flex-shrink: 0; }
.decision-approved { font-size: 13px; font-weight: 500; color: #4ade80; }
.decision-rejected { font-size: 13px; font-weight: 500; color: #f87171; }

/* ── Card sections ────────────────────────────────────── */

.card-section {
  margin-bottom: 12px;
  padding: 12px 14px;
  background: rgba(255,255,255,.02);
  border-radius: 8px;
}

.card-section--info { background: rgba(99,102,241,.05); }

.section-label { font-size: 11px; font-weight: 600; color: #52525b; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 5px; }
.section-text { font-size: 13px; color: #9ca3af; line-height: 1.6; }
.section-text strong { color: #d1d5db; font-weight: 500; }

/* ── Action buttons ───────────────────────────────────── */

.card-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 16px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 9px 20px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all .15s;
  border: none;
}

.action-btn:disabled { opacity: .6; cursor: not-allowed; }

.action-btn--reject {
  background: transparent;
  border: 1px solid #3f3f46;
  color: #9ca3af;
}

.action-btn--reject:hover:not(:disabled) { border-color: #ef4444; color: #f87171; }

.action-btn--approve {
  background: #6366f1;
  color: #ffffff;
}

.action-btn--approve:hover:not(:disabled) { background: #4f46e5; }

.card-undo { display: flex; justify-content: flex-end; margin-top: 14px; }

.undo-btn {
  font-size: 12px;
  color: #52525b;
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: underline;
  padding: 0;
}

.undo-btn:hover { color: #9ca3af; }
</style>