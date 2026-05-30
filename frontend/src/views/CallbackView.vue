<!-- src/views/CallbackView.vue -->
<template>
  <div class="callback-page">
    <div class="spinner"></div>
    <p>Signing you in...</p>
  </div>
</template>

<script setup>
import { onMounted } from "vue"
import { useRouter } from "vue-router"
import { useAuth } from "../composables/useAuth"

const router = useRouter()
const { setToken } = useAuth()

onMounted(() => {
  // Mark user as logged in and go straight to dashboard
  setToken("authenticated")
  router.push({ name: "Dashboard" })
})
</script>

<style scoped>
:global(*) { margin: 0; padding: 0; box-sizing: border-box; }
:global(html), :global(body), :global(#app) { height: 100%; }

.callback-page {
  min-height: 100vh;
  background: #030303;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  font-family: -apple-system, sans-serif;
  color: #6b7280;
  font-size: 14px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #27272a;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>