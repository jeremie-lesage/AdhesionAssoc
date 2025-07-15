#!/bin/sh
echo "window.BACKEND_URL = \"${BACKEND_URL}\"" > /usr/share/nginx/html/config.js
exec nginx -g "daemon off;"
