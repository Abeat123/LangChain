import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  {
    path: '/',
    redirect: '/aichat',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: {
      title: '登录',
      keepAlive: false,
    },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: {
      title: '注册',
      keepAlive: false,
    },
  },
  {
    path: '/aichat',
    name: 'AIChat',
    component: () => import('../views/AIChat.vue'),
    meta: {
      title: 'AI 问答',
      keepAlive: true,
    },
  },
  {
    path: '/aichat/:sessionId',
    name: 'AIChatWithSession',
    component: () => import('../views/AIChat.vue'),
    meta: {
      title: 'AI 问答',
      keepAlive: true,
    },
  },
  {
    path: '/my',
    name: 'My',
    component: () => import('../views/My.vue'),
    meta: {
      title: '我的',
      keepAlive: true,
    },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: {
      title: '我的详情',
      keepAlive: false,
    },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue'),
    meta: {
      title: '设置',
      keepAlive: false,
    },
  },
  {
    path: '/aboutus',
    name: 'AboutUs',
    component: () => import('../views/AboutUs.vue'),
    meta: {
      title: '关于我们',
      keepAlive: false,
    },
  },
  {
    path: '/knowledgebase',
    name: 'KnowledgeBase',
    component: () => import('../views/KnowledgeBase.vue'),
    meta: {
      title: '知识库管理',
      keepAlive: false,
    },
  },
  {
    path: '/retrieval-insights',
    name: 'RetrievalInsights',
    component: () => import('../views/RetrievalInsights.vue'),
    meta: {
      title: '检索可视化',
      keepAlive: false,
    },
  },
  {
    path: '/knowledge-spaces',
    name: 'KnowledgeSpaces',
    component: () => import('../views/KnowledgeSpaces.vue'),
    meta: {
      title: '多知识库切换',
      keepAlive: false,
    },
  },
  {
    path: '/feedback',
    name: 'FeedbackHub',
    component: () => import('../views/FeedbackHub.vue'),
    meta: {
      title: '回答反馈',
      keepAlive: false,
    },
  },
  {
    path: '/sessions',
    name: 'Sessions',
    component: () => import('../views/Sessions.vue'),
    meta: {
      title: '会话管理',
      keepAlive: true,
    },
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || '知识问答';
  next();
});

export default router;
