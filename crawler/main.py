import os.path
import string

import pymongo
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from typing import Tuple, List

PASSWORD = open('.mongopass').read()
client = pymongo.MongoClient(f"mongodb+srv://{PASSWORD}@cluster0.k244v.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.magoole
crawl_queue = db.queue
sites = db.sites
pages = db.pages
search = db.search


def addWebsite(website: dict) -> pymongo.collection.ObjectId:
    """
    Add a website to database
    :param website: website to add
    :return:
    """
    if sites.find_one({'url': website['url']}):
        sites.update_one({'url': website['url']}, {'$set': website})
        return sites.find_one({'url': website['url']})['_id']
    return sites.insert_one(website).inserted_id


def addPage(website: pymongo.collection.ObjectId, title: str, desc: str, terms: list, attributes: dict) -> None:
    """
    Add a page of `website` to database
    :param website: website to add
    :param title: Title of the page
    :param desc: Description of the page
    :param terms: List of terms in association with the page
    :return:
    """
    page = {
        'title': title,
        'description': desc,
        'terms': terms,
        'attributes': attributes,
        'site': website
    }

    if pages.find_one({'site': website}):
        pages.update_one({'site': website}, {'$set': page})
        page_id = pages.find_one({'site': website})['_id']
    else:
        page_id = pages.insert_one(page).inserted_id

    for term in terms:
        word, frequency = term
        word = word.lower()
        if search.find_one({'term': word}):
            term_pages = search.find_one({'term': word})['pages']
            term_pages.append((page_id, frequency))
            search.update_one({'term': word}, {'$set': {'pages': term_pages}})
        else:
            search.insert_one({'term': word.lower(), 'pages': [(page_id, frequency)]})


def getTwentyFrequentsTerms(content: str) -> List[Tuple[str, float]]:
    """
    Get the 20 most frequent terms of content
    :param content: content to be analysed
    :return: list of terms
    """
    expressions = content.split()
    terms = []
    for expression in expressions:
        for term in NOT_TERMS:
            if term == '.' and not expression.endswith('.'):
                continue
            expression = expression.replace(term, '')
        terms.append(expression) if len(expression) > 1 else ...
    words_frequency = sorted([(word, terms.count(word) / len(terms)) for word in terms], key=lambda obj: obj[0])
    words_frequency = sorted(set(words_frequency), key=lambda obj: obj[1], reverse=True)
    return words_frequency[:29]


def getPageDescription(parser: BeautifulSoup) -> str:
    """
    Get the page at `url` description
    :param parser: content of page as BS
    :return: the description
    """
    if parser.find('meta', attrs={'property': 'og:description'}):
        description = parser.find('meta', attrs={'property': 'og:description'}).attrs.get('content')
    else:
        description = parser.text[:20]
    return description if description else 'Aucune description pour ce site...'


def getPageTitle(parser: BeautifulSoup) -> str:
    """
    Get the page at `url` description
    :param parser: content of page as BS
    :return: the description
    """
    if parser.find('title'):
        title = parser.find('title').text
    else:
        title = parser.find('h1').text
    return title.replace('\n', '') if title else parser.text[:20]


def websiteFromMainPage(url: str, parser: BeautifulSoup) -> dict:
    """
    Create a database ready document for the website at `url`
    :param url: website url
    :param parser: BeautifulSoup object
    :return: dict
    """
    if parser.find('meta', attrs={'property': 'og:title'}):
        name = parser.find('meta', attrs={'property': 'og:title'}).attrs.get('content')
    else:
        name = parser.find('title').text
    icon = parser.find('link', attrs={'rel': 'icon'}).attrs.get('href')
    if not icon:
        icon = ''  # //TODO put default icon
    website = {
        'url': url,
        'name': name,
        'icon': icon
    }
    return website


def getRobotsRules(website: str) -> RobotFileParser:
    """
    Return a parsed version of robots.txt if found
    :param website: website url
    :return: list of forbidden routes
    """
    try:
        real_url = requests.get(f'{website}/robots.txt').url
        robots = RobotFileParser(real_url)
        robots.read()
        return robots
    except Exception:
        return RobotFileParser()


def parseMetaTags(tags: list, page_attributes: dict) -> None:
    """
    Parse and add meta `tags` to `page_attributes`
    :param tags:
    :param page_attributes:
    :return:
    """
    for meta in tags:
        if meta.attrs.get('name'):
            match meta['name']:
                case 'description':
                    page_attributes['descriptions'].append(meta['content'])
                case 'keywords':
                    page_attributes['keywords'] += meta['content'].split(',')
                case 'author':
                    page_attributes['authors'].append(meta['content'])

        if meta.attrs.get('property'):
            match meta['property']:
                case 'og:title':
                    page_attributes['titles'].append(meta['content'])
                case 'og:description':
                    page_attributes['descriptions'].append(meta['content'])
                case 'og:type':
                    page_attributes['types'] += meta['content'].split(',')
                case 'og:url':
                    page_attributes['urls'].append(meta['content'])
                case 'og:image':
                    page_attributes['covers'].append(meta['content'])


def discover(url: str, past: list = [], rules: RobotFileParser = RobotFileParser) -> List[Tuple[str, BeautifulSoup]]:
    """
    Crawler each pages of `url` and return them in a list of tuple (url, BS)
    :param url: url to crawl
    :param past: past crawled pages
    :param rules: A RobotFileParser object to navigate through the website and respect robots rules...
    :return: List[Tuple[str, BeautifulSoup]]
    """
    headers = {
        'User-Agent': 'MagooleCrawler/0.0'
    }
    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.RequestException:
        print(f"\t- [-] Ignoring `{url}`: failed with RequestException.")
        return []
    url = response.url
    content = response.content
    parser = BeautifulSoup(content, 'html.parser')
    print(f"- [+] Crawling ` {url} `") if past == [] else print(f"\t - [+] ` {url} `")

    if not response.ok:
        print(f"\t- [-] Ignoring `{url}`: failed with status code {response.status_code}.")
    if not parser.find():
        print(f"\t- [-] Ignoring `{url}`: no valid html page.")

    anchors = parser.find_all('a')
    parsed_url = urlparse(url)
    base_url = parsed_url.scheme + '://' + parsed_url.hostname

    pages: List[Tuple[str, BeautifulSoup]] = [(url, parser)]

    past.append(parsed_url.path)

    for anchor in anchors:
        ref = anchor.attrs.get('href')
        if ref:
            if rules.can_fetch('*', ref) and rules.can_fetch('Magoole', ref):
                if (not ref.startswith('http') and not ref.startswith('#') and ref not in past) or (base_url in ref and ref not in past):
                    past.append(ref)
                    if ref.startswith('http'):
                        page_url = ref
                    else:
                        page_url = base_url + ref if ref.startswith('/') else f"{base_url}/{ref}"
                    for page in discover(page_url, past, rules):
                        pages.append(page)
    return pages


def crawl(url) -> None:
    """
    Navigate through a website and make wordlists...
    :param url: url to crawl
    :return: None
    """
    parsed_url = urlparse(url)
    base_url = parsed_url.scheme + '://' + parsed_url.hostname
    site_pages = discover(url, rules=getRobotsRules(base_url))

    primary_url, page = site_pages[0]
    website = websiteFromMainPage(primary_url, page)
    website_id = addWebsite(website)

    for page in site_pages:
        url, content = page
        text_content = content.text.replace('\n\n', '\n')

        terms = getTwentyFrequentsTerms(text_content)
        description = getPageDescription(content)
        title = getPageTitle(content)

        attributes = {
            'titles': [],
            'types': [],
            'descriptions': [],
            'urls': [],
            'covers': [],
            'keywords': []
        }
        parseMetaTags(content.find_all('meta'), attributes)

        addPage(website_id, title, description, terms, attributes)
        exit()
        # print(text_content)


def isWebsiteBlackListed(domain: str) -> bool:
    """
    Get a website risk score with urlvoid.com
    :param domain: domain to check
    :return: bool
    """
    return domain in BLACKLISTED_DOMAINS


def iterateQueue() -> None:
    """
    Crawl each website in the queue.
    :return: None
    """
    for website in crawl_queue.find():
        domain = urlparse(website['url']).hostname
        if isWebsiteBlackListed(domain):
            print(f'- [-] Ignoring ` {website} `: blacklisted !')
            continue
        crawl(website)
        crawl_queue.delete_one(website)
    exit()


if __name__ == '__main__':
    RISK_SCORE_LIMIT = 80
    file = 'crawler/blocklist.txt' if os.path.isfile('crawler/blocklist.txt') else 'blocklist.txt'
    BLACKLISTED_DOMAINS = open(file).read().split()
    NOT_TERMS = list(string.punctuation.replace('@', ''))
    iterateQueue()
