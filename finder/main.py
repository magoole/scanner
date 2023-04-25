import json
import os.path
import string
import threading
import time
from typing import Tuple
import dns
import pymongo
import requests

PASSWORD = open('.mongopass').read()
client = pymongo.MongoClient(f"mongodb+srv://{PASSWORD}@cluster0.k244v.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.magoole
crawl_queue = db.queue


def addWebsiteToQueue(url: str) -> None:
    """
    Add website url to the crawling queue.
    :param url: url of the wbesite to add
    :return: None
    """
    if crawl_queue.find_one({'url': url}) is None:
        crawl_queue.insert_one({
            'url': url
        })
    print('Website is already queued')


def hasWebServer(domain: str) -> Tuple[bool, str]:
    """
    Check if the `domain` runs a webserver.
    :param domain: the domain to check
    :return: bool
    """
    url = f'http://{domain}'
    secure_url = f'https://{domain}'
    try:
        url = requests.get(url).url
        secure_response = requests.get(secure_url)
        secure_url = secure_response.url
        if secure_response.ok:
            return True, secure_url
        raise requests.exceptions.SSLError(f'Secure connection failed with status code {secure_response.status_code}.')
    except requests.exceptions.SSLError:
        return True, url
    except requests.exceptions.ConnectionError:
        return False, ''


def isDomain(domain: str) -> bool:
    """
    Check if the `domain` is registered by querying dns.
    :param domain:
    :return:bool
    """
    for record_type in DNS_RECORDS_TO_CHECK:
        try:
            dns.resolver.resolve(domain, record_type)
            return True
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            return False
        except dns.resolver.Timeout as error:
            print(f'⚠️ DNS Timed out: "{error.args[0]}"')
        except dns.resolver.NoNameservers:
            # Getting timed out
            time.sleep(0.1)
            return isDomain(domain)
        except dns.name.LabelTooLong as e:
            print(domain)
            raise e


def processCheck(domain: str, is_subdomain: bool = False) -> None:
    """
    Check if `domain` exist, if `domain` runs a webserver and if, add it to crawl queue
    :param domain: domain to check
    :param is_subdomain: optional parameter for output formatting
    :return: None
    """
    if domain.split('.')[-2].endswith('-'):
        # Ignore because it's not a valid DNS label
        return
    if isDomain(domain):
        print(f'Found domain name "{domain}"') if not is_subdomain else ...
        has_web_server, url = hasWebServer(domain)
        if has_web_server:
            print(f'- [+] `{url}`')
            addWebsiteToQueue(url)
            if SUBDOMAINS:
                # 63 is the max chars between two dot in a domain
                if CHAR_LIMIT - len(domain) < 63:
                    searchSubdomains(domain, '', CHAR_LIMIT - len(domain))
                else:
                    searchSubdomains(domain, '', 63)


def search(domain: str, ext: str) -> None:
    """
    Recursive bruteforce search
    :param domain: last fetched domain
    :param ext: domain extension
    :return: None
    """
    if len(domain + ext) <= CHAR_LIMIT and len(domain) + 1 < 63:
        for char in CHARS:
            new_domain = domain + char
            processCheck(new_domain + ext)
            search(new_domain, ext)


def searchSubdomains(domain: str, subdomain: str, limit: int) -> None:
    """
    Recursive bruteforce search
    :param domain: the main domain with extension
    :param subdomain: the last fetched subdomain
    :param limit: char limit for subdomain
    :return: None
    """
    if len(subdomain) <= limit:
        for char in CHARS:
            subdomain = subdomain + char
            full_domain = f'{subdomain}.{domain}'
            processCheck(full_domain, True)
            searchSubdomains(domain, subdomain, limit)


def searchFor(ext) -> None:
    """
    Search for domains.`ext`
    :param ext: domain extension
    :return: None
    """
    print(f'🔄 Searching for `{ext}` domains:')
    search('', ext)
    print(f'✅ Finished for `{ext}`.')


if __name__ == '__main__':
    if os.path.isfile('finder/config.json'):
        config = json.loads(open('finder/config.json').read())
    elif os.path.isfile('config.json'):
        config = json.loads(open('config.json').read())
    else:
        print("❌ No config files found, exiting.")
        exit()
    EXTENSIONS = config['DOMAIN_EXTENSIONS']
    DNS_RECORDS_TO_CHECK = config['DNS']['records']
    CHAR_LIMIT = config['DNS']['domain_max_length']
    SUBDOMAINS = config['DNS']['subdomains']
    THREADING = config['THREADING']['enabled']
    CHARS = list(f"{string.ascii_lowercase}{string.digits}-")  # possibles chars
    PROCESSES = []
    for ext in EXTENSIONS:
        if THREADING:
            thread = threading.Thread(target=searchFor, args=[ext], name=f'Domain scanning: `{ext}`')
            PROCESSES.append(thread)
            continue
        searchFor(ext)
    for thread in PROCESSES:
        thread.start()
        print(f'"{thread.name}" started')
        thread.join()
