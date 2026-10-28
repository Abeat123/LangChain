# 阿里云部署与维护

本次部署目标：Ubuntu 22.04，公网 IP `101.37.229.182`。应用使用 Python 3.12，Nginx 提供前端静态文件和反向代理，systemd 管理 FastAPI、Gunicorn/Django，Redis 在本机提供共享缓存。

## 访问和端口

- 网站：`http://101.37.229.182/`。
- 阿里云安全组入方向需要允许 TCP 80，来源 `0.0.0.0/0`。
- FastAPI `127.0.0.1:8000`、Django `127.0.0.1:8001`、Redis `127.0.0.1:6379` 仅监听本机。
- 当前使用 IP 和 HTTP，尚未配置域名和 HTTPS。
- 服务端关闭了开发调试和 `test/666666` 临时登录。使用原有账号，或在网页注册账号。

## 服务器路径

| 内容 | 路径 |
| --- | --- |
| 应用代码 | `/opt/rag-service/app` |
| Python 虚拟环境 | `/opt/rag-service/.venv` |
| 前端静态文件 | `/var/www/rag-service` |
| Django 静态文件 | `/var/www/rag-static` |
| 上传图片 | `/var/www/rag-media` |
| FastAPI 会话数据库 | `/opt/rag-service/app/backend/data/chat_history.db` |
| 向量库 | `/opt/rag-service/app/backend/data/chromadb` |
| Django 用户数据库 | `/opt/rag-service/app/DjangoUserService/db.sqlite3` |
| 模型配置 | `/opt/rag-service/app/backend/.env` |
| 用户服务配置 | `/opt/rag-service/app/DjangoUserService/.env` |

两个 `.env` 的权限为 `600`，所有者为运行服务的 `ragapp`。服务器使用独立 JWT 密钥；FastAPI 的 `SECRET_KEY` 与 Django 的 `JWT_SECRET_KEY` 必须一致。模型密钥只保存在 `.env`，不写入此文档或前端构建文件。

## 状态、日志和重启

SSH 登录服务器后执行：

```bash
systemctl status rag-backend rag-users nginx redis-server --no-pager
journalctl -u rag-backend -u rag-users -n 100 --no-pager
curl -fsS http://127.0.0.1/health/ready
systemctl restart rag-backend rag-users
```

四个服务已启用开机自启。修改后端代码或模型配置后，重启相应后端服务。

修改前端时，在本地 `front/` 执行 `npm.cmd run build`，再将 `front/dist/` 的内容更新到服务器 `/var/www/rag-service/`。无需在服务器运行 Vite 或安装 Node.js。

## 备份

初始迁移包保存在 `/opt/rag-service/rag-release.tar.gz`，权限为 `600`。它包含部署时的源码、配置和数据快照，不能通过网站公开。

手动创建包含用户、知识库、会话、模型配置和上传图片的数据备份：

```bash
bash /opt/rag-service/app/deploy/backup.sh
```

备份脚本会短暂停止两个后端，确保向量文件和 SQLite 数据一致，完成后恢复服务。备份写入 `/opt/rag-service/backups/`；该目录应只由 root 读取。没有设置定时备份。

## 部署文件

- `bootstrap.sh`：安装系统组件、uv、Python 3.12 和运行依赖。先将项目文件放到 `/opt/rag-service/app`。
- `requirements-server.txt`、`constraints.txt`：服务器依赖及本地验证版本。
- `install-dependencies.sh`：安装或更新虚拟环境内依赖。
- `activate.sh`：配置目录、数据库、静态文件、systemd 和 Nginx。
- `rag-backend.service`、`rag-users.service`：后端服务定义。
- `nginx.conf`：静态页面、上传图片和 SSE 代理配置。

再次迁移数据时应先备份服务器数据，再在停服期间替换数据库和向量库。更新源码时保留服务器现有 `.env` 和业务数据。
