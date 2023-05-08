from flask import escape
import functions_framework
import redis
import time
import os
import socket

@functions_framework.http
def redis_http(request):
    redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
    time_interval = os.getenv("TIME_INTERVAL", 900)
    
    if redis_host == "127.0.0.1":
        print("please correct your redis_host setting!")
        return "please correct your redis_host setting!"

    client = redis.StrictRedis(host=redis_host)
    cursor = '0'

    MESSAGE = "EXIT"

    while cursor != 0:
        try:
            cursor, keys = client.scan(cursor=cursor)
        except Exception as e:
            print("please check your redis connection setting!")
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
                    loop = 0
                    while loop < 3:
                        sock.sendto(bytes(MESSAGE, "utf-8"), (UDP_IP, int(UDP_PORT)))
                        sock.settimeout(0.5)
                        try:
                            data, address = sock.recvfrom(1024)
                        except socket.timeout:
                            print("timeout to close runtime on {}:{}! please check your firewall config!".format(UDP_IP, UDP_PORT))
                            loop = loop + 1
                            if loop == 3:
                                sock.close()
                            continue
                        if MESSAGE in data.decode('utf-8'):
                            print("successed to close runtime on {}:{}!".format(UDP_IP, UDP_PORT))
                            sock.close()
                            break
                        else:
                            loop = loop + 1
                except Exception as e:
                    print(e)
                    print("failed to close runtime on {}:{}!".format(UDP_IP, UDP_PORT))
                    return "failed to close runtime on {}:{}!".format(UDP_IP, UDP_PORT)
                try:
                    client.delete(key)
                except Exception as e:
                    print(e)
                    print("failed to clear key {}!".format(key))
                    return "failed to clear key {}!".format(key)
    return "success tracking!"
