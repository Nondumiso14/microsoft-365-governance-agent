<!-- frontend/src/App.vue -->
<template>
  <!--
    RouterView is where Vue Router renders the current page.
    Without this — no page ever shows, just a blank screen.

    When user visits /dashboard → Vue Router finds the Dashboard route
    → renders DashboardView.vue inside this RouterView
  -->
  <RouterView />
</template>

<script setup>
import { RouterView } from "vue-router"
</script>
