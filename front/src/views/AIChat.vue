<template>
  <div class="page-shell">
    <desktop-sidebar
      active-section="aichat"
      :show-history="true"
      :show-new-chat="true"
      :loading="sessionStore.isLoading"
      :session-groups="sidebarSessionGroups"
      :active-session-id="activeSidebarSessionId"
      @navigate="handleSidebarNavigate"
      @new-chat="startFreshChat"
      @open-session="openSession"
    />

    <main class="page-main">
      <van-nav-bar
        class="chat-nav-bar"
        title="AI 问答"
        fixed
        right-text="会话"
        @click-right="goToSessions"
      />

      <div class="chat-stage" :class="{ 'has-messages': hasRealConversation }">
        <template v-if="!hasRealConversation">
          <section class="landing-stage">
            <div class="landing-brand">
              <img class="landing-logo" :src="allInRagLogo" alt="All in RAG" />
              <span class="landing-brand-text">基于 LangChain 的 RAG 知识库智能问答系统</span>
            </div>
            <h1>开始新一轮知识对话</h1>
            <p class="landing-subtitle">围绕知识库内容进行问答、总结、解释和追问</p>
            <div class="knowledge-base-chip">
              当前知识库：{{ activeKnowledgeBase?.name || '默认知识库' }}
            </div>

            <div class="landing-input-card">
              <van-field
                v-model="userInput"
                rows="4"
                autosize
                type="textarea"
                placeholder="请输入你的问题"
                class="chat-input landing-input"
                @keypress.enter.prevent="sendMessage"
              />
              <div class="input-toolbar">
                <div class="input-actions">
                  <button type="button" class="icon-button" aria-label="attach">+</button>
                  <button
                    type="button"
                    class="send-fab"
                    :disabled="isLoading || !userInput.trim()"
                    @click="sendMessage"
                  >
                    >
                  </button>
                </div>
              </div>
            </div>
          </section>
        </template>

        <template v-else>
          <div class="messages-container" ref="messagesContainer">
            <div
              v-for="(message, index) in messages"
              :key="index"
              :class="['message', message.role === 'user' ? 'user-message' : 'ai-message']"
            >
              <div class="message-content">
                <div v-if="message.thinking && message.thinking.length > 0" class="thinking-section">
                  <div class="thinking-header" @click="toggleThinking(message)">
                    <span class="thinking-label">思考过程</span>
                    <span class="thinking-toggle">{{ message.thinkingCollapsed ? '展开' : '收起' }}</span>
                  </div>
                  <div v-show="!message.thinkingCollapsed" class="thinking-body">
                    <div v-for="(step, sIndex) in message.thinking" :key="sIndex" class="thinking-step">
                      <span class="thinking-stage-label" :style="{ backgroundColor: getStageColor(step.stage) }">
                        {{ getStageLabel(step.stage) }}
                      </span>
                      <span class="thinking-step-content">{{ step.content }}</span>
                      <div v-if="step.details" class="thinking-details">
                        <template v-if="step.details.documents">
                          <div v-if="step.details.file_count" class="thinking-detail-text">
                            共 {{ step.details.chunk_count || step.details.documents.length }} 个相关片段，来自
                            {{ step.details.file_count }} 个文件
                          </div>
                          <div
                            v-for="(doc, dIndex) in step.details.documents.slice(0, 3)"
                            :key="dIndex"
                            class="thinking-doc-item"
                          >
                            <span class="thinking-doc-source">{{ doc.source }}</span>
                            <span class="thinking-doc-preview">{{ truncateText(doc.preview, 48) }}</span>
                          </div>
                          <div v-if="step.details.documents.length > 3" class="thinking-doc-more">
                            还有 {{ step.details.documents.length - 3 }} 个片段
                          </div>
                        </template>
                        <template v-else-if="step.details.scores">
                          <div
                            v-for="(sc, cIndex) in step.details.scores.slice(0, 3)"
                            :key="cIndex"
                            class="thinking-score-item"
                          >
                            <span>#{{ sc.rank || sc.index }}</span>
                            <span>{{ (sc.score * 100).toFixed(0) }}%</span>
                            <span class="thinking-score-preview">{{ truncateText(sc.preview, 40) }}</span>
                          </div>
                        </template>
                        <template v-else-if="step.details.hypothetical_doc_preview">
                          <div class="thinking-detail-text">
                            {{ truncateText(step.details.hypothetical_doc_preview, 80) }}
                          </div>
                        </template>
                        <template v-else>
                          <div v-for="(val, key) in step.details" :key="key" class="thinking-detail-kv">
                            <span class="thinking-detail-key">{{ key }}:</span>
                            <span class="thinking-detail-val">
                              {{ typeof val === 'object' ? JSON.stringify(val) : val }}
                            </span>
                          </div>
                        </template>
                      </div>
                    </div>
                  </div>
                </div>

                <div v-if="message.content" v-html="formatMessage(message.content)"></div>

                <div
                  v-if="message.role === 'assistant' && message.content"
                  class="feedback-row"
                >
                  <button
                    type="button"
                    class="feedback-button"
                    :class="{ active: message.feedbackType === 'up' }"
                    @click="submitFeedback(message, index, 'up')"
                  >
                    有帮助
                  </button>
                  <button
                    type="button"
                    class="feedback-button"
                    :class="{ active: message.feedbackType === 'down' }"
                    @click="submitFeedback(message, index, 'down')"
                  >
                    需改进
                  </button>
                </div>

                <div
                  v-if="message.role === 'assistant' && !message.content && (!message.thinking || message.thinking.length === 0)"
                  class="typing-indicator"
                >
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>

          <div class="input-container chat-thread-input">
            <div class="thread-context">
              当前知识库：{{ activeKnowledgeBase?.name || '默认知识库' }}
            </div>
            <van-field
              v-model="userInput"
              rows="1"
              autosize
              type="textarea"
              placeholder="继续追问"
              class="chat-input"
              @keypress.enter.prevent="sendMessage"
            />
            <div class="thread-input-actions">
              <button type="button" class="icon-button" aria-label="attach">+</button>
              <van-button
                type="primary"
                class="send-button"
                :disabled="isLoading || !userInput.trim()"
                @click="sendMessage"
              >
                发送
              </van-button>
            </div>
          </div>
        </template>
      </div>

      <tab-bar class="mobile-tabbar" />
    </main>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, nextTick, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { showToast } from 'vant';
