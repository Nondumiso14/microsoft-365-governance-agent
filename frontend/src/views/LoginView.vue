<!-- src/views/LoginView.vue -->

<template>
  <div class="page">
    <div class="card">

      <div class="header">
        <svg width="32" height="32" viewBox="0 0 21 21" aria-hidden="true">
          <rect x="1" y="1" width="9" height="9" fill="#f25022"/>
          <rect x="11" y="1" width="9" height="9" fill="#7fba00"/>
          <rect x="1" y="11" width="9" height="9" fill="#00a4ef"/>
          <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
        </svg>
        <h1>M365 Governance Agent</h1>
        <p>Sign in to scan your Microsoft 365 environment</p>
      </div>

      <button
        @click="handleLogin"
        :disabled="isLoading"
        class="ms-btn"
      >
        <template v-if="!isLoading">
          <svg width="20" height="20" viewBox="0 0 21 21" aria-hidden="true">
            <rect x="1" y="1" width="9" height="9" fill="#f25022"/>
            <rect x="11" y="1" width="9" height="9" fill="#7fba00"/>
            <rect x="1" y="11" width="9" height="9" fill="#00a4ef"/>
            <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
          </svg>
          Sign in with Microsoft
        </template>
        <template v-else>
          <div class="spinner"></div>
          Connecting to Microsoft...
        </template>
      </button>

      <p class="security">
        Your credentials are handled securely by Microsoft.
        We never see your password.
      </p>

    </div>
  </div>
</template>

<script setup>
import { ref } from "vue"
import { useAuth } from "../composables/useAuth"

const { login } = useAuth()
const isLoading = ref(false)

const handleLogin = () => {
  isLoading.value = true
  login()
}
</script>

<style scoped>
/* Reset browser defaults so centering works */
:global(*) {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:global(html),
:global(body),
:global(#app) {
  height: 100%;
  width: 100%;
}

/* Full screen centred layout */
.page {
  min-height: 100vh;
  width: 100%;
  background: #111827;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Login card */
.card {
  width: 100%;
  max-width: 400px;
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 16px;
  padding: 40px 36px;
  margin: 20px;
}

/* Header section */
.header {
  text-align: center;
  margin-bottom: 32px;
}

.header svg {
  margin-bottom: 16px;
}

.header h1 {
  font-size: 22px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 8px;
}

.header p {
  font-size: 14px;
  color: #9ca3af;
  line-height: 1.5;
}

/* Microsoft button */
.ms-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 13px 20px;
  background: #ffffff;
  color: #111827;
  font-size: 15px;
  font-weight: 500;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s;
  margin-bottom: 20px;
}

.ms-btn:hover:not(:disabled) {
  background: #f3f4f6;
}

.ms-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.ms-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Spinner */
.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(17, 24, 39, 0.3);
  border-top-color: #111827;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Security note */
.security {
  font-size: 12px;
  color: #6b7280;
  text-align: center;
  line-height: 1.5;
}
</style>