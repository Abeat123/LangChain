<template>
  <div class="page-shell">
    <desktop-sidebar
      active-section="my"
      :show-history="false"
      :show-new-chat="true"
      @navigate="handleSidebarNavigate"
      @new-chat="goToAIChat"
    />

    <main class="page-main">
      <van-nav-bar title="我的" fixed class="mobile-nav" />

      <div class="my-layout">
        <aside class="content-side">
          <section class="hero-card">
            <div class="hero-main">
              <van-image
                round
                width="88"
                height="88"
                :src="avatarSrc"
              />
              <div class="hero-copy">
                <h1>{{ isLogin ? displayName : '未登录' }}</h1>
                <p>{{ isLogin ? userBio : guestDescription }}</p>
              </div>
            </div>

            <div class="hero-actions" v-if="isLogin">
              <van-button type="primary" @click="activePanel = 'profile'">我的详情</van-button>
              <van-button plain @click="goToKnowledgeBase">知识库管理</van-button>
            </div>

            <div class="hero-actions" v-else>
              <van-button type="primary" @click="goToLogin">去登录</van-button>
              <van-button plain @click="goToRegister">去注册</van-button>
            </div>
          </section>

          <section class="menu-section">
            <div class="section-title">页面管理</div>
            <div class="panel-menu">
              <button
                type="button"
                class="panel-menu-item"
                :class="{ active: activePanel === 'profile' }"
                @click="activePanel = 'profile'"
              >
                <van-icon name="contact-o" />
                <span>我的详情</span>
              </button>

              <button
                type="button"
                class="panel-menu-item"
                @click="goToKnowledgeBase"
              >
                <van-icon name="description" />
                <span>知识库管理</span>
              </button>

              <button
                type="button"
                class="panel-menu-item"
                @click="goToSettings"
              >
                <van-icon name="setting-o" />
                <span>设置</span>
              </button>

              <button
                type="button"
                class="panel-menu-item"
                @click="goToAboutUs"
              >
                <van-icon name="info-o" />
                <span>关于我们</span>
              </button>

              <button
                v-if="isLogin"
                type="button"
                class="panel-menu-item danger"
                @click="handleLogout"
              >
                <van-icon name="revoke" />
                <span>退出登录</span>
              </button>
            </div>
          </section>
        </aside>

        <section class="content-main">
          <template v-if="activePanel === 'profile'">
            <div class="content-card">
              <div class="content-card-head">
                <div>
                  <h2>我的详情</h2>
                  <p>当前页面内容固定显示在侧边栏右侧。</p>
                </div>
                <div class="card-actions" v-if="isLogin">
                  <van-button plain @click="goToKnowledgeBase">知识库管理</van-button>
                  <van-button type="primary" @click="showEditProfile = true">编辑资料</van-button>
                </div>
              </div>

              <div v-if="isLogin" class="profile-groups">
                <section class="profile-panel">
                  <div class="section-title">基础信息</div>
                  <van-cell-group inset>
                    <van-cell title="用户 ID" :value="detailId" />
                    <van-cell title="用户名" :value="displayName" />
                    <van-cell title="邮箱" :value="userInfo?.email || '未设置'" />
                    <van-cell title="手机号" :value="userInfo?.telephone || '未设置'" />
                    <van-cell title="性别" :value="genderText" />
                    <van-cell title="个人简介" :label="userBio" />
                  </van-cell-group>
                </section>

                <section class="profile-panel">
                  <div class="section-title">账户信息</div>
                  <van-cell-group inset>
                    <van-cell title="注册时间" :value="createTimeText" />
                    <van-cell title="最后登录时间" :value="lastLoginText" />
                    <van-cell title="修改密码" is-link @click="showPasswordPopup = true" />
                  </van-cell-group>
                </section>
              </div>

              <div v-else class="empty-panel">
                <van-icon name="contact-o" size="42" color="#4d6bfe" />
                <p>登录后可在这里查看和编辑你的个人详情。</p>
                <van-button type="primary" @click="goToLogin">去登录</van-button>
              </div>
            </div>
          </template>
        </section>
      </div>

      <tab-bar class="mobile-tabbar" />
    </main>

    <van-popup
      v-model:show="showEditProfile"
      position="bottom"
      round
      class="edit-popup"
    >
      <div class="popup-body">
        <h3>编辑资料</h3>
        <van-field v-model="editForm.username" label="用户名" placeholder="请输入用户名" />
        <van-field v-model="editForm.email" label="邮箱" placeholder="请输入邮箱" />
        <van-field v-model="editForm.telephone" label="手机号" placeholder="请输入手机号" />
        <van-field v-model="editForm.bio" label="简介" type="textarea" rows="4" autosize placeholder="请输入个人简介" />

        <div class="popup-actions">
          <van-button plain block @click="showEditProfile = false">取消</van-button>
          <van-button type="primary" block @click="saveProfile">保存</van-button>
        </div>
      </div>
    </van-popup>

    <van-popup
      v-model:show="showPasswordPopup"
      position="bottom"
      round
      class="edit-popup"
    >
      <div class="popup-body">
        <h3>修改密码</h3>
        <van-field v-model="passwordForm.oldPassword" label="当前密码" type="password" placeholder="请输入当前密码" />
        <van-field v-model="passwordForm.newPassword" label="新密码" type="password" placeholder="请输入新密码" />
        <van-field v-model="passwordForm.confirmPassword" label="确认密码" type="password" placeholder="请再次输入新密码" />

        <div class="popup-actions">
          <van-button plain block @click="showPasswordPopup = false">取消</van-button>
          <van-button type="primary" block @click="savePassword">保存</van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { showDialog, showFailToast, showLoadingToast, showSuccessToast, showToast } from 'vant';

