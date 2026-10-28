<template>
  <div class="page-shell">
    <desktop-sidebar
      active-section="knowledgebase"
      :show-history="false"
      :show-new-chat="true"
      @navigate="handleSidebarNavigate"
      @new-chat="goToAIChat"
    />

    <main class="page-main">
      <van-nav-bar
        title="知识库管理"
        left-arrow
        fixed
        class="mobile-nav"
        @click-left="onClickLeft"
      />

      <div class="knowledgebase-content">
        <section class="knowledge-overview">
          <div class="overview-copy">
            <h2>{{ documents.length }} 份文档已入库</h2>
            <p>支持 PDF、TXT、DOCX、PPTX 等格式，上传后会自动切片、向量化并参与检索。</p>
            <div class="active-base-badge">
              当前知识库：{{ activeKnowledgeBase?.name || '默认知识库' }}
            </div>
          </div>
          <div class="overview-state" :class="{ busy: uploading }">
            {{ uploading ? '上传中' : '已就绪' }}
          </div>
        </section>

        <div class="upload-area" @click="openFilePicker" @dragover.prevent @drop.prevent="handleDrop">
          <div class="upload-icon">
            <van-icon name="upload" size="48" />
          </div>
          <p class="upload-text">{{ $t('knowledgebase.uploadText') }}</p>
          <p class="upload-hint">{{ $t('knowledgebase.uploadHint') }}</p>
          <input
            ref="fileInput"
            type="file"
            multiple
            accept=".md,.txt,.pdf,.docx,.pptx"
            class="file-input"
            @change="handleFileSelect"
          />
        </div>

        <div v-if="selectedFiles.length > 0" class="file-list">
          <h3 class="section-title">{{ $t('knowledgebase.selectedFiles') }}</h3>
          <van-cell-group inset>
            <van-cell
              v-for="(file, index) in selectedFiles"
              :key="index"
              :title="file.name"
              :value="formatFileSize(file.size)"
              is-link
              @click="removeFile(index)"
            >
              <template #right-icon>
                <van-icon name="delete" color="#f44" />
              </template>
            </van-cell>
          </van-cell-group>
        </div>

        <van-button
          v-if="selectedFiles.length > 0 && !uploading"
          type="primary"
          block
          @click="uploadFiles"
        >
          {{ $t('knowledgebase.uploadButton') }}
        </van-button>

        <div v-if="uploading || uploadComplete" class="upload-progress">
          <h3 class="section-title">{{ $t('knowledgebase.uploadProgress') }}</h3>
          <div
            v-for="(progress, index) in uploadProgressList"
            :key="index"
            class="progress-item"
          >
            <div class="progress-header">
              <span class="progress-filename">{{ progress.filename }}</span>
              <span class="progress-status" :class="getStatusClass(progress.status)">
                {{ getStatusText(progress.status) }}
              </span>
            </div>
            <van-progress v-if="progress.percentage !== null" :percentage="progress.percentage" />
            <p class="progress-message">{{ progress.message }}</p>
          </div>

          <div v-if="uploadComplete" class="upload-result">
            <van-icon
              :name="failedCount > 0 ? 'warning' : 'success'"
              size="32"
              :color="failedCount > 0 ? '#ee0a24' : '#07c160'"
            />
            <p>{{ $t('knowledgebase.uploadComplete') }}</p>
            <p>{{ successCount }} {{ $t('knowledgebase.success') }}, {{ failedCount }} {{ $t('knowledgebase.failed') }}</p>
          </div>
        </div>

        <div v-if="!uploading" class="document-list">
          <div class="list-header">
            <h3 class="section-title">{{ $t('knowledgebase.documentList') }}</h3>
            <div class="list-actions">
              <span class="document-count">{{ documents.length }} {{ $t('knowledgebase.total') }}</span>
              <van-button
                v-if="documents.length > 0"
                size="small"
                type="danger"
                plain
                @click="handleCleanAll"
              >
                {{ $t('knowledgebase.cleanAll') }}
              </van-button>
            </div>
          </div>

          <van-cell-group inset v-if="documents.length > 0">
            <van-cell
              v-for="doc in documents"
              :key="doc.id"
              :title="doc.original_filename || doc.filename"
              is-link
              @click="viewDocumentDetail(doc)"
            >
              <template #icon>
                <van-icon name="file-text-o" size="18" />
              </template>
              <template #label>
                <div class="doc-meta">
                  <span class="chunk-count">{{ doc.chunk_count }} {{ $t('knowledgebase.chunks') }}</span>
                </div>
              </template>
              <template #right-icon>
                <van-icon
                  name="delete"
                  color="#ee0a24"
                  size="18"
                  class="delete-icon"
                  @click.stop="handleDeleteDocument(doc)"
                />
              </template>
            </van-cell>
          </van-cell-group>

          <div v-else-if="!loadingDocuments" class="empty-state">
            <van-icon name="file-text-o" size="48" color="#ccc" />
            <p>{{ $t('knowledgebase.empty') }}</p>
          </div>

          <van-loading v-if="loadingDocuments" />
        </div>
      </div>
    </main>

    <van-popup v-model:show="showDetail" position="bottom" :style="{ height: '70%' }" round>
      <div class="detail-header">
        <h4>{{ $t('knowledgebase.documentContent') }}</h4>
        <div class="header-actions">
          <van-button size="small" type="primary" plain @click="viewDocumentChunks">
            {{ $t('knowledgebase.viewChunks') }}
          </van-button>
          <van-icon name="close" @click="showDetail = false" />
        </div>
      </div>
      <div class="detail-content">
        <van-loading v-if="loadingDetail" />
        <template v-else>
          <div class="detail-meta">
            <span>{{ currentDocument?.chunk_count }} {{ $t('knowledgebase.chunks') }}</span>
          </div>
          <div class="detail-content-full">
            <pre>{{ currentDocument?.content || currentDocument?.preview }}</pre>
          </div>
        </template>
      </div>
    </van-popup>

    <van-popup v-model:show="showChunks" position="bottom" :style="{ height: '70%' }" round>
      <div class="detail-header">
        <h4>{{ $t('knowledgebase.chunkList') }}</h4>
        <van-icon name="close" @click="showChunks = false" />
      </div>
      <div class="detail-content">
        <van-loading v-if="loadingChunks" />
        <template v-else>
          <div class="chunks-header">
            <span>{{ currentDocument?.filename }}</span>
            <span class="chunks-total">{{ totalChunks }} {{ $t('knowledgebase.chunks') }}</span>
          </div>
          <div
            v-for="chunk in chunks"
            :key="chunk.chunk_id"
            class="chunk-item"
          >
            <div class="chunk-index">{{ chunk.index + 1 }}</div>
            <div class="chunk-content">{{ chunk.content }}</div>
          </div>
        </template>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { showDialog, showToast } from 'vant';