import { marked } from 'marked';
import { markedHighlight } from 'marked-highlight';
import DOMPurify from 'dompurify';
import hljs from 'highlight.js';
import 'highlight.js/styles/monokai-sublime.css';
import 'highlight.js/lib/common';

import DesktopSidebar from '../components/DesktopSidebar.vue';
import TabBar from '../components/TabBar.vue';
import allInRagLogo from '../assets/all-in-rag-logo.svg';
import { useUserStore } from '../store/user';
import { useSessionStore } from '../store/session';
import { useKnowledgeBaseStore } from '../store/knowledgeBase';
import { navigateBySidebarKey } from '../utils/sidebarNavigation';

const DEFAULT_ASSISTANT_MESSAGE =
  '你好，我是你的 AI 助手。你可以继续追问，让我总结文档，或者把复杂概念讲得更通俗一些。';

const messages = ref([{ role: 'assistant', content: DEFAULT_ASSISTANT_MESSAGE }]);
const userInput = ref('');
const messagesContainer = ref(null);
const isLoading = ref(false);
const sessionId = ref('');
const autoCollapseTimer = ref(null);

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const sessionStore = useSessionStore();
const knowledgeBaseStore = useKnowledgeBaseStore();

const activeKnowledgeBase = computed(() => knowledgeBaseStore.activeKnowledgeBase);

const activeSidebarSessionId = computed(() => route.params.sessionId || sessionId.value || '');

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

const hasRealConversation = computed(
  () =>
    messages.value.length > 1 ||
    (messages.value.length === 1 && messages.value[0]?.role !== 'assistant') ||
    (messages.value.length === 1 && messages.value[0]?.content !== DEFAULT_ASSISTANT_MESSAGE)
);

marked.use(
  markedHighlight({
    langPrefix: 'hljs language-',
    highlight(code, lang) {
      const language = hljs.getLanguage(lang) ? lang : 'plaintext';
      return hljs.highlight(code, { language }).value;
    },
  })
);

const formatMessage = (content) => {
  if (!content) return '';
  try {
    const parsed = marked(content, {
      breaks: true,
      gfm: true,
      headerIds: false,
      mangle: false,
    });
    return DOMPurify.sanitize(parsed);
  } catch (error) {
    console.error('Markdown parse error:', error);
    return content;
  }
};