import DesktopSidebar from '../components/DesktopSidebar.vue';
import TabBar from '../components/TabBar.vue';
import { useUserStore } from '../store/user';
import { navigateBySidebarKey } from '../utils/sidebarNavigation';

const router = useRouter();
const userStore = useUserStore();

const activePanel = ref('profile');
const showEditProfile = ref(false);
const showPasswordPopup = ref(false);

const editForm = reactive({
  username: '',
  email: '',
  telephone: '',
  bio: '',
});

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
});

const guestDescription = '登录后可管理知识库、查看会话记录，并维护你的个人资料。';

const isLogin = computed(() => userStore.getLoginStatus);
const userInfo = computed(() => userStore.userInfo);
const displayName = computed(() => {
  return userInfo.value?.username || userInfo.value?.nickname || userInfo.value?.email || '未命名用户';
});
const userBio = computed(() => userInfo.value?.bio || '这个用户还没有填写简介');
const detailId = computed(() => userInfo.value?.id || userInfo.value?.uuid || '未设置');
const avatarSrc = computed(() => {
  return userInfo.value?.avatar
    ? userInfo.value.avatar
    : 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg';
});

const genderText = computed(() => {
  const gender = userInfo.value?.gender;
  if (gender === 1) return '男';
  if (gender === 2) return '女';
  return '其他';
});

const createTimeText = computed(() => formatDateTime(userInfo.value?.create_time));
const lastLoginText = computed(() => formatDateTime(userInfo.value?.last_login));

const formatDateTime = (value) => {
  if (!value) return '未设置';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '未设置';

  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const syncEditForm = () => {
  editForm.username = userInfo.value?.username || '';
  editForm.email = userInfo.value?.email || '';
  editForm.telephone = userInfo.value?.telephone || '';
  editForm.bio = userInfo.value?.bio || '';
};

watch(
  userInfo,
  () => {
    syncEditForm();
  },
  { immediate: true }
);

const handleSidebarNavigate = (key) => {
  navigateBySidebarKey(router, key);
};

const goToAIChat = () => {
  router.push('/aichat');
};

const goToLogin = () => {
  router.push('/login');
};

const goToRegister = () => {
  router.push('/register');
};

const goToSettings = () => {
  router.push('/settings');
};

const goToKnowledgeBase = () => {
  if (!isLogin.value) {
    goToLogin();
    return;
  }

  router.push('/knowledgebase');
};

const goToAboutUs = () => {
  router.push('/aboutus');
};

const handleLogout = () => {
  showDialog({
    title: '确认',
    message: '确定退出登录吗？',
    showCancelButton: true,
  }).then((action) => {
    if (action === 'confirm') {
      userStore.logout();
      router.push('/login');
    }
  });
};

const saveProfile = async () => {
  const loadingInstance = showLoadingToast({
    message: '保存中...',
    forbidClick: true,
    duration: 0,
  });

  try {
    const result = await userStore.updateUserInfo({
      username: editForm.username,
      email: editForm.email,
      telephone: editForm.telephone,
      gender: userInfo.value?.gender || 3,
      bio: editForm.bio,
    });

    if (result.success) {
      showSuccessToast('资料更新成功');
      showEditProfile.value = false;
      await userStore.getUserInfoDetail();
    } else {
      showFailToast(result.message || '资料更新失败');
    }
  } catch (error) {
    console.error('更新资料失败:', error);
    showFailToast('资料更新失败');
  } finally {
    loadingInstance.close();
  }
};

const savePassword = async () => {
  if (!passwordForm.oldPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
    showToast('请完整填写密码信息');
    return;
  }

  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    showToast('两次输入的新密码不一致');
    return;
  }

  const loadingInstance = showLoadingToast({
    message: '保存中...',
    forbidClick: true,
    duration: 0,
  });

  try {
    const result = await userStore.updatePassword(
      passwordForm.oldPassword,
      passwordForm.newPassword
    );

    if (result.success) {
      showSuccessToast('密码修改成功');
      showPasswordPopup.value = false;
      passwordForm.oldPassword = '';
      passwordForm.newPassword = '';
      passwordForm.confirmPassword = '';
    } else {
      showFailToast(result.message || '密码修改失败');
    }
  } catch (error) {
    console.error('修改密码失败:', error);
    showFailToast('密码修改失败');
  } finally {
    loadingInstance.close();
  }
};

