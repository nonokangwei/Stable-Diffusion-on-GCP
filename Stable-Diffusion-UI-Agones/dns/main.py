from flask import escape
import functions_framework
import dns.resolver
import json

def resolution_a(domain):
    query_list = []
    res = dns.resolver.Resolver()
    res.nameservers = ['8.8.8.8']
    a = res.resolve(domain, 'A')
    for i in a.response.answer:
        for j in i.items:
            if j.rdtype == 1:
                ip = j.address
                query_list.append(ip)
    return query_list

@functions_framework.http
def dns_http(request):
    try:
        request_args = request.args
        dns_domain = request_args.get('domain')
    except Exception as e:
        print(e)
        return json.dumps({'dns_domain': 'fail'}), 200, {'ContentType': 'application/json'}
    
    ip_address = resolution_a(dns_domain)
    result = ''
    return "the resolved address is {}".format(result.join(ip_address))