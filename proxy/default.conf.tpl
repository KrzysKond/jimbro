
map $http_upgrade $connection_upgrade {
  default upgrade;
    '' close;
}


server {
    listen ${LISTEN_PORT};

    location /static {
        alias /vol/static;
    }

    location / {
        proxy_pass  http://${APP_HOST}:${APP_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;

    }
}