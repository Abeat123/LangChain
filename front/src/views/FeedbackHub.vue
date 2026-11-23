<template>
  <div class="page-shell">
    <desktop-sidebar
      active-section="feedback"
      :show-history="false"
      :show-new-chat="true"
      @navigate="handleSidebarNavigate"
      @new-chat="goToAIChat"
    />

    <main class="page-main">
      <van-nav-bar
        title="回答反馈"
        left-arrow
        fixed
        class="mobile-nav"
        @click-left="onClickLeft"
      />

      <div class="feedback-page">
        <section class="hero-card">
          <div class="hero-copy">
            <h1>回答反馈</h1>
            <p>在 AI 问答页对回答进行“有帮助 / 需改进”反馈后，这里会展示最近记录和整体情况。</p>
          </div>
          <div class="hero-actions">
            <button
              type="button"
              class="chip-button"
              :class="{ active: filterMode === 'current' }"
              @click="switchFilter('current')"
            >
              当前知识库
            </button>
            <button
              type="button"
              class="chip-button"
              :class="{ active: filterMode === 'all' }"
              @click="switchFilter('all')"
            >
              全部知识库
            </button>
          </div>
        </section>

        <section class="stats-grid">
          <article class="stat-card">
            <span class="stat-label">反馈总数</span>
            <strong class="stat-value">{{ stats.total_count }}</strong>
          </article>
          <article class="stat-card">
            <span class="stat-label">有帮助</span>
            <strong class="stat-value good">{{ stats.positive_count }}</strong>
          </article>
          <article class="stat-card">
            <span class="stat-label">需改进</span>
            <strong class="stat-value bad">{{ stats.negative_count }}</strong>
          </article>
          <article class="stat-card">
            <span class="stat-label">正向占比</span>
            <strong class="stat-value">{{ stats.positive_rate }}%</strong>
          </article>
        </section>

        <section class="panel-card">
          <div class="panel-head">
            <h2>最近反馈记录</h2>
            <span>{{ feedbackItems.length }} 条</span>
          </div>

          <div v-if="loading" class="empty-card">正在加载反馈记录...</div>
          <div v-else-if="feedbackItems.length > 0" class="feedback-list">
            <article
              v-for="item in feedbackItems"
              :key="item.id"
              class="feedback-card"
            >
              <div class="feedback-top">
                <div class="feedback-tags">
                  <span class="feedback-type" :class="item.feedback_type">
                    {{ item.feedback_type === 'up' ? '有帮助' : '需改进' }}
                  </span>
                  <span class="feedback-kb">{{ item.knowledge_base_name || '默认知识库' }}</span>
                </div>
                <span class="feedback-time">{{ formatTime(item.updated_at || item.created_at) }}</span>
              </div>

              <div class="feedback-block">
                <span class="block-label">问题</span>
                <p>{{ item.question }}</p>
              </div>

              <div class="feedback-block">
                <span class="block-label">回答</span>
                <p>{{ truncateText(item.answer, 220) }}</p>
              </div>

              <div v-if="item.comment" class="feedback-block note-block">
                <span class="block-label">补充意见</span>
                <p>{{ item.comment }}</p>
              </div>
            </article>
          </div>
          <div v-else class="empty-card">
            还没有反馈记录。去 AI 问答页发起对话后，可以直接对回答进行反馈。
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import DesktopSidebar from '../components/DesktopSidebar.vue';
import { useKnowledgeBaseStore } from '../store/knowledgeBase';
import { navigateBySidebarKey } from '../utils/sidebarNavigation';

const router = useRouter();
const knowledgeBaseStore = useKnowledgeBaseStore();

const filterMode = ref('current');
const loading = ref(false);
const feedbackItems = ref([]);
const stats = reactive({
  total_count: 0,
  positive_count: 0,
  negative_count: 0,
  positive_rate: 0,
});

const activeKnowledgeBase = computed(() => knowledgeBaseStore.activeKnowledgeBase);
const activeKnowledgeBaseId = computed(() => {
  return filterMode.value === 'current' ? activeKnowledgeBase.value?.id || '' : '';
});

const handleSidebarNavigate = (key) => {
  navigateBySidebarKey(router, key);
};

const goToAIChat = () => {
  router.push('/aichat');
};

const onClickLeft = () => {
  router.back();
};

const switchFilter = async (mode) => {
  filterMode.value = mode;
  await fetchFeedbackData();
};

const buildQuery = () => {
  const params = new URLSearchParams();
  if (activeKnowledgeBaseId.value) {
    params.set('knowledge_base_id', activeKnowledgeBaseId.value);
  }
  params.set('limit', '50');
  return params.toString();
};

