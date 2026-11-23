<template>
  <div class="page-shell">
    <desktop-sidebar
      active-section="sessions"
      :show-history="true"
      :show-new-chat="true"
      :loading="sessionStore.isLoading"
      :session-groups="sidebarSessionGroups"
      :active-session-id="activeSidebarSessionId"
      @navigate="handleSidebarNavigate"
      @new-chat="createNewSession"
      @open-session="openSession"
    />

    <main class="page-main">
      <van-nav-bar title="会话管理" fixed class="mobile-nav" />

      <div class="sessions-content">
        <section class="sessions-hero">
          <div class="hero-copy">
            <h2>历史会话</h2>
            <p>{{ sessionStore.sessions.length }} 条记录可随时续聊，重要问题和上下文都会留在这里。</p>
          </div>
          <van-button type="primary" class="hero-action" @click="createNewSession">新对话</van-button>
        </section>

        <div v-if="sessionStore.isLoading" class="loading">
          <van-loading type="spinner" color="var(--primary-color)" />
          <p>正在整理会话历史...</p>
        </div>

        <div v-else-if="sessionStore.sessions.length === 0" class="empty-sessions page-card">
          <van-icon name="chat-o" size="52" color="var(--primary-color)" />
          <p>还没有历史会话，开始第一段对话吧。</p>
          <van-button type="primary" @click="createNewSession">创建新会话</van-button>
        </div>

        <div v-else class="sessions-list">
          <div
            v-for="session in sessionStore.sessions"
            :key="session.session_id"
            class="session-card"
            :class="{ active: sessionStore.currentSession?.session_id === session.session_id }"
            @click="selectSession(session)"
          >
            <div class="session-main">
              <div class="session-badge">
                <van-icon name="chat-o" />
              </div>
              <div class="session-copy">
                <h3>{{ session.title || '新的会话' }}</h3>
                <p>{{ formatSessionTime(session.updated_at || session.created_at) }}</p>
              </div>
            </div>
            <van-button type="danger" plain size="small" @click.stop="deleteSession(session.session_id)">
              删除
            </van-button>
          </div>
        </div>
      </div>

      <van-popup v-model:show="showNewSessionDialog" position="bottom" round class="session-popup">
        <div class="new-session-dialog">
          <h3>发起新对话</h3>
          <p>输入你的第一个问题，系统会自动创建新的上下文。</p>
          <van-field
            v-model="newSessionQuery"
            type="textarea"
            rows="3"
            maxlength="200"
            placeholder="例如：帮我概括这份资料的核心观点"
          />
          <div class="dialog-buttons">
            <van-button plain @click="showNewSessionDialog = false">取消</van-button>
            <van-button type="primary" @click="confirmNewSession" :disabled="!newSessionQuery.trim()">
              开始对话
            </van-button>
          </div>
        </div>
      </van-popup>

      <tab-bar class="mobile-tabbar" />
    </main>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { showToast } from 'vant';

import DesktopSidebar from '../components/DesktopSidebar.vue';
import TabBar from '../components/TabBar.vue';
import { useSessionStore } from '../store/session';
import { useUserStore } from '../store/user';
import { navigateBySidebarKey } from '../utils/sidebarNavigation';

const router = useRouter();
const route = useRoute();
const sessionStore = useSessionStore();
const userStore = useUserStore();

const showNewSessionDialog = ref(false);
const newSessionQuery = ref('');
const activeSidebarSessionId = computed(() => route.params.sessionId || sessionStore.currentSession?.session_id || '');

const sidebarSessionGroups = computed(() => {
  const now = new Date();
  const groups = [];
  const buckets = new Map();

  const getLabel = (timeString) => {
    if (!timeString) return '更早';
    const date = new Date(timeString);
    const diff = now.getTime() - date.getTime();
    const day = 24 * 60 * 60 * 1000;
    if (diff < day) return '7天内';
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
  };

  sessionStore.sessions.slice(0, 20).forEach((session) => {
    const label = getLabel(session.updated_at || session.created_at);
    if (!buckets.has(label)) {
      buckets.set(label, []);
      groups.push({ label, items: buckets.get(label) });
    }
    buckets.get(label).push(session);
  });

  return groups;
});

watch(
  () => route.path,
  async (newPath) => {
    if (newPath === '/sessions') {
      await loadSessions();
    }
  }
);

const handleSidebarNavigate = (key) => {
  navigateBySidebarKey(router, key);
};

