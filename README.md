# Magoole finder and crawler
This repository uses DNS query, bruteforce like domain search, crawling and more technologies to find websites and crawl and reference them on Magoole.

## How it works ?

### Finder
Finder files are contained in `finder/` folder.
1. With given domain extensions, the finder will bruteforce and check every domain name.
2. If a domain is found and a webserver is running, the url is added to a crawling queue.
3. The finder will check every subdomain of the domain and apply the same tests.

### Crawler
The crawler  take each queued website and crawl it.
The scanner take all found domains and scan their websites to get opengraph information, title, icon, content of the page. The scanner is written in python.

When those datas are collected, he simply adds a document to the final database and delete it from temporary database.

## Try locally:
1. Install requirements

```shell
pip install -r requirements.txt
```
2. Set up your mongodb passwords/url<br>
   - If you have an account on Magoole Mongodb just do this
    ```shell
    touch .mongopass && echo "username:password" > .mongopass
    ```
   - Else modify MongoServer url on files finder/main.py and crawler/main.py.py at line `client = pymongo.MongoClient(f"mongodb+srv://yourmongoserver")`
<br>
<br>
3. Run the wanted python file

```shell
cd /path/to/repo && python3 finder/main.py crawler/main.py
```
4. Happy scanning !

You can modify `finder/config.json` to configure search parameters:
```json
{
   "DNS": {
      "domain_max_length": 253,
      "subdomains": false,
      "records": ["A", "AAAA"]
   },

   "THREADING": {
      "enabled": true
   },
   "DOMAIN_EXTENSIONS": [".fr", ".com", ".eu.org", ".tech", ".info", ".dev"]
}
```