import DesktopSidebar from '../components/DesktopSidebar.vue';
import { useKnowledgeBaseStore } from '../store/knowledgeBase';
import { useUserStore } from '../store/user';
import { navigateBySidebarKey } from '../utils/sidebarNavigation';

const router = useRouter();
const userStore = useUserStore();
const knowledgeBaseStore = useKnowledgeBaseStore();
const activeKnowledgeBase = computed(() => knowledgeBaseStore.activeKnowledgeBase);

const fileInput = ref(null);
const selectedFiles = ref([]);
const uploading = ref(false);
const uploadProgressList = ref([]);
const uploadComplete = ref(false);
const successCount = ref(0);
const failedCount = ref(0);

const documents = ref([]);
const loadingDocuments = ref(false);
const showDetail = ref(false);
const showChunks = ref(false);
const currentDocument = ref(null);
const loadingDetail = ref(false);
const loadingChunks = ref(false);
const chunks = ref([]);
const totalChunks = ref(0);

const resolveToken = () => userStore.getToken;
const resolveKnowledgeBaseId = () => activeKnowledgeBase.value?.id || undefined;

const handleSidebarNavigate = (key) => {
  navigateBySidebarKey(router, key);
};

const goToAIChat = () => {
  router.push('/aichat');
};

const onClickLeft = () => {
  router.back();
};

