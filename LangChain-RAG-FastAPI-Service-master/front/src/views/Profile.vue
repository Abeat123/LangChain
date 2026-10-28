<template>
  <div class="profile-redirect">
    <van-loading vertical>正在跳转到我的详情...</van-loading>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

onMounted(() => {
  router.replace('/my');
});
</script>

<style scoped>
.profile-redirect {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
}
</style>
