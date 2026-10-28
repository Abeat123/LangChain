# 基于 LangChain 的 RAG 知识库智能问答系统

项目包含 Vue 3 前端、FastAPI 知识库问答服务和 Django 用户服务，支持文档入库、多个知识库、混合检索、Agent 交互、会话管理和回答反馈，并提供 Windows 本地启动与 Ubuntu / 阿里云部署脚本。

**完整项目说明：[查看 README](LangChain-RAG-FastAPI-Service-master/README.md)**

本工作区的代码位于同名子目录。安装依赖、填写配置或启动服务前，先进入包含 `run.ps1` 的目录：

```powershell
cd .\LangChain-RAG-FastAPI-Service-master
```

完成完整说明中的环境配置后启动：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1
```

本地前端地址为 http://127.0.0.1:3000。

- [安装、模型配置与使用流程](LangChain-RAG-FastAPI-Service-master/README.md#本地快速启动)
- [Ubuntu 与阿里云部署](LangChain-RAG-FastAPI-Service-master/README.md#ubuntu-与阿里云部署)
- [服务器维护与备份](LangChain-RAG-FastAPI-Service-master/deploy/README.md)
