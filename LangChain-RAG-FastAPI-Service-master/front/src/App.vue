<template>
  <div class="app-shell">
    <router-view v-slot="{ Component }">
      <template v-if="$route.meta.keepAlive">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </template>
      <template v-else>
        <component :is="Component" />
      </template>
    </router-view>
  </div>
</template>

<script setup>
// Root shell component
</script>

<style scoped>
.app-shell {
  width: 100%;
  min-height: 100vh;
  position: relative;
}
</style>
