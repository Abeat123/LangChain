import { defineStore } from 'pinia';
import axios from 'axios';
import { apiConfig } from '../config/api';

const getCsrfToken = () => {
  if (typeof document === 'undefined') {
    return '';
  }

  const cookieValue = document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrftoken='))
    ?.split('=')[1];

  return cookieValue || '';
};

const getStoredToken = () => {
  if (typeof window === 'undefined') {
    return '';
  }

  return localStorage.getItem('jwt_token') || '';
};

const persistToken = (token) => {
  if (typeof window === 'undefined') {
    return;
  }

  if (token) {
    localStorage.setItem('jwt_token', token);
  } else {
    localStorage.removeItem('jwt_token');
  }
};

const flattenMessages = (input) => {
  if (!input) {
    return [];
  }

  if (typeof input === 'string') {
    return input.trim() ? [input.trim()] : [];
  }

  if (Array.isArray(input)) {
    return input.flatMap((item) => flattenMessages(item));
  }

  if (typeof input === 'object') {
    return Object.values(input).flatMap((item) => flattenMessages(item));
  }

  return [String(input)];
};

const pickMessage = (fallback, ...candidates) => {
  for (const candidate of candidates) {
    const messages = flattenMessages(candidate);
    if (messages.length > 0) {
      return messages.join('；');
    }
  }

  return fallback;
};

