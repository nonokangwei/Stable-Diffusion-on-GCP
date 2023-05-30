local headers = ngx.req.get_headers()
local key = headers["x-goog-authenticated-user-email"]
-- print(key)

if not key then
    if headers["user-agent"] == "GoogleHC/1.0" then
        ngx.log(ngx.INFO, "health check success!")
        ngx.say("health check success!")
        return ngx.exit(200)
    end
    ngx.log(ngx.ERR, "no iap user identity found")
    ngx.status = 400
    ngx.say("fail to fetch user identity!")
    return ngx.exit(400)
end

local redis = require "resty.redis"
local red = redis:new()

red:set_timeout(1000) -- 1 second
local ok, err = red:connect("${REDIS_HOST}", 6379)
if not ok then
    ngx.log(ngx.ERR, "failed to connect to redis: ", err)
    ngx.status = 500
    ngx.say("failed to connect to redis!")
    return ngx.exit(500)
end

local secs = ngx.time()
local sub_key = string.gsub(key, ":", ".")
local key_uid = string.gsub(sub_key, "@", ".")
local gs_name = "sd-webui-" .. key_uid

local lookup_res, err = red:hget(key_uid, "target")
local gs_name_res, err = red:get(gs_name)
print(lookup_res)
print(gs_name_res)

if lookup_res == ngx.null and gs_name_res ~= "Ready" then                
    local http = require "resty.http"
    local httpc = http.new()
    ngx.log(ngx.INFO, [[{"namespace": "default", "metadata": {"labels": {"user": "]] .. key_uid .. [["}}}]])
    -- local sub_key = string.gsub(key, ":", ".")
    -- local final_uid = string.gsub(sub_key, "@", ".")
    -- local res, err = httpc:request_uri(
    --     "http://agones-allocator.agones-system.svc.cluster.local:443/gameserverallocation",
    --         {
    --         method = "POST",
    --         body = [[{"namespace": "default", "metadata": {"labels": {"user": "]] .. final_uid .. [["}}}]],
    --       }
    -- )
    local res, err = httpc:request_uri(
        "${agones_gs_backend}?username="..key_uid,
            {
            method = "GET",
            ssl_verify = false
          }
    )

    local cjson = require "cjson"
    local resp_data = cjson.decode(res.body)
    local gs_name = resp_data["gs_name"]

    ok, err = red:hset(key_uid, "gsname", gs_name, "lastaccess", secs)
    if not ok then
--         print("fail to set redis key")
        ngx.log(ngx.ERR, "failed to hset: ", err)
        ngx.say("failed to hset: ", err)
        return
    end

    ngx.header.content_type = "text/html"
    ngx.say([[<h1>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Too many users, Please try later! We are cooking for you!</h1><img src="images/coffee-clock.jpg" alt="Take a cup of coffea" />]])
    return
else
    ngx.var.target = lookup_res
    -- local sub_key = string.gsub(key, ":", ".")
    -- local final_uid = string.gsub(sub_key, "@", ".")
    ok, err = red:hset(key_uid, "lastaccess", secs)
    if not ok then
--         print("fail to set redis key")
        ngx.log(ngx.ERR, "failed to hset: ", err)
        ngx.say("failed to hset: ", err)
        return
    end
end