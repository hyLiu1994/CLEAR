<template>
  <header class="topbar">
    <!-- Left: Logo + tagline -->
    <div class="brand" @click="go('/home')">
      <img src="../assets/clearlogo-2.jpg" class="logo-img" alt="CLEAR logo" />

      <div class="brand-tagline">
        CLEAR: Knowledge-Centric Vessel Trajectory Analysis Platform
      </div>
    </div>

    <!-- Navigation -->
    <nav class="nav">
      <button
        class="nav-link"
        :class="{ active: isActive('/home') }"
        @click="go('/home')"
      >
        Home
      </button>

      <button
        class="nav-link"
        :class="{ active: isActive('/map') }"
        @click="go('/map')"
      >
        Map
      </button>

      <button
        class="nav-link"
        :class="{ active: isActive('/sdkg') }"
        @click="go('/sdkg')"
      >
        KG
      </button>

      <button
        class="nav-link"
        :class="{ active: isActive('/settings') }"
        @click="go('/settings')"
      >
        Settings
      </button>
    </nav>
  </header>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const go = p => {
  if (route.path !== p) router.push(p)
}

const isActive = p => route.path.startsWith(p)
</script>

<style scoped>
/* Main container */
.topbar {
  height: 64px;
  padding: 0 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

/* Brand block */
.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
}

.logo-img {
  height: 54px;
  object-fit: contain;
  user-select: none;
}

/* Tagline */
.brand-tagline {
  font-size: 18px;
  color: #475569; /* slate-600 */
  letter-spacing: 0;
  white-space: nowrap;
  font-weight: 500;
}

/* Navigation */
.nav {
  display: flex;
  gap: 32px;
}

.nav-link {
  border: none;
  background: transparent;
  font-size: 21px;
  color: #555;
  cursor: pointer;
  padding: 4px 0;
  position: relative;
  transition: 0.15s;
}

.nav-link:hover {
  color: #111;
}

.nav-link.active {
  color: #2563eb;
  font-weight: 600;
}

.nav-link.active::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -6px;
  height: 2px;
  background: #2563eb;
  border-radius: 999px;
}
</style>
