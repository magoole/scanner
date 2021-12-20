import time
import pymongo
import re
import requests
import urllib.parse

PASSWORD = open('.mongopass').read()
client = pymongo.MongoClient(f"mongodb+srv://{PASSWORD}@cluster0.k244v.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.magoole
sites = db.sites
to_scan = db.to_scan


def get_word_list(html):
    try:
        words = re.findall("(?<=title=\")(.*?)(?=\s*\")", str(html))
    except Exception:
        words = []
    try:
        alts = re.findall("(?<=alt=\")(.*?)(?=\s*\")", str(html))
    except Exception:
        alts = []
    try:
        desc = re.findall("(?<=name=\"description\")(.*?)(?=\s*>)", str(html))[0].split("=")[1].replace("\"", '')
    except Exception:
        desc = ""
    try:
        name = re.findall("(?<=<title)(.*?)(?=\s*</title>)", str(html))[0].replace('>', '')
        if "\"" in name:
            name = name.split("\"")[-1]
    except Exception:
        name = "Unknown"
    words = [urllib.parse.unquote(word) for word in words]
    alts = [urllib.parse.unquote(alt) for alt in alts]
    desc = urllib.parse.unquote(desc)
    name = urllib.parse.unquote(name)
    return words, alts, desc, name


def scan_websites():
    for scan in to_scan.find():
        html = requests.get(scan['url']).content
        words, alts, desc, name = get_word_list(html)
        sites.insert_one({"url": scan['url'], "title": name, "word_list": words, "alt_list": alts, "description": desc})
        to_scan.delete_one({'url': scan['url']})
    print('End of urls')
    time.sleep(120)
    scan_websites()


if __name__ == '__main__':
    scan_websites()