const openFilePicker = () => {
  fileInput.value?.click();
};

const handleFileSelect = (event) => {
  const files = Array.from(event.target.files || []);
  selectedFiles.value = [...selectedFiles.value, ...files];
  event.target.value = '';
};

const handleDrop = (event) => {
  const files = Array.from(event.dataTransfer.files || []);
  selectedFiles.value = [...selectedFiles.value, ...files];
};

const removeFile = (index) => {
  selectedFiles.value.splice(index, 1);
};

const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const ensureAuthorized = async () => {
  userStore.syncFromStorage();

  if (!resolveToken()) {
    showToast('请先登录');
    router.push('/login');
    return false;
  }

  if (!userStore.userInfo) {
    const result = await userStore.getUserInfoDetail();
    if (!result.success) {
      showToast(result.message || '获取用户信息失败');
      return false;
    }
  }

  return true;
};

const uploadFiles = async () => {
  if (selectedFiles.value.length === 0) {
    showToast('请先选择文件');
    return;
  }

  const authorized = await ensureAuthorized();
  if (!authorized) return;

  const token = resolveToken();
  uploading.value = true;
  uploadComplete.value = false;
  uploadProgressList.value = [];
  successCount.value = 0;
  failedCount.value = 0;

  const formData = new FormData();
  if (resolveKnowledgeBaseId()) {
    formData.append('knowledge_base_id', resolveKnowledgeBaseId());
  }
  selectedFiles.value.forEach((file) => {
    formData.append('files', file);
    uploadProgressList.value.push({
      filename: file.name,
      percentage: 0,
      status: 'processing',
      message: '开始处理...',
    });
  });

  try {
    const response = await fetch('/knowledge/add/multiple/stream', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      let errorMessage = '上传失败';
      const contentType = response.headers.get('content-type') || '';

      if (contentType.includes('application/json')) {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } else {
        const errorText = await response.text();
        if (errorText.trim()) {
          errorMessage = errorText.trim();
        }
      }

      throw new Error(errorMessage);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('上传失败');
    }

    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop() || '';

      for (const event of events) {
        if (event.trim()) {
          parseEvent(event);
        }
      }
    }
  } catch (error) {
    console.error('Upload error:', error);
    const message = error instanceof Error && error.message ? error.message : '上传失败';
    showToast(message);
    uploadProgressList.value.forEach((item) => {
      if (item.status !== 'completed') {
        item.status = 'failed';
        item.message = message;
      }
    });
    failedCount.value = uploadProgressList.value.filter((item) => item.status === 'failed').length;
  } finally {
    uploading.value = false;
    uploadComplete.value = true;
    selectedFiles.value = [];
    await fetchDocuments();
  }
};

const parseEvent = (event) => {
  const lines = event.split('\n');
  let data = '';

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      data = line.slice(6);
    }
  }

  try {
    const eventData = JSON.parse(data);
    const {
      event_type,
      filename,
      message,
      progress,
      success_count,
      failed_count,
      error_message,
    } = eventData;

    if (filename) {
      const index = uploadProgressList.value.findIndex((item) => item.filename === filename);
      if (index !== -1) {
        uploadProgressList.value[index].message = error_message || message;

        if (event_type === 'completed') {
          uploadProgressList.value[index].status = 'completed';
          uploadProgressList.value[index].percentage = 100;
          successCount.value += 1;
        } else if (event_type === 'error') {
          uploadProgressList.value[index].status = 'failed';
          if (progress !== undefined) {
            uploadProgressList.value[index].percentage = progress;
          }
        } else {
          uploadProgressList.value[index].status = 'processing';
          if (progress !== undefined) {
            uploadProgressList.value[index].percentage = progress;
          }
        }
      }
    } else if (event_type === 'finish') {
      successCount.value = success_count;
      failedCount.value = failed_count;
    } else if (event_type === 'error') {
      showToast(error_message || message || '上传失败');
    }
  } catch (error) {
    console.error('Parse event error:', error);
  }
};

