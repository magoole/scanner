![](https://repository-images.githubusercontent.com/421378452/ef9e37ee-afcd-4c94-a486-b17620b0bef2)
<div align="center">

# Magoole finder and crawler
Navigate through internet to find and crawl websites.

</div>
This repository uses DNS query, bruteforce like domain search, crawling and more technologies to find websites and crawl and reference them on Magoole.

## Table of content
- [Credits](#credits-and-acknowledgement)
- [How it works ?](#how-it-works-)
  - [Finder](#finder)
  - [Crawler](#crawler)
- [Try it locally](#try-locally-)

## Credits and acknowledgement
- Source code under [CeCLL Licence V2.1](https://github.com/magoole/scanner/tree/main/LICENSE?raw=true) by [@camarm](https://github.com/camarm-dev).
- Brand and logos under [CC BY-NC-ND 3.0 FR](https://creativecommons.org/licenses/by-nc-nd/3.0/fr/) by [@camarm](https://github.com/camarm-dev).
- Icon from [Fontawesome V5.15.4](https://fontawesome.com/v5/icons/brain?f=classic&s=solid).
- Font "League Spartan".

## How it works ?

The Magoole scanner is divided in two parts: 
- **The finder**: recover a list of websites urls
- **The crawler**: crawl and analyse website content

### Finder
Finder files are contained in `finder/` folder.
1. With given domain extensions, the finder will bruteforce and check every domain name.
2. If a domain is found and a webserver is running, the url is added to a crawling queue.
3. The finder will check every subdomain of the domain and apply the same tests.

### Crawler
Crawler files are contained in `crawler/` folder.
1. The crawler take each queued website and perform http requests to recover his html pages.
2. Using BM25, it tokenizes pages content and index them.
3. Meta tags are analysed so images and medias can be referenced as well !
4. Provides his work through a database.

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
   - Or modify MongoServer url on file finder/main.py and crawler/main.py.py at line `client = pymongo.MongoClient(f"mongodb+srv://yourmongoserver")`
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
      "records": ["A", "AAAA"],
      "nameservers": ["1.1.1.1"]
   },

   "THREADING": {
      "enabled": true
   },
   "DOMAIN_EXTENSIONS": [".fr", ".com", ".eu.org", ".tech", ".info", ".dev"]
}
```
