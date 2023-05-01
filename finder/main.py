import json
import math
import os.path
import string
import sys
import threading
import time
from typing import Tuple, Union
import dns
import pymongo
import requests
import numpy

PASSWORD = open('.mongopass').read().replace('\n', '')
MONGO_URL = f"mongodb+srv://{PASSWORD}@cluster0.k244v.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
client = pymongo.MongoClient(MONGO_URL)


def addWebsiteToQueue(url: str) -> None:
    """
    Add website url to the crawling queue.
    :param url: url of the website to add
    :return: None
    """
    client.start_session()
    crawl_queue = client.magoole.queue

    if crawl_queue.find_one({'url': url}) is None:
        crawl_queue.insert_one({
            'url': url
        })
    else:
        print('Website is already queued') if not SILENT else ...
    client.close()


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
        headers = {
            'User-Agent': 'MagooleFinder/0.0'
        }
        secure_response = requests.get(secure_url, headers=headers)
        secure_url = secure_response.url
        if secure_response.ok:
            return True, secure_url
        raise requests.exceptions.SSLError(f'Secure connection failed with status code {secure_response.status_code}.')
    except requests.exceptions.SSLError:
        return True, url
    except requests.exceptions.ConnectionError:
        return False, ''
    except Exception:
        return False, ''


def isDomain(domain: str, recursion: int = 0) -> bool:
    """
    Check if the `domain` is registered by querying dns.
    :param domain: domain to check
    :param recursion:
    :return: bool
    """
    if recursion < DNS_MAX_TEST:
        for record_type in DNS_RECORDS_TO_CHECK:
            try:
                RESOLVER.resolve(domain, record_type)
                return True
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                return False
            except dns.resolver.Timeout as error:
                print(f'⚠️ DNS Timed out: "{error.args[0]}" for "{domain}"') if recursion and not SILENT < 2 else ...
                time.sleep(0.1)
                return isDomain(domain, recursion + 1)
            except dns.resolver.NoNameservers as error:
                print(f'⚠️ DNS encountered a problem: "{error.args[0]}"') if recursion and not SILENT < 2 else ...
            except dns.name.LabelTooLong as error:
                print(f'⚠️ DNS encountered a problem: "{error.args[0]}" for {domain}') if recursion < 2 and not SILENT else ...
    else:
        print(f'⚠️ DNS query aborted for domain: {domain} after {recursion} tests.') if not SILENT else ...
        return False


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
        print(f'Found domain name "{domain}"') if not is_subdomain and not SILENT else ...
        has_web_server, url = hasWebServer(domain)
        if has_web_server:
            print(f'- [+] ` {url} `')
            addWebsiteToQueue(url)
        if SUBDOMAINS:
            # 63 is the max chars between two dot in a domain
            if CHAR_LIMIT - len(domain) < 63:
                searchSubdomains(domain, '', CHAR_LIMIT - len(domain))
            else:
                searchSubdomains(domain, '', 63)


def search(domain: str, ext: str, chars: Union[list, numpy.ndarray], length: int = 63) -> None:
    """
    Recursive bruteforce search
    :param domain: last fetched domain
    :param ext: domain extension
    :param chars: a custom list of chars for the first recursion
    :param length: insight deepness
    :return: None
    """
    if len(domain + ext) <= CHAR_LIMIT and len(domain) + 1 < 63:
        for i in range(1, length):
            for char in chars:
                new_domain = domain + char
                processCheck(new_domain + ext)
                if i < length:
                    search(new_domain, ext, numpy.array(CHARS), length - i)


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
    length = CHAR_LIMIT if CHAR_LIMIT < 63 else 63
    if THREADING:
        divided_chars = []
        parts = THREADS
        chunk_size = math.ceil(len(CHARS) / parts)
        last_chunk = 0
        for part in range(1, parts):
            chunk = part * chunk_size
            divided_chars.append(CHARS[last_chunk:chunk]) if not part == parts else divided_chars.append(CHARS[chunk:])
            last_chunk = chunk
        for chars in divided_chars:
            thread_name = divided_chars.index(chars)
            thread = threading.Thread(target=search, args=('', ext, numpy.array(chars), length), name=f'Thread n°{thread_name} for `{ext}`')
            print(f'Starting thread n°{thread_name}') if not SILENT else ...
            thread.start()
            PROCESSES.append(thread)
    else:
        search('', ext, numpy.array(CHARS), length)
        print(f'✅ Finished for `{ext}`.')


if __name__ == '__main__':
    if os.path.isfile('finder/config.json'):
        config = json.loads(open('finder/config.json').read())
    elif os.path.isfile('config.json'):
        config = json.loads(open('config.json').read())
    else:
        print("❌ No config files found, exiting.")
        exit()
    PROCESSES = []
    RESOLVER = dns.resolver.Resolver()
    EXTENSIONS = config['DOMAIN_EXTENSIONS']
    RESOLVER.nameservers = config['DNS']['nameservers']
    DNS_RECORDS_TO_CHECK = config['DNS']['records']
    DNS_MAX_TEST = config['DNS']['max_recursion']
    CHAR_LIMIT = config['DNS']['domain_max_length']
    SUBDOMAINS = config['DNS']['subdomains']
    THREADING = config['THREADING']['enabled']
    THREADS = config['THREADING']['threads']
    SILENT = True if '-s' in sys.argv or '-q' in sys.argv else False
    CHARS = list(f"{string.ascii_lowercase}{string.digits}-")  # possibles chars
    for ext in EXTENSIONS:
        searchFor(ext)

    print(f"Started {len(PROCESSES)} threads.")
    for thread in PROCESSES:
        if thread.is_alive():
            thread.join()
        print(f'✅ Finished for `{thread.name}`.')
    client.start_session()
    crawl_queue = client.magoole.queue
    print(f"{len(crawl_queue.find())} websites added to queue !")
