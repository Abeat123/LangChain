<template>
  <div class="page-shell">
    <desktop-sidebar
      active-section="knowledge-spaces"
      :show-history="false"
      :show-new-chat="true"
      @navigate="handleSidebarNavigate"
      @new-chat="goToAIChat"
    />

    <main class="page-main">
      <van-nav-bar
        title="多知识库切换"
        left-arrow
        fixed
        class="mobile-nav"
        @click-left="onClickLeft"
      />

      <div class="spaces-page">
        <section class="hero-card">
          <div class="hero-copy">
            <h1>多知识库切换</h1>
            <p>创建独立知识库空间，并随时切换当前问答和上传所使用的知识库。</p>
          </div>
          <div class="hero-chip">当前使用：{{ activeKnowledgeBase?.name || '默认知识库' }}</div>
        </section>

        <div class="spaces-grid">
          <section class="panel-card">
            <div class="panel-head">
              <h2>新建知识库</h2>
              <span>与现有配色和布局保持一致</span>
            </div>

            <van-field
              v-model="createForm.name"
              label="名称"
              placeholder="例如：产品文档库"
              maxlength="32"
            />
            <van-field
              v-model="createForm.description"
              label="说明"
              type="textarea"
              rows="3"
              autosize
              maxlength="120"
              placeholder="简要说明该知识库的用途"
            />

            <div class="form-actions">
              <van-button type="primary" @click="handleCreateBase" :loading="submitting">
                创建并切换
              </van-button>
              <van-button plain @click="router.push('/knowledgebase')">
                去管理文档
              </van-button>
            </div>
          </section>

          <section class="panel-card">
            <div class="panel-head">
              <h2>知识库列表</h2>
              <span>{{ knowledgeBaseStore.knowledgeBases.length }} 个空间</span>
            </div>

            <div v-if="knowledgeBaseStore.knowledgeBases.length > 0" class="space-list">
              <article
                v-for="base in knowledgeBaseStore.knowledgeBases"
                :key="base.id"
                class="space-card"
                :class="{ active: knowledgeBaseStore.activeKnowledgeBaseId === base.id }"
              >
                <div class="space-top">
                  <div>
                    <div class="space-title-row">
                      <h3>{{ base.name }}</h3>
                      <span v-if="base.is_default" class="default-tag">默认</span>
                    </div>
                    <p>{{ base.description || '暂无说明' }}</p>
                  </div>
                  <div class="space-count">{{ base.document_count }} 份文档</div>
                </div>

                <div class="space-actions">
                  <van-button
                    size="small"
                    type="primary"
                    plain
                    :disabled="knowledgeBaseStore.activeKnowledgeBaseId === base.id"
                    @click="setActiveBase(base.id)"
                  >
                    设为当前
                  </van-button>
                  <van-button
                    size="small"
                    plain
                    @click="renameBase(base)"
                  >
                    重命名
                  </van-button>
                  <van-button
                    v-if="!base.is_default"
                    size="small"
                    type="danger"
                    plain
                    @click="removeBase(base)"
                  >
                    删除
                  </van-button>
                </div>
              </article>
            </div>
            <div v-else class="empty-card">暂时没有知识库空间。</div>
          </section>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { showDialog, showToast } from 'vant';

import DesktopSidebar from '../components/DesktopSidebar.vue';
import { useKnowledgeBaseStore } from '../store/knowledgeBase';
import { navigateBySidebarKey } from '../utils/sidebarNavigation';

const router = useRouter();
const knowledgeBaseStore = useKnowledgeBaseStore();

const createForm = reactive({
  name: '',
  description: '',
});
const submitting = ref(false);

const activeKnowledgeBase = computed(() => knowledgeBaseStore.activeKnowledgeBase);

const handleSidebarNavigate = (key) => {
  navigateBySidebarKey(router, key);
};

const goToAIChat = () => {
  router.push('/aichat');
};

const onClickLeft = () => {
  router.back();
};

const setActiveBase = async (baseId) => {
  knowledgeBaseStore.setActiveKnowledgeBase(baseId);
  showToast('已切换当前知识库');
};

const handleCreateBase = async () => {
  const name = createForm.name.trim();
  if (!name) {
    showToast('请输入知识库名称');
    return;
  }

  submitting.value = true;
  try {
    await knowledgeBaseStore.createKnowledgeBase({
      name,
      description: createForm.description.trim(),
    });
    createForm.name = '';
    createForm.description = '';
    showToast('知识库创建成功');
  } catch (error) {
    console.error('handleCreateBase error:', error);
    showToast(error.response?.data?.detail || error.response?.data?.message || '创建失败');
  } finally {
    submitting.value = false;
  }
};

const renameBase = async (base) => {
  const nextName = window.prompt('请输入新的知识库名称', base.name);
  if (nextName === null) return;
  const normalizedName = nextName.trim();
  if (!normalizedName || normalizedName === base.name) return;

  try {
    await knowledgeBaseStore.updateKnowledgeBase(base.id, {
      name: normalizedName,
      description: base.description || '',
    });
    showToast('知识库名称已更新');
  } catch (error) {
    console.error('renameBase error:', error);
    showToast(error.response?.data?.detail || error.response?.data?.message || '更新失败');
  }
};

const removeBase = (base) => {
  showDialog({
    title: '确认删除',
    message: `删除“${base.name}”后，该知识库下文档也会一起移除。`,
    showCancelButton: true,
  }).then(async (action) => {
    if (action !== 'confirm') return;

    try {
      await knowledgeBaseStore.deleteKnowledgeBase(base.id);
      showToast('知识库已删除');
    } catch (error) {
      console.error('removeBase error:', error);
      showToast(error.response?.data?.detail || error.response?.data?.message || '删除失败');
    }
  });
};

onMounted(async () => {
  await knowledgeBaseStore.ensureKnowledgeBasesLoaded();
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

.spaces-page {
  padding: 26px 28px 30px;
}

.hero-card,
.panel-card,
.space-card {
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

.hero-chip,
.default-tag,
.space-count {
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.hero-chip {
  padding: 10px 14px;
  background: #ffffff;
  border: 1px solid #d8e4fa;
  color: #48607f;
}

.spaces-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.25fr);
  gap: 18px;
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

.panel-head span {
  color: #7b89a3;
  font-size: 13px;
}

.panel-card :deep(.van-field) {
  margin-bottom: 12px;
  border-radius: 18px;
  background: #f9fbff;
}

.panel-card :deep(.van-field__label),
.panel-card :deep(.van-field__control) {
  color: #20314f;
}

.form-actions,
.space-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.form-actions {
  margin-top: 8px;
}

.space-list {
  display: grid;
  gap: 12px;
}

.space-card {
  padding: 18px;
  border-radius: 22px;
}

.space-card.active {
  border-color: #bfd1ff;
  background: #fbfdff;
}

.space-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 14px;
}

.space-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.space-title-row h3 {
  margin: 0;
  font-size: 17px;
  color: #20314f;
}

.space-top p {
  margin: 0;
  color: #6f7f9c;
  line-height: 1.7;
}

.default-tag {
  padding: 4px 10px;
  background: #eef4ff;
  color: #3f63f4;
}

.space-count {
  padding: 7px 12px;
  background: #f7faff;
  color: #5f7090;
  border: 1px solid #e3ebfa;
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

  .spaces-page {
    padding: 60px 12px 24px;
  }

  .hero-card,
  .spaces-grid,
  .space-top {
    display: grid;
  }

  .spaces-grid {
    grid-template-columns: 1fr;
  }

  .hero-copy h1 {
    font-size: 22px;
  }
}
</style>