const stageConfig = {
  retrieval: { label: '检索', color: '#5aa8ff' },
  hyde: { label: 'HyDE', color: '#7f7bff' },
  reorder: { label: '重排序', color: '#4fd0ac' },
  summarize: { label: '总结', color: '#ffbf69' },
};

const getStageLabel = (stage) => stageConfig[stage]?.label || stage || '处理中';
const getStageColor = (stage) => stageConfig[stage]?.color || '#8fa8cf';

const truncateText = (text, maxLen) => {
  if (!text) return '';
  return text.length > maxLen ? `${text.slice(0, maxLen)}...` : text;
};

const THINKING_HISTORY_KEY = 'ai_thinking_history';

const saveThinkingToHistory = (sid, query, thinking) => {
  if (!sid || !thinking || thinking.length === 0) return;
  try {
    let history = JSON.parse(localStorage.getItem(THINKING_HISTORY_KEY) || '[]');
    history = history.filter((entry) => !(entry.sessionId === sid && entry.query === query));
    const timestamp = Date.now();
    history.unshift({
      id: `${sid}-${timestamp}`,
      sessionId: sid,
      query,
      thinking,
      timestamp,
      knowledgeBaseId: activeKnowledgeBase.value?.id || '',
      knowledgeBaseName: activeKnowledgeBase.value?.name || '默认知识库',
    });
    localStorage.setItem(THINKING_HISTORY_KEY, JSON.stringify(history.slice(0, 20)));
  } catch (error) {
    console.error('saveThinkingToHistory error:', error);
  }
};

const loadThinkingFromHistory = (sid, query = '') => {
  if (!sid) return null;
  try {
    const history = JSON.parse(localStorage.getItem(THINKING_HISTORY_KEY) || '[]');
    const matched = history.find((entry) => entry.sessionId === sid && entry.query === query);
    return matched?.thinking || null;
  } catch (error) {
    console.error('loadThinkingFromHistory error:', error);
    return null;
  }
};

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

const toggleThinking = (message) => {
  message.thinkingCollapsed = !message.thinkingCollapsed;
  if (autoCollapseTimer.value) {
    clearTimeout(autoCollapseTimer.value);
    autoCollapseTimer.value = null;
  }
};

const goToSessions = () => {
  router.push('/sessions');
};

const goToProfile = () => {
  router.push('/my');
};

const handleSidebarNavigate = (key) => {
  if (key === 'aichat') {
    if (route.params.sessionId) {
      router.push('/aichat');
    }
    return;
  }
  navigateBySidebarKey(router, key);
};

const openSession = (sid) => {
  if (!sid) return;
  router.push(`/aichat/${sid}`);
};

const startFreshChat = () => {
  sessionId.value = '';
  sessionStore.setCurrentSession(null);
  userInput.value = '';
  messages.value = [{ role: 'assistant', content: DEFAULT_ASSISTANT_MESSAGE }];
  if (route.params.sessionId) {
    router.push('/aichat');
  }
};

const ensureSessionsLoaded = async () => {
  if (!userStore.getLoginStatus) return;
  if (!userStore.userInfo) {
    const userInfoResult = await userStore.getUserInfoDetail();
    if (!userInfoResult.success) return;
  }
  const userId = userStore.userInfo?.uuid || userStore.userInfo?.id || userStore.userInfo?.user_id;
  if (!userId) return;
  await sessionStore.getUserSessions(userId);
};

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return;

  if (!userStore.getLoginStatus) {
    showToast('请先登录');
    return;
  }

  const userMessage = userInput.value.trim();
  messages.value.push({ role: 'user', content: userMessage });
  userInput.value = '';

  messages.value.push({
    role: 'assistant',
    content: '',
    thinking: [],
    thinkingCollapsed: false,
    thinkingAutoCollapsed: false,
  });

  await nextTick();
  scrollToBottom();

  isLoading.value = true;
  try {
    await fetchAIResponse(userMessage);
  } catch (error) {
    console.error('Error fetching AI response:', error);
    messages.value[messages.value.length - 1].content = `发生错误: ${error.message || '请检查网络连接和接口状态'}`;
  } finally {
    isLoading.value = false;
    await nextTick();
    scrollToBottom();
    await ensureSessionsLoaded();
  }
};

