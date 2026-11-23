import { defineStore } from 'pinia';
import axios from 'axios';

const pickFallbackBaseId = (knowledgeBases = []) => {
  return knowledgeBases.find((item) => item.is_default)?.id || knowledgeBases[0]?.id || '';
};

export const useKnowledgeBaseStore = defineStore('knowledge-base', {
  state: () => ({
    knowledgeBases: [],
    activeKnowledgeBaseId: '',
    loading: false,
  }),

  getters: {
    activeKnowledgeBase: (state) => {
      return state.knowledgeBases.find((item) => item.id === state.activeKnowledgeBaseId) || null;
    },
  },

  actions: {
    getToken() {
      return localStorage.getItem('jwt_token') || '';
    },

    async loadKnowledgeBases() {
      const token = this.getToken();
      if (!token) {
        this.knowledgeBases = [];
        this.activeKnowledgeBaseId = '';
        return {
          success: false,
          message: '未登录',
        };
      }

      this.loading = true;
      try {
        const response = await axios.get('/knowledge/bases', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const list = response.data?.data?.knowledge_bases || [];
        this.knowledgeBases = list;

        const hasActive = list.some((item) => item.id === this.activeKnowledgeBaseId);
        if (!hasActive) {
          this.activeKnowledgeBaseId = pickFallbackBaseId(list);
        }

        return {
          success: true,
          data: list,
        };
      } catch (error) {
        console.error('加载知识库列表失败:', error);
        return {
          success: false,
          message: error.response?.data?.detail || error.response?.data?.message || '加载知识库列表失败',
        };
      } finally {
        this.loading = false;
      }
    },

    async ensureKnowledgeBasesLoaded() {
      return this.loadKnowledgeBases();
    },

    setActiveKnowledgeBase(baseId) {
      this.activeKnowledgeBaseId = baseId || pickFallbackBaseId(this.knowledgeBases);
    },

    async createKnowledgeBase(payload) {
      const token = this.getToken();
      const response = await axios.post('/knowledge/bases', payload, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const created = response.data?.data;
      await this.loadKnowledgeBases();
      if (created?.id) {
        this.activeKnowledgeBaseId = created.id;
      }
      return created;
    },

    async updateKnowledgeBase(baseId, payload) {
      const token = this.getToken();
      const response = await axios.patch(`/knowledge/bases/${baseId}`, payload, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      await this.loadKnowledgeBases();
      return response.data?.data;
    },

    async deleteKnowledgeBase(baseId) {
      const token = this.getToken();
      await axios.delete(`/knowledge/bases/${baseId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      await this.loadKnowledgeBases();
      if (this.activeKnowledgeBaseId === baseId) {
        this.activeKnowledgeBaseId = pickFallbackBaseId(this.knowledgeBases);
      }
    },
  },

  persist: {
    enabled: true,
    strategies: [
      {
        key: 'knowledge-base-store',
        storage: localStorage,
      },
    ],
  },
});
