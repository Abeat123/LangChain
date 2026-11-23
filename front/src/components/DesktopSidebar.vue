<template>
  <aside class="desktop-sidebar">
    <div class="sidebar-top">
      <div class="sidebar-head">
        <div class="brand-row">
          <img class="brand-logo" :src="allInRagLogo" alt="All in RAG" />
          <div class="brand-text">知识问答</div>
        </div>
      </div>

      <button
        v-if="showNewChat"
        type="button"
        class="new-chat-button"
        @click="$emit('new-chat')"
      >
        <span class="new-chat-plus">+</span>
        <span>开启新对话</span>
      </button>
    </div>

    <div v-if="showHistory" class="sidebar-history">
      <div v-if="loading" class="history-loading">加载中...</div>
      <template v-else-if="sessionGroups.length > 0">
        <section
          v-for="group in sessionGroups"
          :key="group.label"
          class="history-group"
        >
          <div class="history-label">{{ group.label }}</div>
          <button
            v-for="session in group.items"
            :key="session.session_id"
            type="button"
            class="history-item"
            :class="{ active: activeSessionId === session.session_id }"
            @click="$emit('open-session', session.session_id)"
          >
            <span class="history-title">{{ session.title || '新的会话' }}</span>
            <span class="history-time">
              {{ formatRelativeSessionTime(session.updated_at || session.created_at) }}
            </span>
          </button>
        </section>
      </template>
      <div v-else class="history-empty">暂无历史会话</div>
    </div>

    <div v-else class="sidebar-spacer"></div>

    <div class="sidebar-footer">
      <div class="sidebar-nav">
        <button
          v-for="item in navItems"
          :key="item.key"
          type="button"
          class="sidebar-nav-item"
          :class="{ active: activeSection === item.key }"
          @click="$emit('navigate', item.key)"
        >
          {{ item.label }}
        </button>
      </div>

      <button
        type="button"
        class="account-card"
        @click="$emit('navigate', 'my')"
      >
        <span class="account-avatar">{{ currentUserInitial }}</span>
        <span class="account-copy">
          <span class="account-name">{{ currentUserName }}</span>
          <span class="account-meta">账户中心</span>
        </span>
        <span class="account-more">...</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue';
import allInRagLogo from '../assets/all-in-rag-logo.svg';
import { useUserStore } from '../store/user';

defineProps({
  activeSection: {
    type: String,
    default: 'aichat',
  },
  showHistory: {
    type: Boolean,
    default: true,
  },
  showNewChat: {
    type: Boolean,
    default: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  sessionGroups: {
    type: Array,
    default: () => [],
  },
  activeSessionId: {
    type: String,
    default: '',
  },
});

defineEmits(['navigate', 'new-chat', 'open-session']);

const userStore = useUserStore();

const navItems = [
  { key: 'aichat', label: 'AI 问答' },
  { key: 'sessions', label: '会话管理' },
  { key: 'knowledgebase', label: '知识库管理' },
  { key: 'retrieval-insights', label: '检索可视化' },
  { key: 'knowledge-spaces', label: '多知识库切换' },
  { key: 'feedback', label: '回答反馈' },
  { key: 'my', label: '我的' },
];

const currentUserName = computed(() => {
  return (
    userStore.userInfo?.username ||
    userStore.userInfo?.nickname ||
    userStore.userInfo?.email ||
    '未登录用户'
  );
});

const currentUserInitial = computed(() => {
  const firstChar = currentUserName.value.slice(0, 1) || 'U';
  return firstChar.toUpperCase();
});

const formatRelativeSessionTime = (timeString) => {
  if (!timeString) return '';

  const date = new Date(timeString);
  const diff = Date.now() - date.getTime();
  const hour = 60 * 60 * 1000;
  const day = 24 * hour;

  if (diff < hour) return '刚刚';
  if (diff < day) return `${Math.floor(diff / hour)} 小时前`;
  if (diff < 7 * day) return `${Math.floor(diff / day)} 天前`;

  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
  });
};
</script>

<style scoped>
.desktop-sidebar {
  width: 232px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: sticky;
  top: 0;
  background: #f8f9fc;
  border-right: 1px solid #ebeff6;
}

.sidebar-top {
  padding: 12px 10px 14px;
}

.sidebar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 14px;
}

.brand-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.brand-logo {
  width: 56px;
  height: 34px;
  display: block;
  object-fit: contain;
  flex-shrink: 0;
}

.brand-text {
  color: #3558ff;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.04em;
}

.new-chat-button {
  width: 100%;
  height: 36px;
  border-radius: 999px;
  border: 1px solid #dfe5ef;
  background: #ffffff;
  color: #232d41;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 2px 10px rgba(120, 142, 183, 0.08);
}

.new-chat-plus {
  width: 16px;
  height: 16px;
  border-radius: 999px;
  border: 1px solid #ccd6e8;
  display: grid;
  place-items: center;
  font-size: 12px;
  line-height: 1;
}

.sidebar-history {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px 16px;
}

.sidebar-spacer {
  flex: 1;
}

.history-group + .history-group {
  margin-top: 14px;
}

.history-label {
  padding: 0 10px 8px;
  color: #9aa6ba;
  font-size: 12px;
  font-weight: 600;
}

.history-loading,
.history-empty {
  padding: 8px 10px;
  color: #97a3b8;
  font-size: 13px;
}

.history-item {
  width: 100%;
  border: none;
  background: transparent;
  text-align: left;
  display: block;
  padding: 9px 10px;
  border-radius: 10px;
  margin-bottom: 2px;
  transition: background 0.2s ease, color 0.2s ease;
}

.history-item:hover,
.history-item.active {
  background: #eef3ff;
}

.history-title {
  display: block;
  color: #29344c;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 3px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-time {
  display: block;
  color: #9aa6ba;
  font-size: 12px;
}

.sidebar-footer {
  padding: 10px 10px 12px;
  border-top: 1px solid #ebeff6;
}

.sidebar-nav {
  display: grid;
  gap: 6px;
  margin-bottom: 10px;
}

.sidebar-nav-item {
  height: 36px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: #5e6b86;
  font-size: 14px;
  text-align: left;
  padding: 0 12px;
}

.sidebar-nav-item:hover {
  background: #edf2fc;
  color: #415274;
}

.sidebar-nav-item.active {
  background: #e8efff;
  color: #2f56ff;
  font-weight: 600;
}

.account-card {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  border: none;
  border-radius: 12px;
  background: transparent;
  padding: 8px 6px;
  text-align: left;
}

.account-avatar {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: linear-gradient(135deg, #d7c1aa 0%, #c79569 100%);
  color: #ffffff;
  display: grid;
  place-items: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.account-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.account-name {
  color: #313d56;
  font-size: 13px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-meta {
  color: #98a3b6;
  font-size: 12px;
}

.account-more {
  color: #9aa5b8;
  font-size: 14px;
}

@media (max-width: 900px) {
  .desktop-sidebar {
    display: none;
  }
}
</style>
