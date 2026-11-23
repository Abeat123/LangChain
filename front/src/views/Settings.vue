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
      <van-nav-bar
        :title="$t('settings.title')"
        left-arrow
        fixed
        class="mobile-nav"
        @click-left="onClickLeft"
      />

      <div class="settings-page">
        <section class="settings-shell">
          <div class="settings-header">
            <div>
              <h1>{{ $t('settings.title') }}</h1>
              <p>统一管理当前界面的主题和语言设置。</p>
            </div>
          </div>

          <section class="settings-block">
            <div class="section-title">{{ $t('settings.personalization') }}</div>
            <van-cell-group inset>
              <van-cell
                :title="$t('settings.themeCustomization')"
                :value="activeThemeName"
                is-link
                @click="showThemePopup = true"
              />
              <van-cell
                :title="$t('settings.languageSettings')"
                :value="activeLanguageLabel"
                is-link
                @click="showLanguagePopup = true"
              />
            </van-cell-group>
          </section>
        </section>
      </div>
    </main>

    <van-popup
      v-model:show="showThemePopup"
      position="bottom"
      round
      class="settings-popup"
    >
      <div class="popup-body">
        <div class="popup-title">{{ $t('settings.selectTheme') }}</div>
        <div class="theme-list">
          <button
            v-for="theme in themeList"
            :key="theme.id"
            type="button"
            class="theme-item"
            :class="{ active: currentTheme === theme.id }"
            @click="changeTheme(theme.id)"
          >
            <span class="theme-color" :style="{ backgroundColor: theme.primaryColor }"></span>
            <span class="theme-name">{{ theme.name }}</span>
          </button>
        </div>
      </div>
    </van-popup>

    <van-popup
      v-model:show="showLanguagePopup"
      position="bottom"
      round
      class="settings-popup"
    >
      <div class="popup-body">
        <div class="popup-title">{{ $t('settings.selectLanguage') }}</div>
        <van-radio-group v-model="currentLanguage">
          <van-cell-group inset>
            <van-cell
              v-for="lang in languageOptions"
              :key="lang.value"
              :title="lang.label"
              clickable
              :class="{ 'language-active': currentLanguage === lang.value }"
              @click="currentLanguage = lang.value"
            >
              <template #right-icon>
                <van-radio :name="lang.value" />
              </template>
            </van-cell>
          </van-cell-group>
        </van-radio-group>
        <div class="popup-footer">
          <van-button type="primary" block @click="changeLanguage">
            {{ $t('common.confirm') }}
          </van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { showToast } from 'vant';
import { useI18n } from 'vue-i18n';

import DesktopSidebar from '../components/DesktopSidebar.vue';
import { useLanguageStore } from '../store/language';
import { useThemeStore } from '../store/theme';
import { navigateBySidebarKey } from '../utils/sidebarNavigation';

const router = useRouter();
const themeStore = useThemeStore();
const languageStore = useLanguageStore();
const { t, locale } = useI18n();

const showThemePopup = ref(false);
const showLanguagePopup = ref(false);

const themeList = computed(() => themeStore.getAllThemes);
const currentTheme = computed(() => themeStore.getCurrentTheme);
const activeThemeName = computed(() => {
  return themeList.value.find((item) => item.id === currentTheme.value)?.name || 'Sky';
});

const languageOptions = [
  { label: '简体中文', value: 'zh-CN' },
  { label: 'English', value: 'en-US' },
];

const currentLanguage = ref(languageStore.getCurrentLanguage);
const activeLanguageLabel = computed(() => {
  return languageOptions.find((item) => item.value === currentLanguage.value)?.label || '简体中文';
});

const onClickLeft = () => {
  router.back();
};

const handleSidebarNavigate = (key) => {
  navigateBySidebarKey(router, key);
};

const goToAIChat = () => {
  router.push('/aichat');
};

const changeTheme = (themeId) => {
  themeStore.setTheme(themeId);
  showToast(t('settings.themeChanged'));
  showThemePopup.value = false;
};

const changeLanguage = () => {
  languageStore.setLanguage(currentLanguage.value);
  locale.value = currentLanguage.value;
  showLanguagePopup.value = false;
  showToast(t('settings.languageChanged'));
  window.location.reload();
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
  background: #ffffff;
}

.settings-page {
  padding: 28px 32px 36px;
}

.settings-shell {
  width: min(100%, 760px);
}

.settings-header {
  margin-bottom: 18px;
}

.settings-header h1 {
  margin: 0 0 8px;
  font-size: 30px;
  color: #1f2d48;
}

.settings-header p {
  margin: 0;
  color: #6f7f9c;
  line-height: 1.7;
}

.settings-block {
  padding: 22px;
  border: 1px solid #e5ecf8;
  border-radius: 28px;
  background: linear-gradient(180deg, #fbfcff 0%, #f3f7ff 100%);
  box-shadow: 0 18px 42px rgba(153, 171, 206, 0.12);
}

.section-title {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 700;
  color: #586883;
}

.settings-block :deep(.van-cell-group) {
  border-radius: 22px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.96);
}

.settings-block :deep(.van-cell) {
  padding-top: 16px;
  padding-bottom: 16px;
  --van-cell-text-color: #20314f;
  --van-cell-value-color: #627392;
  --van-cell-label-color: #627392;
}

.settings-block :deep(.van-cell__title),
.settings-block :deep(.van-cell__title span) {
  color: #20314f;
  font-weight: 600;
}

.settings-block :deep(.van-cell__value) {
  color: #627392;
}

.settings-block :deep(.van-cell__right-icon) {
  color: #7c8baa;
}

.settings-popup {
  max-width: 760px;
  margin: 0 auto;
}

.popup-body {
  padding: 24px 20px calc(20px + env(safe-area-inset-bottom));
}

.popup-title {
  margin-bottom: 18px;
  text-align: center;
  font-size: 22px;
  font-weight: 700;
  color: #1f2d48;
}

.theme-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.theme-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  border: 1px solid #d9e4f7;
  border-radius: 18px;
  background: #ffffff;
  color: #1f2d48;
  text-align: left;
}

.theme-item.active {
  border-color: #bfd2ff;
  background: #eef4ff;
  box-shadow: 0 10px 24px rgba(77, 107, 254, 0.12);
}

.theme-color {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  flex-shrink: 0;
}

.theme-name {
  color: #41516d;
  font-weight: 600;
}

.popup-body :deep(.van-cell-group) {
  border-radius: 20px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.96);
}

.popup-body :deep(.van-cell) {
  --van-cell-text-color: #20314f;
  --van-cell-value-color: #627392;
}

.popup-body :deep(.van-cell__title),
.popup-body :deep(.van-cell__title span) {
  color: #20314f;
  font-weight: 600;
}

.popup-body :deep(.van-radio__label) {
  color: #20314f;
}

.popup-body :deep(.van-cell__right-icon) {
  color: #7c8baa;
}

.popup-footer {
  margin-top: 18px;
}

.language-active {
  background: #eef4ff;
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

  .settings-page {
    padding: 60px 12px 24px;
  }

  .settings-shell {
    width: 100%;
  }

  .settings-header h1 {
    font-size: 24px;
  }

  .settings-block {
    padding: 20px;
  }

  .theme-list {
    grid-template-columns: 1fr;
  }
}
</style>