const fetchDocuments = async () => {
  const authorized = await ensureAuthorized();
  if (!authorized) return;

  loadingDocuments.value = true;

  try {
    const params = new URLSearchParams();
    if (resolveKnowledgeBaseId()) {
      params.set('knowledge_base_id', resolveKnowledgeBaseId());
    }

    const response = await fetch(`/knowledge/list${params.toString() ? `?${params.toString()}` : ''}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${resolveToken()}`,
        Accept: 'application/json',
      },
    });

    if (response.ok) {
      const result = await response.json();
      if (result.code === 200 && result.data) {
        documents.value = result.data.documents || [];
      }
    } else {
      console.error('Failed to fetch documents');
    }
  } catch (error) {
    console.error('Fetch documents error:', error);
  } finally {
    loadingDocuments.value = false;
  }
};

const fetchDocumentDetail = async (filename) => {
  loadingDetail.value = true;

  try {
    const params = new URLSearchParams({
      filename,
    });
    if (resolveKnowledgeBaseId()) {
      params.set('knowledge_base_id', resolveKnowledgeBaseId());
    }

    const response = await fetch(`/knowledge/detail?${params.toString()}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${resolveToken()}`,
        Accept: 'application/json',
      },
    });

    if (response.ok) {
      const result = await response.json();
      if (result.code === 200 && result.data) {
        return result.data;
      }
    }
  } catch (error) {
    console.error('Fetch document detail error:', error);
  } finally {
    loadingDetail.value = false;
  }

  return null;
};

const fetchDocumentChunks = async (filename) => {
  loadingChunks.value = true;
  chunks.value = [];
  totalChunks.value = 0;

  try {
    const params = new URLSearchParams({
      filename,
    });
    if (resolveKnowledgeBaseId()) {
      params.set('knowledge_base_id', resolveKnowledgeBaseId());
    }

    const response = await fetch(`/knowledge/chunks?${params.toString()}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${resolveToken()}`,
        Accept: 'application/json',
      },
    });

    if (response.ok) {
      const result = await response.json();
      if (result.code === 200 && result.data) {
        chunks.value = result.data.chunks || [];
        totalChunks.value = result.data.total_chunks || 0;
      }
    }
  } catch (error) {
    console.error('Fetch document chunks error:', error);
  } finally {
    loadingChunks.value = false;
  }
};

const deleteDocumentByFilename = async (filename) => {
  if (!filename) {
    return false;
  }

  try {
    const qs = new URLSearchParams({
      filename,
      delete_documents: 'true',
    });
    if (resolveKnowledgeBaseId()) {
      qs.set('knowledge_base_id', resolveKnowledgeBaseId());
    }

    const response = await fetch(`/knowledge/delete/filename?${qs.toString()}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${resolveToken()}`,
        Accept: 'application/json',
      },
    });

    if (response.ok) {
      const result = await response.json();
      return result.code === 200;
    }
  } catch (error) {
    console.error('Delete document error:', error);
  }

  return false;
};

const handleDeleteDocument = async (doc) => {
  showDialog({
    title: '确认',
    message: `确定删除文档“${doc.original_filename || doc.filename}”吗？`,
    showCancelButton: true,
  }).then(async (action) => {
    if (action === 'confirm') {
      const success = await deleteDocumentByFilename(doc.original_filename || doc.filename);
      if (success) {
        showToast('删除成功');
        await fetchDocuments();
      } else {
        showToast('删除失败');
      }
    }
  });
};

const cleanAllVectors = async () => {
  try {
    const params = new URLSearchParams();
    if (resolveKnowledgeBaseId()) {
      params.set('knowledge_base_id', resolveKnowledgeBaseId());
    }

    const response = await fetch(`/knowledge/clean${params.toString() ? `?${params.toString()}` : ''}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${resolveToken()}`,
        Accept: 'application/json',
      },
    });

    if (response.ok) {
      showToast('知识库已清空');
      await fetchDocuments();
    } else {
      showToast('清空失败');
    }
  } catch (error) {
    console.error('Clean vectors error:', error);
    showToast('清空失败');
  }
};