const loadSessions = async () => {
  if (!userStore.getLoginStatus) {
    showToast('请先登录');
    router.push('/login');
    return;
  }

  if (!userStore.userInfo) {
    const result = await userStore.getUserInfoDetail();
    if (!result.success) {
      showToast('获取用户信息失败');
      return;
    }
  }

  if (!userStore.userInfo) {
    showToast('获取用户信息失败');
    return;
  }

  const userId = userStore.userInfo.uuid || userStore.userInfo.id || userStore.userInfo.user_id;
  if (!userId) {
    showToast('获取用户 ID 失败');
    return;
  }

  await sessionStore.getUserSessions(userId);
};

onMounted(async () => {
  await loadSessions();
});

const formatSessionTime = (timeString) => {
  if (!timeString) return '';
  try {
    const date = new Date(timeString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    return timeString;
  }
};

const selectSession = (session) => {
  router.push(`/aichat/${session.session_id}`);
};

const openSession = (sessionId) => {
  if (!sessionId) return;
  router.push(`/aichat/${sessionId}`);
};

const deleteSession = async (sessionId) => {
  const result = await sessionStore.deleteSession(sessionId);
  if (result.success) {
    showToast('会话删除成功');
  } else {
    showToast(result.message || '删除失败');
  }
};

const createNewSession = () => {
  showNewSessionDialog.value = true;
};

const confirmNewSession = async () => {
  if (!newSessionQuery.value.trim()) return;

  const toastInstance = showToast({
    type: 'loading',
    message: '创建会话中...',
    forbidClick: true,
    duration: 0,
  });

  try {
    const result = await sessionStore.createSession(newSessionQuery.value);
    if (result.success && result.data?.session_id) {
      showToast('会话创建成功');
      showNewSessionDialog.value = false;
      newSessionQuery.value = '';
      router.push(`/aichat/${result.data.session_id}`);
    } else {
      showToast(result.message || '创建会话失败');
    }
  } catch (error) {
    console.error('创建会话失败:', error);
    showToast('创建会话失败');
  } finally {
    if (toastInstance?.close) {
      toastInstance.close();
    }
  }
};
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

.sessions-content {
  padding: 26px 28px 30px;
}

.sessions-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
  padding: 24px 26px;
  border-radius: 28px;
  background: linear-gradient(180deg, #fbfcff 0%, #f3f7ff 100%);
  border: 1px solid #e5ecf8;
  box-shadow: 0 18px 42px rgba(153, 171, 206, 0.12);
}

.hero-copy h2 {
  margin: 0 0 8px;
  font-size: 28px;
  color: #1c2941;
}

.hero-copy p {
  margin: 0;
  color: #7b89a3;
  line-height: 1.7;
}

.hero-action {
  min-width: 104px;
}

.loading,
.empty-sessions {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  min-height: 320px;
  text-align: center;
}

.empty-sessions {
  padding: 28px;
  border-radius: 28px;
}

.empty-sessions p,
.loading p {
  margin: 0;
  color: #7b89a3;
}

.sessions-list {
  display: grid;
  gap: 14px;
}

.session-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 18px;
  border-radius: 22px;
  background: #ffffff;
  border: 1px solid #e6edf8;
  box-shadow: 0 12px 28px rgba(166, 182, 212, 0.1);
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.session-card.active {
  border-color: #cfdcff;
  box-shadow: 0 14px 34px rgba(146, 165, 201, 0.16);
}

.session-card:hover {
  transform: translateY(-1px);
}

.session-main {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.session-badge {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eff4ff;
  color: #4d6bfe;
  font-size: 22px;
}

.session-copy {
  min-width: 0;
}

.session-copy h3 {
  margin: 0 0 6px;
  font-size: 16px;
  color: #1f2d48;
}

.session-copy p {
  margin: 0;
  color: #8e99b0;
  font-size: 12px;
}

.session-popup {
  max-width: 750px;
  margin: 0 auto;
}

.new-session-dialog {
  padding: 24px 20px calc(20px + env(safe-area-inset-bottom));
}

.new-session-dialog h3 {
  margin: 0 0 8px;
  font-size: 22px;
  color: #1f2d48;
}

.new-session-dialog p {
  margin: 0 0 18px;
  color: #70809e;
  line-height: 1.7;
}

.dialog-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 18px;
}

.mobile-nav,
.mobile-tabbar {
  display: none;
}

@media (max-width: 900px) {
  .page-main {
    width: 100%;
  }

  .mobile-nav,
  .mobile-tabbar {
    display: block;
  }

  .sessions-content {
    padding: 60px 12px 84px;
  }

  .sessions-hero {
    flex-direction: column;
    align-items: stretch;
    padding: 18px;
  }

  .hero-copy h2 {
    font-size: 22px;
  }

  .hero-action {
    width: 100%;
  }

  .session-card {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