const fetchAIResponse = async (userMessage) => {
  const token = localStorage.getItem('jwt_token') || userStore.token;
  const response = await fetch('/chat/agent/query/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      session_id: sessionId.value || undefined,
      query: userMessage,
      knowledge_base_id: activeKnowledgeBase.value?.id || undefined,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let aiResponse = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const data = line.slice(6);
      if (!data) continue;

      try {
        const json = JSON.parse(data);

        switch (json.type) {
          case 'thinking': {
            const idx = messages.value.length - 1;
            if (messages.value[idx].role === 'assistant') {
              const newStep = {
                stage: json.stage || '',
                content: json.content || '',
                details: json.details || null,
              };

              messages.value[idx] = {
                ...messages.value[idx],
                thinking: [...messages.value[idx].thinking, newStep],
              };
              await nextTick();
              await new Promise((resolve) => requestAnimationFrame(resolve));
              scrollToBottom();
            }
            break;
          }
          case 'response': {
            const lastMsg = messages.value[messages.value.length - 1];
            if (!lastMsg.thinkingAutoCollapsed && lastMsg.thinking.length > 0) {
              lastMsg.thinkingAutoCollapsed = true;
              if (autoCollapseTimer.value) clearTimeout(autoCollapseTimer.value);
              autoCollapseTimer.value = setTimeout(() => {
                lastMsg.thinkingCollapsed = true;
                autoCollapseTimer.value = null;
              }, 1500);
            }

            const content = json.content || '';
            if (content) {
              aiResponse += content;
              const displayContent = lastMsg.content || '';
              const remainingContent = aiResponse.substring(displayContent.length);

              for (const char of remainingContent) {
                lastMsg.content += char;
                await new Promise((resolve) => setTimeout(resolve, 8));
                scrollToBottom();
              }
            }

            if (json.session_id && typeof json.session_id === 'string' && json.session_id.trim()) {
              sessionId.value = json.session_id;
            }
            break;
          }
          case 'done': {
            const sid = json.session_id;
            if (sid && typeof sid === 'string' && sid.trim()) {
              sessionId.value = sid;
              const lastMsg = messages.value[messages.value.length - 1];
              if (lastMsg && lastMsg.role === 'assistant') {
                saveThinkingToHistory(sid, userMessage, lastMsg.thinking);
              }
              if (!route.params.sessionId) {
                router.push(`/aichat/${sid}`);
              }
            }
            break;
          }
          case 'error':
            throw new Error(json.content || '接口返回错误');
          default:
            break;
        }
      } catch (error) {
        console.error('Error parsing SSE data:', error);
      }
    }
  }

  if (!aiResponse) {
    messages.value[messages.value.length - 1].content =
      '抱歉，我暂时没有生成有效回复。请稍后再试，或换一种问法。';
  }
};

const loadSessionHistory = (session) => {
  if (!session?.history?.length) return;

  messages.value = [];
  session.history.forEach(([userMsg, aiMsg]) => {
    messages.value.push({ role: 'user', content: userMsg });
    const savedThinking = loadThinkingFromHistory(session.session_id, userMsg);
    messages.value.push({
      role: 'assistant',
      content: aiMsg,
      thinking: savedThinking || [],
      thinkingCollapsed: true,
      thinkingAutoCollapsed: true,
    });
  });

  sessionId.value = session.session_id;
};

const getQuestionForAssistantMessage = (messageIndex) => {
  for (let index = messageIndex - 1; index >= 0; index -= 1) {
    if (messages.value[index]?.role === 'user') {
      return messages.value[index].content || '';
    }
  }
  return '';
};

const submitFeedback = async (message, messageIndex, feedbackType) => {
  if (!message?.content) return;
  if (!userStore.getLoginStatus) {
    showToast('请先登录');
    return;
  }

  const question = getQuestionForAssistantMessage(messageIndex);
  if (!question) {
    showToast('当前回答缺少对应问题，暂时无法反馈');
    return;
  }

  const promptText =
    feedbackType === 'down'
      ? '可选：补充说明哪里需要改进'
      : '可选：补充说明哪里对你有帮助';
  const comment = window.prompt(promptText, message.feedbackComment || '');
  if (comment === null) {
    return;
  }

  try {
    const token = localStorage.getItem('jwt_token') || userStore.token;
    const response = await fetch('/chat/feedback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        session_id: sessionId.value || route.params.sessionId || undefined,
        knowledge_base_id: activeKnowledgeBase.value?.id || undefined,
        question,
        answer: message.content,
        feedback_type: feedbackType,
        comment: comment || undefined,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || error.message || '反馈提交失败');
    }

    message.feedbackType = feedbackType;
    message.feedbackComment = comment || '';
    showToast(feedbackType === 'up' ? '已记录为有帮助' : '已记录改进建议');
  } catch (error) {
    console.error('submitFeedback error:', error);
    showToast(error.message || '反馈提交失败');
  }
};

