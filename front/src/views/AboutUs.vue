<template>
  <div class="aboutus-container">
    <van-nav-bar :title="$t('settings.aboutUs')" left-arrow @click-left="onClickLeft" fixed />

    <div class="aboutus-content">
      <section class="about-hero">
        <h2>深蓝知识问答工作台</h2>
        <p>
          基于 LangChain、FastAPI、Django 与 Vue 3 构建，为智能问答、企业知识库和长会话工作流提供开箱即用的能力。
        </p>
      </section>

      <van-cell-group inset class="info-group">
        <van-cell
          class="contact-cell"
          title="官方 GitHub"
          is-link
          @click="openLink('https://github.com/RMA-MUN/LangChain-RAG-FastAPI-Service')"
        >
          <template #icon>
            <div class="contact-icon github-icon">
              <svg viewBox="0 0 24 24" width="16" height="16">
                <path
                  fill="currentColor"
                  d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"
                />
              </svg>
            </div>
          </template>
          <template #label>
            <span class="link-text">github.com/RMA-MUN/LangChain-RAG-FastAPI-Service</span>
          </template>
        </van-cell>
        <van-cell class="contact-cell" title="作者邮箱" value="n3032747608@163.com">
          <template #icon>
            <div class="contact-icon email-icon">
              <van-icon name="envelop-o" size="14" />
            </div>
          </template>
        </van-cell>
        <van-cell class="contact-cell" title="作者 QQ" value="3032747608">
          <template #icon>
            <div class="contact-icon qq-icon">Q</div>
          </template>
        </van-cell>
      </van-cell-group>

      <section class="info-panel">
        <h3>技术栈</h3>
        <p>LangChain · FastAPI · Django · Vue 3 · ChromaDB · DashScope</p>
      </section>

      <section class="feature-grid">
        <article class="feature-card">
          <h4>知识库管理</h4>
          <p>支持文档上传、自动切片与语义检索，让 RAG 数据准备更顺手。</p>
        </article>
        <article class="feature-card">
          <h4>会话记忆</h4>
          <p>数据库持久化上下文，适合连续追问、复盘与长期协作场景。</p>
        </article>
        <article class="feature-card">
          <h4>全链路检索</h4>
          <p>BM25 与向量混合召回，再结合百炼在线重排序，提升答案相关性。</p>
        </article>
        <article class="feature-card">
          <h4>深蓝主题界面</h4>
          <p>移动端优先设计，保持信息层次、沉浸感和可读性之间的平衡。</p>
        </article>
      </section>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

const onClickLeft = () => {
  router.back();
};

const openLink = (url) => {
  window.open(url, '_blank');
};
</script>

<style scoped>
.aboutus-container {
  min-height: 100vh;
  padding-top: 46px;
  padding-bottom: 24px;
}

.aboutus-content {
  padding: 18px 16px;
}

.about-hero {
  padding: 24px 22px;
  margin-bottom: 18px;
  border-radius: 28px;
  background: linear-gradient(180deg, #fbfcff 0%, #f3f7ff 100%);
  border: 1px solid #e5ecf8;
  box-shadow: 0 18px 48px rgba(130, 154, 204, 0.12);
}

.about-hero h2 {
  margin: 12px 0 10px;
  font-size: 26px;
  color: #1f2d48;
}

.about-hero p {
  margin: 0;
  color: #566784;
  line-height: 1.7;
}

.info-group {
  margin-bottom: 18px;
}

.link-text {
  font-size: 12px;
  color: var(--primary-strong);
}

.contact-icon {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
}

.github-icon {
  background: #edf3ff;
  color: #315ecf;
}

.email-icon {
  background: #edf3ff;
  color: #315ecf;
}

.qq-icon {
  background: #edf3ff;
  color: #315ecf;
  font-weight: 700;
}

.contact-cell {
  border-radius: 18px;
}

.info-panel {
  padding: 22px;
  margin-bottom: 18px;
  border-radius: 24px;
  background: linear-gradient(180deg, #ffffff 0%, #f7faff 100%);
  border: 1px solid #e5ecf8;
  box-shadow: 0 14px 38px rgba(130, 154, 204, 0.12);
}

.info-panel h3 {
  margin: 0 0 10px;
  font-size: 16px;
  color: #1f2d48;
}

.info-panel p {
  margin: 0;
  color: #566784;
  line-height: 1.7;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.feature-card {
  padding: 18px;
  border-radius: 22px;
  background: linear-gradient(180deg, #ffffff 0%, #f7faff 100%);
  border: 1px solid #e5ecf8;
  box-shadow: 0 14px 38px rgba(130, 154, 204, 0.12);
}

.feature-card h4 {
  margin: 0 0 10px;
  color: #1f2d48;
  font-size: 16px;
}

.feature-card p {
  margin: 0;
  color: #5f7090;
  line-height: 1.7;
}

@media (max-width: 640px) {
  .aboutus-content {
    padding: 14px 12px;
  }

  .about-hero {
    padding: 20px 18px;
  }

  .about-hero h2 {
    font-size: 24px;
  }

  .feature-grid {
    grid-template-columns: 1fr;
  }
}
</style>
