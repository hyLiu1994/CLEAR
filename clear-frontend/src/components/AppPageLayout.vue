<!-- AppPageLayout.vue -->
<template>
  <div class="page">
    <TopNav />

    <main class="main">
      <slot />
    </main>
  </div>
</template>

<script setup>
import TopNav from './TopNav.vue'
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  /* height: 100vh; */
  min-height: 100vh;
  background: #f5f5f5;
}

.main {
  flex: 1;
  padding: 6px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}
</style>
