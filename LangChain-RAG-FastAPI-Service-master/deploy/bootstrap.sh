#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y nginx redis-server libmagic1 poppler-utils ca-certificates curl python3-pip
python3 -m pip install --disable-pip-version-check uv -i https://pypi.tuna.tsinghua.edu.cn/simple
export UV_PYTHON_INSTALL_DIR=/opt/rag-python
export UV_HTTP_TIMEOUT=120
uv python install 3.12
uv venv --python 3.12 /opt/rag-service/.venv
uv pip install --python /opt/rag-service/.venv/bin/python \
  -r /opt/rag-service/app/deploy/requirements-server.txt \
  -i https://pypi.tuna.tsinghua.edu.cn/simple
id ragapp >/dev/null 2>&1 || useradd --system --home-dir /opt/rag-service --shell /usr/sbin/nologin ragapp
systemctl enable --now redis-server
echo BOOTSTRAP_OK
