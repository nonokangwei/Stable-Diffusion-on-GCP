from flask import escape
import functions_framework
import redis
import time
import os
import socket

@functions_framework.http
def redis_http(request):
    redis_host = os.getenv("10.120.148.68", "127.0.0.1")
    # time_interval in secs unit
    time_interval = os.getenv("TIME_INTERVAL", 900)
    
    if redis_host == "127.0.0.1":
        return "please correct your redis_host setting!"

    client = redis.StrictRedis(host=redis_host)
    cursor = '0'

    MESSAGE = "EXIT"

    while cursor != 0:
        try:
            cursor, keys = client.scan(cursor=cursor)
        except Exception as e:
            print(e)
            return "please check your redis connection setting!"
        
        for key in keys:
            result = client.hgetall(key)
            last_access = int(result[b'lastaccess'].decode('utf-8'))
            current_time = int(time.time())
            if current_time - last_access >= time_interval:
                try:
                    host_info = result[b'port'].decode('utf-8').split(":")
                    UDP_IP = host_info[0]
                    UDP_PORT = host_info[1]
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # 
                    sock.sendto(bytes(MESSAGE, "utf-8"), (UDP_IP, int(UDP_PORT)))
                except Exception as e:
                    print(e)
                    return "failed to close runtime on {}:{}!".format(UDP_IP, UDP_PORT)
                try:
                    client.delete(key)
                except Exception as e:
                    print(e)
                    return "failed to clear key {}!".format(key)
    return "success tracking!"