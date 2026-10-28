<template>
  <div class="auth-shell">
    <div class="auth-panel">
      <van-nav-bar title="用户注册" left-arrow fixed @click-left="onClickLeft" />

      <div class="register-container">
        <section class="register-hero">
          <van-image
            width="84"
            height="84"
            src="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
            round
          />
          <h2>创建你的知识空间</h2>
          <p>注册后即可使用知识库上传、会话管理与个人资料维护。</p>
        </section>

        <div class="register-form">
          <van-cell-group inset>
            <van-field
              v-model="form.username"
              placeholder="请输入用户名"
              :rules="usernameRules"
              required
              left-icon="user-o"
              @blur="validateUsername"
            />

            <van-field
              v-model="form.email"
              placeholder="请输入邮箱地址"
              :rules="emailRules"
              required
              type="email"
              left-icon="envelop-o"
              @blur="validateEmail"
            />

            <van-field
              v-model="form.telephone"
              placeholder="请输入手机号"
              type="tel"
              left-icon="phone"
              maxlength="11"
            />

            <van-field
              v-model="form.password"
              placeholder="请输入密码（6-20位）"
              :rules="passwordRules"
              required
              type="password"
              left-icon="lock"
              @blur="validatePassword"
            />

            <van-field
              v-model="form.confirm_password"
              placeholder="请确认密码"
              :rules="confirmPasswordRules"
              required
              type="password"
              left-icon="lock"
              @blur="validateConfirmPassword"
            />
          </van-cell-group>

          <div class="register-btn-container">
            <van-button type="primary" block :loading="loading" @click="handleRegister">
              {{ loading ? '注册中...' : '注册' }}
            </van-button>
          </div>
        </div>

        <div class="login-link">
          已有账号？<span @click="goToLogin">去登录</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { showToast } from 'vant';

import { useUserStore } from '../store/user';

const router = useRouter();
const userStore = useUserStore();

const loading = ref(false);

const form = reactive({
  username: '',
  email: '',
  telephone: '',
  password: '',
  confirm_password: '',
});

const usernameRules = [{ required: true, message: '请输入用户名' }];
const emailRules = [
  { required: true, message: '请输入邮箱地址' },
  { pattern: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/, message: '请输入正确的邮箱地址' },
];
const passwordRules = [
  { required: true, message: '请输入密码' },
  { pattern: /^.{6,20}$/, message: '密码长度应为 6-20 位' },
];
const confirmPasswordRules = [{ required: true, message: '请确认密码' }];

const toastText = (message, type = 'text') => {
  showToast({
    message,
    position: 'top',
    type,
  });
};

const validateUsername = () => {
  if (!form.username) {
    toastText('请输入用户名');
    return false;
  }
  return true;
};

const validateEmail = () => {
  if (!form.email) {
    toastText('请输入邮箱地址');
    return false;
  }

  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  if (!emailRegex.test(form.email)) {
    toastText('请输入正确的邮箱地址');
    return false;
  }

  return true;
};

const validatePassword = () => {
  if (!form.password) {
    toastText('请输入密码');
    return false;
  }

  if (form.password.length < 6 || form.password.length > 20) {
    toastText('密码长度应为 6-20 位');
    return false;
  }

  return true;
};

const validateConfirmPassword = () => {
  if (!form.confirm_password) {
    toastText('请确认密码');
    return false;
  }

  if (form.password !== form.confirm_password) {
    toastText('两次输入的密码不一致');
    return false;
  }

  return true;
};

const validateForm = () => {
  return (
    validateUsername() &&
    validateEmail() &&
    validatePassword() &&
    validateConfirmPassword()
  );
};

const handleRegister = async () => {
  if (!validateForm()) return;

  loading.value = true;
  try {
    const result = await userStore.register(form);

    if (result.success) {
      toastText(result.message, 'success');
      setTimeout(() => {
        router.push('/aichat');
      }, 1200);
    } else {
      toastText(result.message || '注册失败', 'fail');
    }
  } catch (error) {
    console.error('注册失败:', error);
    toastText('注册失败，请稍后重试', 'fail');
  } finally {
    loading.value = false;
  }
};

const onClickLeft = () => {
  router.back();
};

const goToLogin = () => {
  router.push('/login');
};
</script>

<style scoped>
.auth-shell {
  min-height: 100vh;
  background: #ffffff;
  padding: 24px;
}

.auth-panel {
  width: min(100%, 760px);
  margin: 0 auto;
  min-height: calc(100vh - 48px);
  background: #ffffff;
  border: 1px solid #e8edf7;
  border-radius: 28px;
  box-shadow: 0 24px 60px rgba(130, 154, 204, 0.12);
  overflow: hidden;
}

.register-container {
  padding: 68px 24px 28px;
}

.register-hero {
  padding: 32px 24px;
  margin-bottom: 18px;
  border-radius: 28px;
  text-align: center;
  background: linear-gradient(180deg, #fbfcff 0%, #f3f7ff 100%);
  border: 1px solid #e5ecf8;
}

.register-hero h2 {
  margin: 16px 0 10px;
  font-size: 32px;
  color: #1f2d48;
}

.register-hero p {
  margin: 0;
  color: #6f7f9c;
  line-height: 1.7;
}

.register-form {
  width: min(100%, 560px);
  margin: 0 auto;
}

.register-form :deep(.van-cell-group) {
  border-radius: 24px;
}

.register-form :deep(.van-field) {
  --van-field-input-text-color: #1f2d48;
  --van-field-placeholder-text-color: #7a89a5;
}

.register-form :deep(.van-field__control) {
  color: #1f2d48;
  -webkit-text-fill-color: #1f2d48;
}

.register-form :deep(.van-field__control::placeholder) {
  color: #7a89a5;
  -webkit-text-fill-color: #7a89a5;
}

.register-form :deep(.van-field__left-icon) {
  color: #7a89a5;
}

.register-form :deep(input:-webkit-autofill),
.register-form :deep(input:-webkit-autofill:hover),
.register-form :deep(input:-webkit-autofill:focus),
.register-form :deep(textarea:-webkit-autofill),
.register-form :deep(textarea:-webkit-autofill:hover),
.register-form :deep(textarea:-webkit-autofill:focus) {
  -webkit-text-fill-color: #1f2d48;
  caret-color: #1f2d48;
  box-shadow: 0 0 0 1000px rgba(245, 248, 255, 0.96) inset;
  transition: background-color 9999s ease-in-out 0s;
}

.register-btn-container {
  margin-top: 18px;
}

.login-link {
  text-align: center;
  margin-top: 24px;
  color: var(--muted-text-color);
  font-size: 14px;
}

.login-link span {
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

  .register-container {
    padding: 68px 16px 24px;
  }

  .register-hero {
    padding: 24px 18px;
  }

  .register-hero h2 {
    font-size: 24px;
  }
}
</style>
