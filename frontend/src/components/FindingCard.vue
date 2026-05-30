<!-- src/components/FindingCard.vue -->

<!--
  WHAT THIS COMPONENT IS:
  A reusable card that displays one security finding.
  Used in DashboardView, FindingsView, and ApprovalsView.

  WHY A SEPARATE COMPONENT?
  All three pages show finding cards. Without this component
  the same card HTML is copied three times across three files.
  If you want to change how a card looks — you change it once here.

  HOW TO USE IT:
    import FindingCard from "../components/FindingCard.vue"

    <FindingCard
      :finding="finding"
      show-action
      action-label="Review fix →"
      action-to="/approvals"
    />

  PROPS:
    finding     — object  — the finding data object (required)
    showAction  — boolean — whether to show the action link
    actionLabel — string  — text on the action link
    actionTo    — string  — router path for the action link

  WHAT A FINDING OBJECT LOOKS LIKE:
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
-->

<template>
  <div
    class="card"
    :class="`card--${finding.severity}`"
  >

    <!-- Card top row: file info + badge + score -->
    <div class="card-top">

      <div class="card-left">
        <!-- Severity badge — uses RiskBadge component -->
        <RiskBadge :severity="finding.severity" size="sm" />

        <!-- File name and finding type -->
        <div class="card-text">
          <p class="card-name">{{ finding.resource_name }}</p>
          <p class="card-type">{{ formatType(finding.finding_type) }}</p>
        </div>
      </div>

      <div class="card-right">
        <!-- Risk score -->
        <span class="risk-score">{{ finding.risk_score }}/10</span>

        <!-- Action link — only shows if showAction is true -->
        <router-link
          v-if="showAction && actionTo"
          :to="actionTo"
          class="action-link"
        >
          {{ actionLabel }}
        </router-link>
      </div>

    </div>

    <!-- Evidence text -->
    <p class="card-evidence">{{ finding.evidence }}</p>

    <!-- Recommended action — only shows if present -->
    <div v-if="finding.recommended_action" class="card-recommendation">
      <span class="rec-label">Recommended:</span>
      <span class="rec-text">{{ finding.recommended_action }}</span>
    </div>

    <!-- Status pill at the bottom -->
    <div class="card-footer">
      <span :class="['status-pill', `status-pill--${finding.status}`]">
        {{ finding.status?.replace("_", " ") }}
      </span>
    </div>

  </div>
</template>


<script setup>
import RiskBadge from "./RiskBadge.vue"

/*
 * Props this component accepts from its parent.
 *
 * finding    — the actual finding data object (required)
 * showAction — whether to show the action button (default false)
 * actionLabel— text on the button
 * actionTo   — router path to navigate to on click
 */
defineProps({
  finding: {
    type: Object,
    required: true,
  },
  showAction: {
    type: Boolean,
    default: false,
  },
  actionLabel: {
    type: String,
    default: "Review →",
  },
  actionTo: {
    type: String,
    default: "/approvals",
  },
})

/*
 * formatType() converts database value to readable text.
 * "anonymous_link" → "Anonymous Link"
 */
const formatType = (type) => {
  if (!type) return ""
  return type
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
}
</script>


<style scoped>
.card {
  background: #0f0f11;
  border: 1px solid #1f1f23;
  border-left-width: 3px;
  border-radius: 12px;
  padding: 16px 18px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  transition: border-color 0.15s;
}

/* Left border colour matches severity */
.card--critical { border-left-color: #ef4444; }
.card--high     { border-left-color: #f97316; }
.card--medium   { border-left-color: #eab308; }
.card--low      { border-left-color: #22c55e; }

/* ── Card top ─────────────────────────────────────────── */

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 10px;
}

.card-left {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.card-text { flex: 1; min-width: 0; }

.card-name {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-type {
  font-size: 11px;
  color: #6b7280;
}

.card-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.risk-score {
  font-size: 11px;
  color: #52525b;
  white-space: nowrap;
}

.action-link {
  font-size: 12px;
  color: #6366f1;
  text-decoration: none;
  white-space: nowrap;
  transition: color 0.15s;
}
.action-link:hover { color: #818cf8; }

/* ── Evidence ─────────────────────────────────────────── */

.card-evidence {
  font-size: 13px;
  color: #9ca3af;
  line-height: 1.5;
  margin-bottom: 10px;
}

/* ── Recommendation ───────────────────────────────────── */

.card-recommendation {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 12px;
  line-height: 1.4;
}

.rec-label {
  font-weight: 500;
  color: #52525b;
  margin-right: 4px;
}

.rec-text { color: #9ca3af; }

/* ── Footer ───────────────────────────────────────────── */

.card-footer { display: flex; align-items: center; }

.status-pill {
  font-size: 10px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 20px;
  text-transform: capitalize;
}

.status-pill--open          { background: rgba(99,102,241,.15); color: #818cf8; }
.status-pill--resolved      { background: rgba(34,197,94,.15);  color: #4ade80; }
.status-pill--in_progress   { background: rgba(234,179,8,.15);  color: #fbbf24; }
.status-pill--accepted_risk { background: rgba(107,114,128,.15);color: #9ca3af; }
</style>