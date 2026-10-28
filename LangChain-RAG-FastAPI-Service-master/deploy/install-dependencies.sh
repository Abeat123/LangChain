#!/usr/bin/env bash
set -euo pipefail
export UV_HTTP_TIMEOUT=120
export UV_CONCURRENT_DOWNLOADS=4
export UV_CONCURRENT_INSTALLS=2
uv pip install --python /opt/rag-service/.venv/bin/python \
  -r /opt/rag-service/app/deploy/requirements-server.txt \
  -i https://pypi.tuna.tsinghua.edu.cn/simple
id ragapp >/dev/null 2>&1 || useradd --system --home-dir /opt/rag-service --shell /usr/sbin/nologin ragapp
echo DEPENDENCIES_OK
