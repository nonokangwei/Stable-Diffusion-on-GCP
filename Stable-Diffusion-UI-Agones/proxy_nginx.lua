worker_processes  2;
error_log /var/log/nginx/error.log debug;

events {
    worker_connections 1024;
}

http {
    lua_package_path "/home/kangwe/nginx/lua-resty-redis-0.29/lib/?.lua;;";
    lua_package_cpath "/usr/local/lib/lua/5.1/?.so;;";

    server {
        listen 8080;

        location / {
            resolver 8.8.4.4;  # use Google's open DNS server

            set $target '';
            access_by_lua '
                --local key = ngx.var.remote_addr
                
                --for k, v in pairs(headers) do
                --    print(k, ": ", v)
                --end
                local headers = ngx.req.get_headers()
                local key = headers["x-goog-authenticated-user-email"]
                print(key)
                
                if not key then
                    ngx.log(ngx.ERR, "no remote-address found")
                    return ngx.exit(400)
                end

                local redis = require "resty.redis"
                local red = redis:new()

                red:set_timeout(1000) -- 1 second

                local ok, err = red:connect("10.177.146.60", 6379)
                if not ok then
                    ngx.log(ngx.ERR, "failed to connect to redis: ", err)
                    return ngx.exit(500)
                end

                local lookup_res, err = red:get(key)
                print(lookup_res)
                if lookup_res == ngx.null then                
                    local http = require "resty.http"
                    local httpc = http.new()
                    local res, err = httpc:request_uri(
                        "http://34.70.113.80:443/gameserverallocation",
                            {
                            method = "POST",
                            body = [[{"namespace": "default"}]],
                          }
                    )
                    -- print(res.body)
                
                    local cjson = require "cjson"
                    local resp_data = cjson.decode(res.body)
                    local host = resp_data["address"]
                    local port = resp_data["ports"][2]["port"]
                    -- print(host, ": ", port)

                    -- ngx.var.target = "34.172.255.13:7812"
                    ngx.var.target = host .. ":" .. port
                    print("set redis ", ngx.var.target)
                    ok, err = red:set(key, ngx.var.target)
                    if not ok then
                       print("fail to set redis key")
                       ngx.say("failed to set dog: ", err)
                       return
                    end
                else
                    ngx.var.target = lookup_res
                end
            ';

            proxy_pass http://$target;
        }
    }
}