watch(
  messages,
  () => {
    nextTick(() => {
      scrollToBottom();
    });
  },
  { deep: true }
);

watch(
  () => route.params.sessionId,
  async (newSessionId) => {
    if (!newSessionId) {
      if (!hasRealConversation.value) {
        messages.value = [{ role: 'assistant', content: DEFAULT_ASSISTANT_MESSAGE }];
      }
      return;
    }
    try {
      const result = await sessionStore.getSession(newSessionId);
      if (result.success && sessionStore.currentSession) {
        loadSessionHistory(sessionStore.currentSession);
      } else {
        showToast('加载会话历史失败');
      }
    } catch (error) {
      console.error('加载会话历史失败:', error);
      showToast('加载会话历史失败');
    }
  },
  { immediate: true }
);

onMounted(async () => {
  await knowledgeBaseStore.ensureKnowledgeBasesLoaded();
  await ensureSessionsLoaded();

  const routeSessionId = route.params.sessionId;
  if (routeSessionId) {
    try {
      const result = await sessionStore.getSession(routeSessionId);
      if (result.success && sessionStore.currentSession) {
        loadSessionHistory(sessionStore.currentSession);
      } else {
        showToast('加载会话历史失败');
      }
    } catch (error) {
      console.error('加载会话历史失败:', error);
      showToast('加载会话历史失败');
    }
  }

  scrollToBottom();
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

.chat-stage {
  min-height: 100vh;
  padding: 26px 32px 28px;
  display: flex;
  flex-direction: column;
}

.chat-stage.has-messages {
  padding-top: 24px;
  background:
    radial-gradient(circle at 78% 8%, rgba(92, 133, 255, 0.08), transparent 32%),
    linear-gradient(180deg, #fbfdff 0%, #ffffff 44%, #f8fbff 100%);
}

.landing-stage {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-bottom: 12vh;
}

.landing-brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  max-width: min(100%, 820px);
  margin-bottom: 18px;
  transform: translateY(-80px);
}

.landing-logo {
  display: block;
  width: clamp(112px, 9vw, 148px);
  height: clamp(132px, 10.6vw, 174px);
  aspect-ratio: 1 / 1.32;
  object-fit: fill;
  flex-shrink: 0;
}

.landing-brand-text {
  color: #1f2d48;
  font-size: clamp(40px, 2.2vw, 34px);
  font-weight: 700;
  letter-spacing: -0.03em;
  white-space: nowrap;
  line-height: 1.16;
}

.landing-stage h1 {
  margin: 0;
  color: #101828;
  font-size: clamp(20px, 1.65vw, 23px);
  font-weight: 800;
  letter-spacing: -0.04em;
}

.landing-subtitle {
  margin: 12px 0 22px;
  color: #8a96aa;
  font-size: 15px;
}

.knowledge-base-chip {
  margin-bottom: 22px;
  padding: 8px 14px;
  border-radius: 999px;
  background: #f5f8ff;
  border: 1px solid #dce7fb;
  color: #48607f;
  font-size: 13px;
  font-weight: 600;
}

.landing-input-card {
  width: min(100%, 690px);
  background: #ffffff;
  border: 1px solid #e7edf7;
  border-radius: 24px;
  box-shadow: 0 18px 42px rgba(146, 165, 201, 0.14);
  padding: 12px 14px 14px;
}

.landing-input {
  margin-bottom: 8px;
}

.landing-input :deep(.van-field__control) {
  min-height: 74px;
}

.input-toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
  gap: 12px;
}

.input-actions,
.thread-input-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.icon-button {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: #55637d;
  font-size: 20px;
  line-height: 1;
}

.icon-button:hover {
  background: #f2f5fb;
}

.send-fab {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #9db4ff 0%, #8ea9ff 100%);
  color: #ffffff;
  font-size: 18px;
  box-shadow: 0 10px 22px rgba(77, 107, 254, 0.2);
}

.send-fab:disabled {
  opacity: 0.5;
  box-shadow: none;
}

.messages-container {
  flex: 1;
  width: min(100%, 960px);
  margin: 0 auto;
  overflow-y: auto;
  padding: 18px 8px 22px;
  scroll-behavior: smooth;
}

.message {
  margin-bottom: 22px;
  max-width: min(74%, 760px);
  position: relative;
}

.user-message {
  margin-left: auto;
  margin-right: auto;
  max-width: min(74%, 760px);
}

.ai-message {
  margin-right: auto;
}

.message-content {
  padding: 18px 20px;
  border-radius: 26px;
  word-break: break-word;
  border: 1px solid #e8eef9;
  box-shadow: 0 16px 34px rgba(155, 174, 210, 0.12);
  line-height: 1.76;
}

.user-message .message-content {
  background: rgba(255, 255, 255, 0.96);
  color: #1f2d48;
  border-color: #dfe8f8;
  border-top-right-radius: 12px;
  border-top-left-radius: 12px;
  box-shadow: 0 16px 34px rgba(155, 174, 210, 0.12);
}

.ai-message .message-content {
  background: rgba(255, 255, 255, 0.96);
  color: #1f2d48;
  border-top-left-radius: 12px;
  border-color: #dfe8f8;
}

.feedback-row {
  margin-top: 14px;
  display: flex;
  gap: 10px;
}

.feedback-button {
  border: 1px solid #d8e4fa;
  background: linear-gradient(180deg, #ffffff 0%, #f6f9ff 100%);
  color: #50647f;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
  padding: 8px 12px;
  border-radius: 999px;
}

.feedback-button.active {
  background: #e8efff;
  border-color: #bfd1ff;
  color: #2f56ff;
}

.input-container {
  width: min(100%, 960px);
  margin: 0 auto;
  padding: 14px 16px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid #dfe8f8;
  box-shadow: 0 18px 48px rgba(126, 150, 194, 0.18);
  backdrop-filter: blur(12px);
}

.chat-thread-input {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px;
}

.thread-context {
  width: 100%;
  color: #587094;
  font-size: 13px;
  font-weight: 600;
}

.chat-input {
  flex: 1;
  padding: 0;
}

.chat-input :deep(.van-field) {
  background: transparent;
  padding: 0;
}

.chat-input :deep(.van-field__control) {
  color: #1f2d48;
  line-height: 1.75;
  font-size: 16px;
}

.send-button {
  min-width: 88px;
  height: 40px;
  border-radius: 999px;
  padding: 0 20px;
  box-shadow: 0 10px 24px rgba(77, 107, 254, 0.18);
}

.typing-indicator {
  display: inline-flex;
  gap: 6px;
  padding: 6px 0 2px;
}

.typing-indicator span {
  height: 8px;
  width: 8px;
  background-color: rgba(77, 107, 254, 0.55);
  border-radius: 50%;
  display: inline-block;
  animation: bounce 1.5s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%,
  60%,
  100% {
    transform: translateY(0);
  }

  30% {
    transform: translateY(-5px);
  }
}

:deep(pre) {
  background: #f4f7ff;
  padding: 15px;
  border-radius: 14px;
  overflow-x: auto;
  margin: 10px 0;
  color: #1d2b53;
  border: 1px solid #dde6fb;
}

:deep(pre code) {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
  color: inherit;
}

:deep(code) {
  font-family: "Consolas", "Monaco", "Courier New", monospace;
  background-color: rgba(77, 107, 254, 0.08);
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 0.9em;
}

:deep(p) {
  margin: 8px 0;
  line-height: 1.7;
}

:deep(ul),
:deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}

:deep(li) {
  margin: 4px 0;
  line-height: 1.6;
}

:deep(a) {
  color: var(--primary-color);
  text-decoration: none;
}

:deep(a:hover) {
  text-decoration: underline;
}

:deep(h1),
:deep(h2),
:deep(h3),
:deep(h4),
:deep(h5),
:deep(h6) {
  margin: 12px 0 8px 0;
  font-weight: 700;
}

:deep(blockquote) {
  border-left: 4px solid rgba(77, 107, 254, 0.46);
  margin: 10px 0;
  color: var(--secondary-text-color);
  background-color: rgba(77, 107, 254, 0.05);
  padding: 10px 14px;
  border-radius: 0 12px 12px 0;
}

:deep(hr) {
  border: 0;
  border-top: 1px solid rgba(140, 163, 212, 0.18);
  margin: 16px 0;
}

:deep(img) {
  max-width: 100%;
  border-radius: 10px;
  margin: 8px 0;
}

:deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0;
}

