<template>
  <div class="page-shell">
    <desktop-sidebar
      active-section="retrieval-insights"
      :show-history="false"
      :show-new-chat="true"
      @navigate="handleSidebarNavigate"
      @new-chat="goToAIChat"
    />

    <main class="page-main">
      <van-nav-bar
        title="检索可视化"
        left-arrow
        fixed
        class="mobile-nav"
        @click-left="onClickLeft"
      />

      <div class="insights-page">
        <section class="hero-card">
          <div class="hero-copy">
            <h1>知识库检索结果可视化</h1>
            <p>查看最近问答中的检索阶段、命中文档分布和来源文件情况。</p>
          </div>
          <div class="hero-side">
            <div class="hero-chip">当前知识库：{{ activeKnowledgeBase?.name || '默认知识库' }}</div>
            <div class="hero-actions">
              <button
                type="button"
                class="chip-button"
                :class="{ active: filterMode === 'current' }"
                @click="filterMode = 'current'"
              >
                当前知识库
              </button>
              <button
                type="button"
                class="chip-button"
                :class="{ active: filterMode === 'all' }"
                @click="filterMode = 'all'"
              >
                全部知识库
              </button>
            </div>
          </div>
        </section>

        <section class="stats-grid">
          <article class="stat-card">
            <span class="stat-label">最近检索次数</span>
            <strong class="stat-value">{{ filteredHistory.length }}</strong>
          </article>
          <article class="stat-card">
            <span class="stat-label">平均命中片段</span>
            <strong class="stat-value">{{ averageChunkCount }}</strong>
          </article>
          <article class="stat-card">
            <span class="stat-label">涉及文件数</span>
            <strong class="stat-value">{{ uniqueSourceCount }}</strong>
          </article>
        </section>

        <div class="content-grid">
          <section class="panel-card">
            <div class="panel-head">
              <h2>检索阶段分布</h2>
              <span>{{ totalStageCount }} 个阶段事件</span>
            </div>
            <div v-if="stageRows.length > 0" class="stage-list">
              <div
                v-for="row in stageRows"
                :key="row.stage"
                class="stage-row"
              >
                <div class="stage-meta">
                  <span class="stage-name">{{ row.label }}</span>
                  <span class="stage-count">{{ row.count }}</span>
                </div>
                <div class="stage-track">
                  <div class="stage-fill" :style="{ width: `${row.percent}%` }"></div>
                </div>
              </div>
            </div>
            <div v-else class="empty-card">还没有可展示的检索记录。</div>
          </section>

          <section class="panel-card">
            <div class="panel-head">
              <h2>命中文件热度</h2>
              <span>{{ sourceRows.length }} 个来源</span>
            </div>
            <div v-if="sourceRows.length > 0" class="source-list">
              <div
                v-for="row in sourceRows"
                :key="row.source"
                class="source-row"
              >
                <span class="source-name">{{ row.source }}</span>
                <span class="source-count">{{ row.count }} 次</span>
              </div>
            </div>
            <div v-else class="empty-card">暂时没有来源文件数据。</div>
          </section>
        </div>

        <section class="panel-card">
          <div class="panel-head">
            <h2>最近检索记录</h2>
            <span>{{ filteredHistory.length }} 条</span>
          </div>

          <div v-if="filteredHistory.length > 0" class="history-list">
            <article
              v-for="entry in filteredHistory"
              :key="entry.id || `${entry.sessionId}-${entry.timestamp}`"
              class="history-card"
            >
              <div class="history-top">
                <div>
                  <h3>{{ entry.query }}</h3>
                  <p>{{ entry.knowledgeBaseName || '默认知识库' }} · {{ formatTime(entry.timestamp) }}</p>
                </div>
                <button type="button" class="open-button" @click="openSession(entry.sessionId)">
                  打开会话
                </button>
              </div>

              <div class="stage-tags">
                <span
                  v-for="(step, index) in entry.thinking || []"
                  :key="`${entry.id || entry.sessionId}-${index}`"
                  class="stage-tag"
                >
                  {{ stageLabelMap[step.stage] || step.stage || '处理' }}
                </span>
              </div>

              <div v-if="collectDocuments(entry).length > 0" class="doc-list">
                <div
                  v-for="(doc, index) in collectDocuments(entry).slice(0, 3)"
                  :key="`${entry.id || entry.sessionId}-doc-${index}`"
                  class="doc-item"
                >
                  <span class="doc-source">{{ doc.source }}</span>
                  <span class="doc-preview">{{ doc.preview }}</span>
                </div>
              </div>
            </article>
          </div>
          <div v-else class="empty-card">
            先去发起几轮知识对话，这里会自动沉淀最近的检索可视化记录。
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import DesktopSidebar from '../components/DesktopSidebar.vue';
import { useKnowledgeBaseStore } from '../store/knowledgeBase';
import { navigateBySidebarKey } from '../utils/sidebarNavigation';

const router = useRouter();
const knowledgeBaseStore = useKnowledgeBaseStore();

const THINKING_HISTORY_KEY = 'ai_thinking_history';
const historyEntries = ref([]);
const filterMode = ref('current');

const stageLabelMap = {
  retrieval: '检索',
  hyde: 'HyDE',
  reorder: '重排序',
  summarize: '总结',
};

const activeKnowledgeBase = computed(() => knowledgeBaseStore.activeKnowledgeBase);

const filteredHistory = computed(() => {
  if (filterMode.value === 'all') {
    return historyEntries.value;
  }

  const activeId = activeKnowledgeBase.value?.id;
  if (!activeId) {
    return historyEntries.value;
  }

  return historyEntries.value.filter((entry) => entry.knowledgeBaseId === activeId);
});

