local headers = ngx.req.get_headers()
local key = headers["x-goog-authenticated-user-email"]
print(key)

if not key then
    ngx.log(ngx.ERR, "no iap user identity found")
    ngx.say("fail to fetch user identity!")
    return ngx.exit(400)
end

local redis = require "resty.redis"
local red = redis:new()

red:set_timeout(1000) -- 1 second
local ok, err = red:connect("${REDIS_HOST}", 6379)
if not ok then
    ngx.log(ngx.ERR, "failed to connect to redis: ", err)
    ngx.say("failed to connect to redis!")
    return ngx.exit(500)
end

local secs = ngx.time()

local lookup_res, err = red:hget(key, "target")
print(lookup_res)

if lookup_res == ngx.null then                
    local http = require "resty.http"
    local httpc = http.new()
    local sub_key = string.gsub(key, ":", ".")
    local final_uid = string.gsub(sub_key, "@", ".")
    local res, err = httpc:request_uri(
        "http://agones-allocator.agones-system.svc.cluster.local:443/gameserverallocation",
            {
            method = "POST",
            body = [[{"namespace": "default", "metadata": {"labels": {"user": "]] .. final_uid .. [["}}}]],
          }
    )

    local cjson = require "cjson"
    local resp_data = cjson.decode(res.body)
    local host = resp_data["address"]
    if host == nil then
        ngx.header.content_type = "text/html"
        ngx.say([[<h1>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Too many users, Please try later! We are cooking for you!</h1><img src="images/coffee-clock.jpg" alt="Take a cup of coffea" />]])
        return
    end

    local sd_port = resp_data["ports"][2]["port"]
    local gs_port = resp_data["ports"][1]["port"]
    
    ngx.var.target = host .. ":" .. sd_port
    print("set redis ", ngx.var.target)

    ok, err = red:hset(key, "target", ngx.var.target, "port", host .. ":" .. gs_port, "lastaccess", secs)
    if not ok then
        print("fail to set redis key")
        ngx.say("failed to hset: ", err)
        return
    end
else
    ngx.var.target = lookup_res
    ok, err = red:hset(key, "lastaccess", secs)
    if not ok then
        print("fail to set redis key")
        ngx.say("failed to hset: ", err)
        return
    end
end