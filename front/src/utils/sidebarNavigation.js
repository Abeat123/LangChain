export const navigateBySidebarKey = (router, key) => {
  const routeMap = {
    aichat: '/aichat',
    sessions: '/sessions',
    knowledgebase: '/knowledgebase',
    'retrieval-insights': '/retrieval-insights',
    'knowledge-spaces': '/knowledge-spaces',
    feedback: '/feedback',
    my: '/my',
  };

  const target = routeMap[key];
  if (!target) {
    return false;
  }

  router.push(target);
  return true;
};