:deep(th),
:deep(td) {
  border: 1px solid rgba(140, 163, 212, 0.18);
  padding: 8px;
  text-align: left;
}

:deep(th) {
  background-color: rgba(77, 107, 254, 0.04);
  font-weight: 700;
}

.thinking-section {
  margin-bottom: 14px;
  border-left: 3px solid rgba(77, 107, 254, 0.55);
  background: linear-gradient(180deg, #f8fbff 0%, #eef5ff 100%);
  border-radius: 18px;
  padding: 12px 14px;
  font-size: 12px;
  box-shadow: inset 0 0 0 1px rgba(214, 225, 246, 0.7);
}

.thinking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
  padding: 2px 2px 4px;
}

.thinking-label {
  color: #24395d;
  font-weight: 700;
  font-size: 13px;
}

.thinking-toggle {
  color: #57729a;
  font-size: 12px;
}

.thinking-body {
  margin-top: 6px;
}

.thinking-step {
  padding: 10px 0;
  border-bottom: 1px solid rgba(140, 163, 212, 0.16);
  line-height: 1.6;
}

.thinking-step:last-child {
  border-bottom: none;
}

.thinking-stage-label {
  display: inline-block;
  font-size: 10px;
  color: #fff;
  padding: 3px 8px;
  border-radius: 999px;
  margin-right: 8px;
  vertical-align: middle;
  line-height: 1.5;
  box-shadow: 0 8px 16px rgba(77, 107, 254, 0.16);
}

