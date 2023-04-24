import string
import time
from typing import List, Tuple
import dns
import pymongo
import requests

PASSWORD = open('.mongopass').read()
client = pymongo.MongoClient(f"mongodb+srv://{PASSWORD}@cluster0.k244v.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.magoole
crawl_queue = db.queue


def addWebsiteToQueue(url) -> None:
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


def hasWebServer(domain) -> Tuple[bool, str]:
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


def isDomain(domain) -> bool:
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
            print(f"DNS Timed out {error.args}")
        except dns.resolver.NoNameservers:
            # Getting timed out
            time.sleep(0.1)
            return isDomain(domain)


def processCheck(domain, is_subdomain=False) -> None:
    """
    Check if `domain` exist, if `domain` runs a webserver and if, add it to crawl queue
    :param domain: domain to check
    :param is_subdomain: optional parameter for output formatting
    :return: None
    """
    if isDomain(domain):
        print(f'Found domain name "{domain}"') if not is_subdomain else ...
        has_web_server, url = hasWebServer(domain)
        if has_web_server:
            print(f'- [+] `{url}`') if not is_subdomain else print(f'\t- [+] `{url}`')
            addWebsiteToQueue(url)
            if SUBDOMAINS:
                # 63 is the max chars between two dot in a domain
                if CHAR_LIMIT - len(domain) < 63:
                    searchSubdomains(domain, '', CHAR_LIMIT - len(domain))
                else:
                    searchSubdomains(domain, '', 63)


def search(domain, ext) -> None:
    """
    Recursive bruteforce search
    :param domain: last fetched domain
    :param ext: domain extension
    :return: None
    """
    if len(domain) <= CHAR_LIMIT:
        for char in CHARS:
            domain = domain + char
            processCheck(domain + ext)
            search(domain, ext)


def searchSubdomains(domain, subdomain, limit) -> None:
    """
    Recursive bruteforce search
    :param domain: last fetched domain
    :param limit: char limit for subdomain
    :return: None
    """
    if len(subdomain) <= limit:
        for char in CHARS:
            subdomain = subdomain + char
            print(subdomain)
            full_domain = f'{subdomain}.{domain}'
            processCheck(full_domain, True)
            searchSubdomains(domain, subdomain, limit)


if __name__ == '__main__':
    EXTENSIONS = ['.fr', '.com', '.eu.org', '.tech', '.info', '.dev']
    DNS_RECORDS_TO_CHECK = ['A', 'AAAA']
    # CHAR_LIMIT = 253 # Real char limit in registration
    CHAR_LIMIT = 10
    SUBDOMAINS = False
    CHARS = list(f"{string.ascii_lowercase}{string.digits}‐")  # possibles chars
    for ext in EXTENSIONS:
        print(f'Search for `{ext}` domains:')
        search('', ext)