const totalStageCount = computed(() => {
  return filteredHistory.value.reduce((sum, entry) => sum + (entry.thinking?.length || 0), 0);
});

const averageChunkCount = computed(() => {
  if (filteredHistory.value.length === 0) return 0;
  const totalChunks = filteredHistory.value.reduce((sum, entry) => {
    const retrievalStep = (entry.thinking || []).find((step) => step.stage === 'retrieval' && step.details?.chunk_count);
    return sum + (retrievalStep?.details?.chunk_count || 0);
  }, 0);
  return Math.round((totalChunks / filteredHistory.value.length) * 10) / 10;
});

const uniqueSourceCount = computed(() => {
  return sourceRows.value.length;
});

const stageRows = computed(() => {
  const counts = new Map();
  for (const entry of filteredHistory.value) {
    for (const step of entry.thinking || []) {
      const key = step.stage || 'unknown';
      counts.set(key, (counts.get(key) || 0) + 1);
    }
  }

  const total = Array.from(counts.values()).reduce((sum, count) => sum + count, 0) || 1;
  return Array.from(counts.entries())
    .map(([stage, count]) => ({
      stage,
      label: stageLabelMap[stage] || stage || '处理',
      count,
      percent: Math.round((count / total) * 100),
    }))
    .sort((a, b) => b.count - a.count);
});

const sourceRows = computed(() => {
  const counts = new Map();
  for (const entry of filteredHistory.value) {
    for (const doc of collectDocuments(entry)) {
      const key = doc.source || '未知来源';
      counts.set(key, (counts.get(key) || 0) + 1);
    }
  }

  return Array.from(counts.entries())
    .map(([source, count]) => ({ source, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 8);
});

const loadHistory = () => {
  try {
    historyEntries.value = JSON.parse(localStorage.getItem(THINKING_HISTORY_KEY) || '[]');
  } catch (error) {
    console.error('loadHistory error:', error);
    historyEntries.value = [];
  }
};

const collectDocuments = (entry) => {
  const docs = [];
  for (const step of entry.thinking || []) {
    if (Array.isArray(step.details?.documents)) {
      docs.push(...step.details.documents);
    }
  }
  return docs;
};

const handleSidebarNavigate = (key) => {
  navigateBySidebarKey(router, key);
};

const goToAIChat = () => {
  router.push('/aichat');
};

const onClickLeft = () => {
  router.back();
};

const openSession = (sessionId) => {
  if (!sessionId) return;
  router.push(`/aichat/${sessionId}`);
};

const formatTime = (timestamp) => {
  if (!timestamp) return '';
  return new Date(timestamp).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

onMounted(async () => {
  await knowledgeBaseStore.ensureKnowledgeBasesLoaded();
  loadHistory();
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

.insights-page {
  padding: 26px 28px 30px;
}

.hero-card,
.panel-card,
.stat-card,
.history-card {
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

.hero-side {
  display: grid;
  gap: 12px;
}

.hero-chip,
.chip-button,
.stage-tag,
.open-button {
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.hero-chip {
  padding: 9px 14px;
  background: #ffffff;
  border: 1px solid #d8e4fa;
  color: #48607f;
}

.hero-actions {
  display: flex;
  gap: 10px;
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
  grid-template-columns: repeat(3, minmax(0, 1fr));
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

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr);
  gap: 18px;
  margin-bottom: 18px;
}

.panel-card {
  border-radius: 28px;
  padding: 22px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.panel-head h2 {
  margin: 0;
  font-size: 18px;
  color: #1f2d48;
}

.panel-head span {
  color: #7b89a3;
  font-size: 13px;
}

.stage-list,
.source-list,
.history-list {
  display: grid;
  gap: 12px;
}

.stage-row {
  display: grid;
  gap: 8px;
}

.stage-meta,
.source-row,
.history-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.stage-name,
.source-name,
.history-top h3,
.doc-source {
  color: #20314f;
  font-weight: 600;
}

.stage-count,
.source-count,
.history-top p,
.doc-preview {
  color: #70809e;
  font-size: 13px;
}

.stage-track {
  width: 100%;
  height: 10px;
  border-radius: 999px;
  background: #eef3fb;
  overflow: hidden;
}

.stage-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #5f85ff 0%, #84afff 100%);
}

.source-row {
  padding: 12px 14px;
  border-radius: 18px;
  background: #f9fbff;
  border: 1px solid #edf2fb;
}

.history-card {
  padding: 18px;
  border-radius: 22px;
}

.history-top h3 {
  margin: 0 0 6px;
  font-size: 16px;
}

.history-top p {
  margin: 0;
}

.open-button {
  border: 1px solid #cad8f5;
  background: #f7faff;
  color: #3558ff;
  padding: 8px 12px;
}

.stage-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 14px 0;
}

.stage-tag {
  padding: 6px 10px;
  background: #eef4ff;
  color: #3f63f4;
}

.doc-list {
  display: grid;
  gap: 10px;
}

.doc-item {
  padding: 12px 14px;
  border-radius: 16px;
  background: #f9fbff;
  border: 1px solid #edf2fb;
}

.doc-source {
  display: block;
  margin-bottom: 6px;
}

.doc-preview {
  display: block;
  line-height: 1.6;
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

  .insights-page {
    padding: 60px 12px 24px;
  }

  .hero-card,
  .content-grid {
    display: grid;
  }

  .hero-card {
    grid-template-columns: 1fr;
  }

  .stats-grid,
  .content-grid {
    grid-template-columns: 1fr;
  }

  .hero-copy h1 {
    font-size: 22px;
  }
}
</style>
