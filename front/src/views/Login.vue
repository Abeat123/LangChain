<template>
  <div class="auth-shell">
    <div class="auth-panel">
      <van-nav-bar title="用户登录" left-arrow fixed @click-left="onClickLeft" />

      <div class="login-container">
        <section class="login-hero">
          <van-image
            width="84"
            height="84"
            src="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
            round
          />
          <h2>欢迎回来</h2>
          <p>进入深蓝知识工作台，继续你的会话和知识库管理。</p>
        </section>

        <van-form @submit="onSubmit" class="login-form">
          <van-cell-group inset>
            <van-field
              v-model="username"
              name="username"
              label="用户名"
              placeholder="请输入用户名"
              :rules="[{ required: true, message: '请填写用户名' }]"
            />
            <van-field
              v-model="password"
              type="password"
              name="password"
              label="密码"
              placeholder="请输入密码"
              :rules="[{ required: true, message: '请填写密码' }]"
            />
          </van-cell-group>

          <div class="submit-btn">
            <van-button round block type="primary" native-type="submit" size="large">
              登录
            </van-button>
          </div>

          <div class="test-user-btn">
            <van-button round block plain size="large" @click="loginTestUser">
              填充测试账号
            </van-button>
          </div>

          <div class="register-link">
            还没有账号？<span @click="goToRegister">去注册</span>
          </div>
        </van-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { showToast } from 'vant';

import { useUserStore } from '../store/user';

const router = useRouter();
const userStore = useUserStore();

const username = ref('');
const password = ref('');

const onSubmit = async () => {
  showToast({
    type: 'loading',
    message: '登录中...',
    forbidClick: true,
    duration: 0,
  });

  try {
    const result = await userStore.login({
      username: username.value,
      password: password.value,
    });

    if (result.success) {
      showToast({
        type: 'success',
        message: result.message,
      });
      router.push('/');
    } else {
      showToast({
        type: 'fail',
        message: result.message,
      });
    }
  } catch (error) {
    console.error('登录失败:', error);
    showToast({
      type: 'fail',
      message: '登录失败，请稍后再试',
    });
  }
};

const onClickLeft = () => {
  router.back();
};

const goToRegister = () => {
  router.push('/register');
};

const loginTestUser = () => {
  username.value = 'test';
  password.value = '666666';
};
</script>

<style scoped>
.auth-shell {
  min-height: 100vh;
  background: #ffffff;
  padding: 24px;
}

.auth-panel {
  width: min(100%, 720px);
  margin: 0 auto;
  min-height: calc(100vh - 48px);
  background: #ffffff;
  border: 1px solid #e8edf7;
  border-radius: 28px;
  box-shadow: 0 24px 60px rgba(130, 154, 204, 0.12);
  overflow: hidden;
}

.login-container {
  padding: 68px 24px 28px;
}

.login-hero {
  padding: 32px 24px;
  margin-bottom: 18px;
  border-radius: 28px;
  text-align: center;
  background: linear-gradient(180deg, #fbfcff 0%, #f3f7ff 100%);
  border: 1px solid #e5ecf8;
}

.login-hero h2 {
  margin: 16px 0 10px;
  font-size: 32px;
  color: #1f2d48;
}

.login-hero p {
  margin: 0;
  color: #566784;
  line-height: 1.7;
}

.login-form {
  width: min(100%, 560px);
  margin: 0 auto;
}

.login-form :deep(.van-cell-group) {
  border-radius: 24px;
}

.login-form :deep(.van-field) {
  --van-field-input-text-color: #1f2d48;
  --van-field-placeholder-text-color: #7a89a5;
}

.login-form :deep(.van-field__control) {
  color: #1f2d48;
  -webkit-text-fill-color: #1f2d48;
}

.login-form :deep(.van-field__control::placeholder) {
  color: #7a89a5;
  -webkit-text-fill-color: #7a89a5;
}

.login-form :deep(.van-field__left-icon) {
  color: #7a89a5;
}

.login-form :deep(input:-webkit-autofill),
.login-form :deep(input:-webkit-autofill:hover),
.login-form :deep(input:-webkit-autofill:focus),
.login-form :deep(textarea:-webkit-autofill),
.login-form :deep(textarea:-webkit-autofill:hover),
.login-form :deep(textarea:-webkit-autofill:focus) {
  -webkit-text-fill-color: #1f2d48;
  caret-color: #1f2d48;
  box-shadow: 0 0 0 1000px rgba(245, 248, 255, 0.96) inset;
  transition: background-color 9999s ease-in-out 0s;
}

.submit-btn,
.test-user-btn {
  margin: 18px 0 0;
}

.register-link {
  text-align: center;
  margin-top: 24px;
  color: #5f7090;
  font-size: 14px;
}

.register-link span {
  color: var(--primary-color);
}

@media (max-width: 900px) {
  .auth-shell {
    padding: 0;
  }

  .auth-panel {
    width: 100%;
    min-height: 100vh;
    border-radius: 0;
    border: none;
    box-shadow: none;
  }

  .login-container {
    padding: 68px 16px 24px;
  }

  .login-hero {
    padding: 24px 18px;
  }

  .login-hero h2 {
    font-size: 24px;
  }
}
</style>
