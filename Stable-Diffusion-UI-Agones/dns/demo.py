import dns.resolver
import json

def resolution_a(domain):
    res = dns.resolver.Resolver()
    res.nameservers = ['8.8.8.8']
    a = res.resolve(domain, 'A')
    for i in a.response.answer:
        for j in i.items:
            if j.rdtype == 1:
                ip = j.address
    return ip

ip_address = resolution_a('www.baidu.com')
print("the resolved address is {}".format(ip_address))