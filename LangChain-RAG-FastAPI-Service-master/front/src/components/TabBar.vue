<template>
  <van-tabbar
    v-model="active"
    route
    class="app-tabbar"
    active-color="var(--primary-color)"
    inactive-color="var(--muted-text-color)"
  >
    <van-tabbar-item to="/aichat" icon="chat-o">{{ $t('nav.aiChat') }}</van-tabbar-item>
    <van-tabbar-item to="/sessions" icon="comment-circle-o">{{ $t('nav.sessions') }}</van-tabbar-item>
    <van-tabbar-item to="/my" icon="user-o">{{ $t('nav.my') }}</van-tabbar-item>
  </van-tabbar>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const active = ref(0);

const setActiveTab = () => {
  const path = route.path;
  if (path.includes('/aichat')) {
    active.value = 0;
  } else if (path.includes('/sessions')) {
    active.value = 1;
  } else if (path.includes('/my')) {
    active.value = 2;
  }
};

setActiveTab();

watch(
  () => route.path,
  () => {
    setActiveTab();
  }
);
</script>

<style scoped>
.app-tabbar {
  left: 50%;
  width: min(calc(100% - 24px), 1280px);
  transform: translateX(-50%);
  bottom: 12px;
  border: 1px solid rgba(140, 163, 212, 0.2);
  border-radius: 22px;
  box-shadow: 0 18px 44px rgba(77, 107, 254, 0.12);
  overflow: hidden;
}

.app-tabbar::before {
  display: none;
}

.app-tabbar :deep(.van-tabbar-item) {
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.app-tabbar :deep(.van-tabbar-item--active) {
  transform: translateY(-2px);
}

.app-tabbar :deep(.van-tabbar-item__icon) {
  font-size: 20px;
}

.app-tabbar :deep(.van-tabbar-item__text) {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.03em;
}

@media (min-width: 901px) {
  .app-tabbar {
    display: none;
  }
}

@media (max-width: 640px) {
  .app-tabbar {
    width: 100%;
    bottom: 0;
    border-right: none;
    border-bottom: none;
    border-left: none;
    border-radius: 0;
    box-shadow: 0 -10px 24px rgba(77, 107, 254, 0.08);
  }
}
</style>