.thinking-step-content {
  color: #2f4263;
  font-size: 13px;
  vertical-align: middle;
}

.thinking-details {
  margin-top: 8px;
  padding: 10px 12px;
  background-color: #ffffff;
  border: 1px solid #e7edf8;
  border-radius: 14px;
  font-size: 12px;
  color: #5f7090;
}

.thinking-detail-kv,
.thinking-doc-item,
.thinking-score-item {
  gap: 6px;
  line-height: 1.5;
}

.thinking-detail-kv,
.thinking-score-item {
  display: flex;
}

.thinking-doc-item {
  display: block;
  padding: 6px 0;
}

.thinking-doc-item + .thinking-doc-item {
  border-top: 1px solid rgba(140, 163, 212, 0.12);
}

.thinking-detail-key {
  color: #41516d;
  white-space: nowrap;
}

.thinking-detail-text,
.thinking-detail-val,
.thinking-doc-source,
.thinking-doc-preview,
.thinking-doc-more,
.thinking-score-item,
.thinking-score-preview {
  color: #5f7090;
}

.thinking-doc-source {
  display: block;
  margin-bottom: 2px;
  color: #41516d;
  font-weight: 600;
}

.thinking-doc-preview,
.thinking-score-preview {
  display: block;
  overflow: hidden;
}

.mobile-tabbar,
:deep(.chat-nav-bar) {
  display: none;
}

@media (max-width: 900px) {
  .page-main {
    width: 100%;
  }

  :deep(.chat-nav-bar) {
    display: block;
  }

  .chat-stage {
    min-height: 100vh;
    padding: 58px 0 86px;
  }

  .landing-stage {
    justify-content: flex-start;
    padding: 30px 16px 0;
  }

  .landing-stage h1 {
    font-size: 19px;
    text-align: center;
  }

  .landing-brand {
    gap: 10px;
  }

  .landing-logo {
    width: min(34vw, 112px);
    height: min(44vw, 146px);
  }

  .landing-brand-text {
    font-size: clamp(16px, 4vw, 20px);
  }

  .landing-subtitle {
    text-align: center;
    margin-bottom: 18px;
  }

  .landing-input-card,
  .messages-container,
  .input-container {
    width: auto;
    margin-left: 12px;
    margin-right: 12px;
  }

  .messages-container {
    padding: 16px 0;
  }

  .message {
    max-width: 90%;
  }

  .input-toolbar,
  .chat-thread-input {
    flex-direction: column;
    align-items: stretch;
  }

  .input-actions,
  .thread-input-actions {
    justify-content: flex-end;
  }

  .mobile-tabbar {
    display: block;
  }
}
</style>