onMounted(async () => {
  userStore.syncFromStorage();

  if (userStore.getToken) {
    await userStore.getUserInfoDetail();
  }
});
</script>

<style scoped>
.page-shell {
  display: flex;
  min-height: 100vh;
  background: #ffffff;
}

.page-main {
  flex: 1;
  min-width: 0;
  min-height: 100vh;
}

.my-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 18px;
  padding: 26px 28px 30px;
}

.content-side,
.content-main {
  min-width: 0;
}

.hero-card,
.content-card {
  background: linear-gradient(180deg, #fbfcff 0%, #f3f7ff 100%);
  border-radius: 28px;
  border: 1px solid #e5ecf8;
  box-shadow: 0 18px 42px rgba(153, 171, 206, 0.12);
}

.hero-card {
  padding: 24px;
  margin-bottom: 18px;
}

.hero-main {
  display: flex;
  align-items: center;
  gap: 18px;
}

.hero-copy {
  min-width: 0;
}

.hero-copy h1 {
  margin: 0 0 8px;
  font-size: 28px;
  color: #1f2d48;
}

.hero-copy p {
  margin: 0;
  color: #6f7f9c;
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  gap: 12px;
  margin-top: 22px;
}

.section-title {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 700;
  color: #586883;
}

.panel-menu {
  display: grid;
  gap: 10px;
}

.panel-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 14px 16px;
  border: 1px solid #e5ecf8;
  border-radius: 18px;
  background: #ffffff;
  color: #1f2d48;
  text-align: left;
  box-shadow: 0 8px 18px rgba(166, 182, 212, 0.08);
}

.panel-menu-item.active {
  border-color: #c6d6ff;
  background: #edf3ff;
  color: #3558ff;
}

.panel-menu-item.danger {
  color: #d84664;
}

.content-card {
  padding: 24px;
  min-height: calc(100vh - 56px);
}

.content-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.content-card-head h2 {
  margin: 0 0 8px;
  font-size: 28px;
  color: #1f2d48;
}

.content-card-head p {
  margin: 0;
  color: #73829f;
  line-height: 1.7;
}

.card-actions {
  display: flex;
  gap: 12px;
}

.profile-groups {
  display: grid;
  gap: 18px;
}

.profile-panel :deep(.van-cell-group) {
  border-radius: 24px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.94);
}

.profile-panel :deep(.van-cell) {
  padding-top: 16px;
  padding-bottom: 16px;
  --van-cell-text-color: #4f5f7e;
  --van-cell-value-color: #20314f;
  --van-cell-label-color: #627392;
}

.profile-panel :deep(.van-cell__title),
.profile-panel :deep(.van-cell__title span) {
  color: #4f5f7e;
  font-weight: 600;
}

.profile-panel :deep(.van-cell__value) {
  color: #20314f;
  font-weight: 600;
}

.profile-panel :deep(.van-cell__label) {
  margin-top: 8px;
  color: #627392;
  line-height: 1.7;
}

.profile-panel :deep(.van-cell__right-icon) {
  color: #7c8baa;
}

.hero-actions :deep(.van-button--plain),
.card-actions :deep(.van-button--plain) {
  color: #4065f4;
  background: rgba(255, 255, 255, 0.96);
  border-color: #c9d7f6;
}

.popup-body :deep(.van-field__label) {
  color: #4f5f7e;
  font-weight: 600;
}

.popup-body :deep(.van-field__control) {
  color: #1f2d48;
}

.empty-panel {
  min-height: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 14px;
  text-align: center;
  color: #6f7f9c;
}

.mobile-nav,
.mobile-tabbar {
  display: none;
}

.edit-popup {
  max-width: 760px;
  margin: 0 auto;
}

.popup-body {
  padding: 24px 20px calc(20px + env(safe-area-inset-bottom));
}

.popup-body h3 {
  margin: 0 0 16px;
  font-size: 22px;
  color: #1f2d48;
}

.popup-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 18px;
}

@media (max-width: 900px) {
  .page-main {
    width: 100%;
  }

  .mobile-nav,
  .mobile-tabbar {
    display: block;
  }

  .my-layout {
    grid-template-columns: 1fr;
    padding: 60px 12px 84px;
  }

  .hero-main {
    align-items: flex-start;
  }

  .hero-copy h1,
  .content-card-head h2 {
    font-size: 22px;
  }

  .hero-actions,
  .card-actions {
    flex-direction: column;
  }

  .content-card-head {
    flex-direction: column;
  }

  .content-card {
    min-height: auto;
  }

  .popup-actions {
    grid-template-columns: 1fr;
  }
}
</style>
