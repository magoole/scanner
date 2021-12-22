import ipaddress
import pymongo
import requests
from pythonping import ping

PASSWORD = open('.mongopass').read()
client = pymongo.MongoClient(f"mongodb+srv://{PASSWORD}@cluster0.k244v.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.magoole
to_scan = db.to_scan


def addData(url):
    # print(to_scan.find_one({'url': url}))
    if to_scan.find_one({'url': url}) is None:
        to_scan.insert_one({'url': 'http://' + url})
        print(f"Website: {url}")
    print('Ignore')


def isWebsite(ip):
    try:
        assert ping(ip, count=1).success()
        print('Find ip: ', ip)
        response = requests.get(f'http://{ip}', headers={'FROM': 'Magoole, free and open source search motor'})
        print(response.url)
        if response.url == f'http://{ip}/':
            return False, None
        else:
            return True, response.url
    except Exception as e:
        # raise e
        return False, None


def Int2IP(ipnum):
    o1 = int(ipnum / 16777216) % 256
    o2 = int(ipnum / 65536) % 256
    o3 = int(ipnum / 256) % 256
    o4 = int(ipnum) % 256
    return '%(o1)s.%(o2)s.%(o3)s.%(o4)s' % locals()


if __name__ == '__main__':
    start_ip = ipaddress.IPv4Address('0.0.0.0')
    end_ip = ipaddress.IPv4Address('255.255.255.255')
    print(f'Find ips from {start_ip} to {end_ip}')
    for ip_int in range(int(start_ip), int(end_ip)):
        IP = Int2IP(ip_int)
        IPExist, url = isWebsite(IP)
        if IPExist:
            print(f'{IP}: {url}')
