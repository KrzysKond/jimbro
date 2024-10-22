#!/bin/sh

set -e
envsubst '$${LISTEN_PORT},$${APP_PORT},$${APP_HOST}' < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf

nginx -g 'daemon off;'