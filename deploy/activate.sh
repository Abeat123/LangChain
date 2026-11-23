#!/usr/bin/env bash
set -euo pipefail
app=/opt/rag-service/app
python=/opt/rag-service/.venv/bin/python
id ragapp >/dev/null 2>&1
install -d -m 755 /var/www/rag-service /var/www/rag-static
install -d -o ragapp -g www-data -m 2750 /var/www/rag-media
cp -a "$app/front/dist/." /var/www/rag-service/
if [ -d "$app/DjangoUserService/media" ]; then
    cp -a "$app/DjangoUserService/media/." /var/www/rag-media/
fi
chown -R root:www-data /var/www/rag-service /var/www/rag-static
chown -R ragapp:www-data /var/www/rag-media
chmod -R g+rX /var/www/rag-service /var/www/rag-media
chown -R ragapp:ragapp /opt/rag-service/app
find "$app" -type d -exec chmod 750 {} +
find "$app" -type f -exec chmod 640 {} +
chmod 600 "$app/backend/.env" "$app/DjangoUserService/.env"
chmod 755 /opt/rag-service /opt/rag-service/app
cd "$app/DjangoUserService"
runuser -u ragapp -- "$python" manage.py check
runuser -u ragapp -- "$python" manage.py migrate --noinput
runuser -u ragapp -- "$python" manage.py collectstatic --noinput
cp -a staticfiles/. /var/www/rag-static/
chown -R root:www-data /var/www/rag-static
chmod -R g+rX /var/www/rag-static
install -m 644 "$app/deploy/rag-backend.service" /etc/systemd/system/rag-backend.service
install -m 644 "$app/deploy/rag-users.service" /etc/systemd/system/rag-users.service
if [ -e /etc/nginx/sites-enabled/default ]; then
    mv /etc/nginx/sites-enabled/default /etc/nginx/sites-available/default.disabled-by-rag
fi
install -m 644 "$app/deploy/nginx.conf" /etc/nginx/sites-available/rag-service
ln -sfn /etc/nginx/sites-available/rag-service /etc/nginx/sites-enabled/rag-service
nginx -t
systemctl daemon-reload
systemctl enable --now rag-users rag-backend nginx redis-server
systemctl restart rag-users rag-backend
systemctl reload nginx
echo ACTIVATION_OK