const handleCleanAll = () => {
  showDialog({
    title: '确认',
    message: '确定清空所有知识库文档吗？此操作不可恢复。',
    showCancelButton: true,
  }).then(async (action) => {
    if (action === 'confirm') {
      await cleanAllVectors();
    }
  });
};

const viewDocumentDetail = async (doc) => {
  currentDocument.value = doc;
  const detail = await fetchDocumentDetail(doc.filename);
  if (detail) {
    currentDocument.value = detail;
  }
  showDetail.value = true;
};

const viewDocumentChunks = async () => {
  if (!currentDocument.value?.filename) return;

  showDetail.value = false;
  showChunks.value = true;
  await fetchDocumentChunks(currentDocument.value.filename);
};

const getStatusClass = (status) => {
  if (status === 'completed') return 'status-success';
  if (status === 'failed') return 'status-failed';
  return 'status-processing';
};

const getStatusText = (status) => {
  if (status === 'completed') return '已完成';
  if (status === 'failed') return '失败';
  return '处理中';
};

watch(
  () => knowledgeBaseStore.activeKnowledgeBaseId,
  async () => {
    await fetchDocuments();
  }
);

onMounted(async () => {
  await knowledgeBaseStore.ensureKnowledgeBasesLoaded();
  await fetchDocuments();
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

.knowledgebase-content {
  padding: 26px 28px 30px;
}

.knowledge-overview {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
  padding: 22px;
  border-radius: 28px;
  background: linear-gradient(180deg, #fbfcff 0%, #f3f7ff 100%);
  border: 1px solid #e5ecf8;
  box-shadow: 0 18px 42px rgba(153, 171, 206, 0.12);
}

.overview-copy h2 {
  margin: 10px 0 8px;
  font-size: 24px;
  color: #1f2d48;
}

.overview-copy p {
  margin: 0;
  color: #6f7f9c;
  line-height: 1.7;
}

.active-base-badge {
  margin-top: 12px;
  display: inline-flex;
  align-items: center;
  padding: 8px 14px;
  border-radius: 999px;
  background: #ffffff;
  border: 1px solid #dbe5f5;
  color: #4d607d;
  font-size: 13px;
  font-weight: 600;
}

.overview-state {
  padding: 10px 14px;
  border-radius: 999px;
  background: #ffffff;
  color: #1f2d48;
  border: 1px solid #dbe5f5;
  white-space: nowrap;
  font-weight: 600;
}

.overview-state.busy {
  background: #eef3ff;
  color: #3558ff;
  border-color: #c9d8ff;
}

.upload-area {
  border: 1px dashed #cfdaf0;
  border-radius: 28px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  margin-bottom: 20px;
  background: #ffffff;
  box-shadow: 0 14px 38px rgba(145, 167, 207, 0.1);
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.upload-area:hover {
  border-color: #9fb7ea;
  box-shadow: 0 18px 42px rgba(145, 167, 207, 0.16);
}

.upload-area:active {
  transform: scale(0.995);
}

.upload-icon {
  color: var(--primary-color);
  margin-bottom: 12px;
}

.upload-text {
  font-size: 17px;
  font-weight: 700;
  margin: 0 0 8px;
  color: #1f2d48;
}

.upload-hint {
  font-size: 13px;
  color: #7b89a3;
  margin: 0;
  line-height: 1.6;
}

.file-input {
  display: none;
}

.file-list,
.upload-progress,
.document-list {
  margin-top: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  margin: 0 0 12px;
  color: #586883;
}

.file-list :deep(.van-cell-group),
.document-list :deep(.van-cell-group) {
  border-radius: 24px;
}

.file-list :deep(.van-cell),
.document-list :deep(.van-cell) {
  padding-top: 16px;
  padding-bottom: 16px;
}

.document-list :deep(.van-cell-group) {
  background: #ffffff;
  border: 1px solid #e5ecf8;
  box-shadow: 0 14px 32px rgba(145, 167, 207, 0.1);
}

.file-list :deep(.van-cell-group) {
  background: #ffffff;
  border: 1px solid #e5ecf8;
  box-shadow: 0 14px 32px rgba(145, 167, 207, 0.1);
}

.file-list :deep(.van-cell__title) {
  min-width: 0;
}

.file-list :deep(.van-cell__title span) {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #1f2d48;
  font-weight: 600;
}

.file-list :deep(.van-cell__value) {
  flex: none;
  margin-left: 16px;
  color: #7b89a3;
}

.file-list :deep(.van-icon-delete) {
  color: #e45b6f !important;
}

.document-list :deep(.van-cell__title) {
  min-width: 0;
}

.document-list :deep(.van-cell__title span) {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #1f2d48;
  font-weight: 600;
}

.document-list :deep(.van-cell__label) {
  margin-top: 6px;
}

.document-list :deep(.van-badge__wrapper),
.document-list :deep(.van-icon-file-text-o) {
  color: #5c76cb;
}

.document-list :deep(.van-cell::after) {
  border-color: #edf2fb;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.list-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.document-count,
.doc-meta,
.progress-message,
.detail-meta,
.chunks-total {
  font-size: 12px;
  color: #667899;
}

.delete-icon {
  cursor: pointer;
  padding: 8px;
}

.chunk-count {
  margin-right: 16px;
}

.doc-meta {
  color: #667899;
}

.document-list :deep(.van-button--danger.van-button--plain) {
  color: #d94b64;
  border-color: #f2c5ce;
  background: #fffafb;
}

.empty-state {
  text-align: center;
  padding: 48px 20px;
  color: #8a96aa;
  border-radius: 24px;
  background: #ffffff;
  border: 1px dashed #d8e2f3;
}

.empty-state p {
  margin: 12px 0 0;
}

.progress-item {
  margin-bottom: 16px;
  padding: 16px;
  border-radius: 22px;
  background: #ffffff;
  border: 1px solid #e2eaf7;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.progress-filename {
  font-size: 14px;
  color: #1f2d48;
}

.progress-status {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  font-weight: 600;
}

.status-processing {
  background: #eff4ff;
  color: #3558ff;
}

.status-success {
  background: #edf9f2;
  color: #17814b;
}

.status-failed {
  background: #fff1f3;
  color: #d83b5c;
}

.upload-result {
  text-align: center;
  padding: 24px;
  margin-top: 20px;
  border-radius: 24px;
  background: #ffffff;
  border: 1px solid #e2eaf7;
}

.upload-result p {
  margin: 8px 0 0;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 16px;
  background: #ffffff;
  border-bottom: 1px solid rgba(132, 171, 231, 0.12);
}

.detail-header h4 {
  margin: 0;
  font-size: 16px;
  color: #1f2d48;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-actions :deep(.van-button--primary.van-button--plain) {
  color: #3558ff;
  border-color: #c9d8ff;
  background: #f7faff;
}

.detail-header :deep(.van-icon-close) {
  color: #5f7090;
  font-size: 18px;
}

.detail-content {
  padding: 16px;
  overflow-y: auto;
  height: calc(100% - 64px);
  background: #ffffff;
}

.detail-content-full,
.chunk-content {
  font-size: 14px;
  line-height: 1.8;
  color: #41516d;
  white-space: pre-wrap;
  word-break: break-word;
}

.detail-content-full pre {
  margin: 0;
  padding: 0;
  font-family: inherit;
  font-size: inherit;
  white-space: pre-wrap;
  color: #41516d;
}

.chunks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(132, 171, 231, 0.12);
  color: #1f2d48;
  font-weight: 600;
}

.chunk-item {
  display: flex;
  margin-bottom: 16px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(77, 107, 254, 0.04);
  border: 1px solid rgba(140, 163, 212, 0.12);
}

.chunk-index {
  min-width: 30px;
  height: 30px;
  background: linear-gradient(135deg, #5f8198 0%, #4c6a7d 100%);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  margin-right: 12px;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.12);
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

  .knowledgebase-content {
    padding: 60px 12px 24px;
  }

  .knowledge-overview {
    flex-direction: column;
    padding: 18px;
  }

  .overview-copy h2 {
    font-size: 22px;
  }

  .list-header {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }
}
</style>