const fetchFeedbackData = async () => {
  const token = localStorage.getItem('jwt_token') || '';
  if (!token) {
    feedbackItems.value = [];
    Object.assign(stats, {
      total_count: 0,
      positive_count: 0,
      negative_count: 0,
      positive_rate: 0,
    });
    return;
  }

  loading.value = true;
  try {
    const query = buildQuery();
    const [listResponse, statsResponse] = await Promise.all([
      fetch(`/chat/feedback?${query}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }),
      fetch(`/chat/feedback/stats?${query}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }),
    ]);

    const listData = listResponse.ok ? await listResponse.json() : {};
    const statsData = statsResponse.ok ? await statsResponse.json() : {};

    feedbackItems.value = listData?.data?.items || [];
    Object.assign(stats, {
      total_count: statsData?.data?.total_count || 0,
      positive_count: statsData?.data?.positive_count || 0,
      negative_count: statsData?.data?.negative_count || 0,
      positive_rate: statsData?.data?.positive_rate || 0,
    });
  } catch (error) {
    console.error('fetchFeedbackData error:', error);
    feedbackItems.value = [];
  } finally {
    loading.value = false;
  }
};

const truncateText = (text, maxLength) => {
  if (!text) return '';
  return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text;
};

const formatTime = (timeString) => {
  if (!timeString) return '';
  return new Date(timeString).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

onMounted(async () => {
  await knowledgeBaseStore.ensureKnowledgeBasesLoaded();
  await fetchFeedbackData();
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

.feedback-page {
  padding: 26px 28px 30px;
}

.hero-card,
.stat-card,
.panel-card,
.feedback-card {
  background: #ffffff;
  border: 1px solid #e5ecf8;
  box-shadow: 0 18px 42px rgba(153, 171, 206, 0.12);
}

.hero-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 24px 26px;
  border-radius: 28px;
  background: linear-gradient(180deg, #fbfcff 0%, #f3f7ff 100%);
  margin-bottom: 18px;
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
  gap: 10px;
}

.chip-button,
.feedback-type,
.feedback-kb {
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.chip-button {
  border: 1px solid #d8e4fa;
  background: #f8fbff;
  color: #50647f;
  padding: 8px 12px;
}

.chip-button.active {
  background: #e8efff;
  border-color: #bfd1ff;
  color: #2f56ff;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.stat-card {
  padding: 20px 22px;
  border-radius: 24px;
}

.stat-label {
  display: block;
  color: #70809e;
  font-size: 13px;
  margin-bottom: 10px;
}

.stat-value {
  color: #1f2d48;
  font-size: 30px;
  line-height: 1;
}

.stat-value.good {
  color: #17814b;
}

.stat-value.bad {
  color: #d83b5c;
}

.panel-card {
  border-radius: 28px;
  padding: 22px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 14px;
}

.panel-head h2 {
  margin: 0;
  font-size: 18px;
  color: #1f2d48;
}

.panel-head span,
.feedback-time,
.block-label {
  color: #7b89a3;
  font-size: 13px;
}

.feedback-list {
  display: grid;
  gap: 12px;
}

.feedback-card {
  padding: 18px;
  border-radius: 22px;
}

.feedback-top,
.feedback-tags {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.feedback-top {
  margin-bottom: 14px;
}

.feedback-tags {
  justify-content: flex-start;
  flex-wrap: wrap;
}

.feedback-type {
  padding: 6px 10px;
}

.feedback-type.up {
  background: #edf9f2;
  color: #17814b;
}

.feedback-type.down {
  background: #fff1f3;
  color: #d83b5c;
}

.feedback-kb {
  padding: 6px 10px;
  background: #eef4ff;
  color: #3f63f4;
}

.feedback-block + .feedback-block {
  margin-top: 12px;
}

.block-label {
  display: block;
  margin-bottom: 6px;
}

.feedback-block p {
  margin: 0;
  color: #20314f;
  line-height: 1.7;
}

.note-block {
  padding: 12px 14px;
  border-radius: 16px;
  background: #f9fbff;
  border: 1px solid #edf2fb;
}

.empty-card {
  padding: 28px 18px;
  border-radius: 18px;
  background: #f9fbff;
  border: 1px dashed #d8e2f3;
  color: #7b89a3;
  text-align: center;
}

.mobile-nav {
  display: none;
}

@media (max-width: 900px) {
  .page-main {
    width: 100%;
  }

  .mobile-nav {
    display: block;
  }

  .feedback-page {
    padding: 60px 12px 24px;
  }

  .hero-card,
  .stats-grid {
    display: grid;
  }

  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }

  .hero-copy h1 {
    font-size: 22px;
  }
}
</style>