const TEST_USER = {
  username: 'test',
  password: '666666',
  token: 'test_token_for_unlogin',
  user: {
    id: 1,
    username: 'test',
    email: 'test@example.com',
    bio: '测试用户',
  },
};

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: null,
    token: getStoredToken(),
    isLogin: Boolean(getStoredToken()),
    userBio: '这个用户还没有填写简介',
  }),

  getters: {
    getUserInfo: (state) => state.userInfo,
    getToken: (state) => state.token || getStoredToken(),
    getLoginStatus: (state) => Boolean(state.isLogin || state.token || getStoredToken()),
    getUserBio: (state) => state.userInfo?.bio || state.userBio,
  },

  actions: {
    applyAuth(token, userInfo = this.userInfo) {
      this.token = token || '';
      this.isLogin = Boolean(token);
      this.userInfo = userInfo;
      persistToken(this.token);
    },

    clearAuth() {
      this.userInfo = null;
      this.token = '';
      this.isLogin = false;
      persistToken('');
    },

    syncFromStorage() {
      const token = getStoredToken();
      this.token = token;
      this.isLogin = Boolean(token);
    },

    async login(userData) {
      try {
        if (
          userData.username === TEST_USER.username &&
          userData.password === TEST_USER.password
        ) {
          this.applyAuth(TEST_USER.token, TEST_USER.user);
          return {
            success: true,
            message: '测试用户登录成功',
          };
        }

        const response = await axios.post(
          apiConfig.endpoints.login,
          {
            username: userData.username,
            password: userData.password,
          },
          {
            headers: {
              'X-CSRFTOKEN': getCsrfToken(),
            },
          }
        );

        if (response.status === 200 && response.data?.token) {
          const nextUserInfo = response.data.user || response.data.data || null;
          this.applyAuth(response.data.token, nextUserInfo);

          return {
            success: true,
            message: pickMessage('登录成功', response.data?.message),
          };
        }

        return {
          success: false,
          message: pickMessage('登录失败', response.data?.detail, response.data?.message),
        };
      } catch (error) {
        console.error('登录请求失败:', error);
        return {
          success: false,
          message: pickMessage(
            '登录请求失败，请稍后再试',
            error.response?.data?.detail?.non_field_errors,
            error.response?.data?.detail,
            error.response?.data?.message
          ),
        };
      }
    },

    async logout() {
      const token = this.getToken;

      try {
        if (token) {
          await axios.post(
            apiConfig.endpoints.logout,
            {},
            {
              headers: {
                Authorization: `Bearer ${token}`,
                'X-CSRFTOKEN': getCsrfToken(),
              },
            }
          );
        }
      } catch (error) {
        console.error('注销请求失败:', error);
      } finally {
        this.clearAuth();
      }
    },

    async getUserInfoDetail() {
      const token = this.getToken;

      if (!token) {
        this.clearAuth();
        return {
          success: false,
          message: '未登录',
        };
      }

      try {
        const response = await axios.get(apiConfig.endpoints.profile, {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-CSRFTOKEN': getCsrfToken(),
          },
        });

        if (response.status === 200) {
          const nextUserInfo = response.data?.data || response.data?.user || response.data;
          this.applyAuth(token, nextUserInfo);

          return {
            success: true,
            message: pickMessage('获取用户信息成功', response.data?.message),
            data: nextUserInfo,
          };
        }

        return {
          success: false,
          message: pickMessage('获取用户信息失败', response.data?.detail, response.data?.message),
        };
      } catch (error) {
        console.error('获取用户信息请求失败:', error);

        if ([401, 403].includes(error.response?.status)) {
          this.clearAuth();
        }

        return {
          success: false,
          message: pickMessage(
            '获取用户信息请求失败，请稍后再试',
            error.response?.data?.detail,
            error.response?.data?.message
          ),
        };
      }
    },

    async updateUserInfo(userData) {
      const token = this.getToken;

      if (!token) {
        this.clearAuth();
        return {
          success: false,
          message: '未登录',
        };
      }

      try {
        const response = await axios.put('/user/update/', userData, {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-CSRFTOKEN': getCsrfToken(),
            'Content-Type': 'application/json',
          },
        });

        if (response.status === 200) {
          const nextUserInfo =
            response.data?.user ||
            response.data?.data ||
            {
              ...(this.userInfo || {}),
              ...userData,
            };
          const nextToken = response.data?.token || token;

          this.applyAuth(nextToken, nextUserInfo);

          return {
            success: true,
            message: pickMessage('用户信息更新成功', response.data?.message),
          };
        }

        return {
          success: false,
          message: pickMessage('更新用户信息失败', response.data?.detail, response.data?.message),
        };
      } catch (error) {
        console.error('更新用户信息请求失败:', error);

        return {
          success: false,
          message: pickMessage(
            '更新用户信息请求失败，请稍后再试',
            error.response?.data?.message,
            error.response?.data?.detail
          ),
        };
      }
    },

    async updatePassword(oldPassword, newPassword) {
      const token = this.getToken;

      if (!token) {
        this.clearAuth();
        return {
          success: false,
          message: '未登录',
        };
      }

      try {
        const response = await axios.post(
          '/user/change_password/',
          {
            old_password: oldPassword,
            new_password: newPassword,
          },
          {
            headers: {
              Authorization: `Bearer ${token}`,
              'X-CSRFTOKEN': getCsrfToken(),
              'Content-Type': 'application/json',
            },
          }
        );

        if (response.status === 200) {
          const nextToken = response.data?.token || token;
          this.applyAuth(nextToken, this.userInfo);

          return {
            success: true,
            message: pickMessage('密码修改成功', response.data?.message),
          };
        }

        return {
          success: false,
          message: pickMessage('更新密码失败', response.data?.detail, response.data?.message),
        };
      } catch (error) {
        console.error('更新密码请求失败:', error);
        return {
          success: false,
          message: pickMessage(
            '更新密码请求失败，请稍后再试',
            error.response?.data?.detail,
            error.response?.data?.message
          ),
        };
      }
    },

    async register(userData) {
      try {
        const response = await axios.post(
          apiConfig.endpoints.register,
          {
            username: userData.username,
            email: userData.email,
            telephone: userData.telephone || '',
            password: userData.password,
            confirm_password: userData.confirm_password,
          },
          {
            headers: {
              'X-CSRFTOKEN': getCsrfToken(),
              'Content-Type': 'application/json',
            },
          }
        );

        if (response.data?.status === 201 && response.data?.token) {
          this.applyAuth(response.data.token, response.data.user || null);

          return {
            success: true,
            message: pickMessage('注册成功', response.data?.message),
          };
        }

        return {
          success: false,
          message: pickMessage('注册失败', response.data?.detail, response.data?.message),
        };
      } catch (error) {
        console.error('注册请求异常:', error);

        return {
          success: false,
          message: pickMessage(
            '注册失败，请稍后重试',
            error.response?.data?.detail,
            error.response?.data?.message
          ),
        };
      }
    },
  },

  persist: {
    enabled: true,
    strategies: [
      {
        key: 'user-store',
        storage: localStorage,
      },
    ],
  },
});
