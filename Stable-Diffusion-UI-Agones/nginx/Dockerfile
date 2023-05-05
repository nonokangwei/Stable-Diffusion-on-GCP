FROM openresty/openresty:1.21.4.1-0-focal

RUN opm get ledgetech/lua-resty-http
RUN opm get openresty/lua-resty-redis
RUN opm get openresty/lua-resty-dns

COPY nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY default.conf /etc/nginx/conf.d/default.conf
COPY sd.lua /usr/local/openresty/nginx/sd.lua
COPY coffee-clock.jpg  /usr/local/openresty/nginx/html/images/coffee-clock.jpg