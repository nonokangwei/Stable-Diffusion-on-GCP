from flask import escape
import functions_framework
import os
import time
import json
import redis

@functions_framework.http
def agones_listener_http(request):
    redis_host = os.getenv("REDIS_HOST", "127.0.0.1")

    if redis_host == "127.0.0.1":
        return "please correct your redis_host setting!"
    
    try:
        request_json = request.get_json(force=True, silent=True)
        print(request_json)
    except Exception as e:
        print(e)
        return "this is malform request!"
    
    client = redis.StrictRedis(host=redis_host)

    if request.method == "POST" and request_json != None:
        try:
            # event_type = request_json['body']['header']['headers']['event_source']
            gs_status = request_json['body']['message']['message']['body']['status']['state']
            gs_name = request_json['body']['message']['message']['body']['metadata']['name']
        except Exception as e:
            print(e)
            return "this is malform request!"

        if client.get(gs_name) == None:
            try:
                client.set(gs_name, gs_status)

                gs_user = request_json['body']['message']['message']['body']['metadata']['labels']['user']
                current_time = int(time.time())

                client.hmset(gs_user, {'startaccess': current_time, 'lastaccess': current_time, 'status': 'NotReady'})

                print("GS OnAdd: add gs {} {} state success!".format(gs_name, gs_status))
                return "GS OnAdd: add gs {} {} state success!".format(gs_name, gs_status)
            except Exception as e:
                print(e)
                return "GS OnAdd: add gs state failed!"
        else:
            print("GS OnAdd: existing gs {} {} state success!".format(gs_name, gs_status))
            return "GS OnAdd: existing gs {} {} state success!".format(gs_name, gs_status)
    elif request.method == "PUT" and request_json != None:
        try:
            # event_type = request_json['body']['header']['headers']['event_source']
            gs_status = request_json['body']['message']['message']['body']['new_obj']['status']['state']
            gs_name = request_json['body']['message']['message']['body']['new_obj']['metadata']['name']
            # gs_user = request_json['body']['message']['message']['body']['new_obj']['metadata']['labels']['user']
        except Exception as e:
            print(e)
            return "this is malform request!"
        
        if client.get(gs_name).decode('utf-8') != 'Ready' and gs_status == 'Ready':
            try:
                client.set(gs_name, gs_status)
                
                gs_user = request_json['body']['message']['message']['body']['new_obj']['metadata']['labels']['user']
                target = request_json['body']['message']['message']['body']['new_obj']['status']['address']
                #ToDo: using compute engine lookup to get node private ip to support GKE private cluster
                #target_fqdns = request_json['body']['message']['message']['body']['new_obj']['status']['nodeName']
                sd_port = request_json['body']['message']['message']['body']['new_obj']['status']['ports'][1]['port']
                gs_port = request_json['body']['message']['message']['body']['new_obj']['status']['ports'][0]['port']
                current_time = int(time.time())

                client.hmset(gs_user, {'target': target + ":" + str(sd_port), 'port': target + ":" + str(gs_port), 'lastaccess': current_time, 'status': 'Ready'})

                print("GS Update: update gs {} {} state success!".format(gs_name, gs_status))
                return "GS Update: update gs {} {} state success!".format(gs_name, gs_status)
            except Exception as e:
                print("GS Update: update gs state failed! ", e)
                return "GS Update: update gs state failed!"
        else:
            print("GS Update: latest gs {} {} state!".format(gs_name, gs_status))
            return "GS Update: gs state not ready yet!"
    elif request.method == "DELETE" and request_json == None:
        args = request.args
        gs_name = args.get('name')

        if gs_name != None and client.get(gs_name) != None:
            try:
                client.delete(gs_name)
                print("GS Delete: delete gs state success!")

                # Complete a structured log entry.
                # entry = dict(
                #     severity="NOTICE",
                #     message="usage-stat",
                #     # Log viewer accesses 'component' as jsonPayload.component'.
                #     username="abc.company.com",
                #     starttime=123,
                #     endtime=456,
                # )
                # print(json.dumps(entry))  

                return "GS Delete: delete gs state success!"
            except Exception as e:
                print("GS Delete: delete gs state failed! ", e)
                return "GS Delete: delete gs state failed!"
            # ToDo: add the usage data to bigquery  
        else:
            print("GS Delete: delete gs state failed!")
            return "GS Delete: delete gs state failed!"
    else:
        print("No match method: this is malform request!")
        return "this is malform request!"
