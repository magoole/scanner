# Magoole scanner
This repository uses DNS query, ip scan, reverse ip lookup, crawling and more technologies to find websites and crawl them to reference them on Magoole.

# Try locally:
1. Install requirements

```shell
pip install -r requirements.txt
```
2. Set up your mongodb passwords/url<br>
   - If you have an account on Magoole Mongodb just do this
    ```shell
    touch .mongopass && echo "username:password" > .mongopass
    ```
   - Else modify MongoServer url on files scan.py/url_search.py at line `client = pymongo.MongoClient(f"mongodb+srv://yourmongoserver")`
<br>
<br>
3. Run python file

```shell
cd /path/to/scanner && python3 url_search.py/scan.py
```
4. Happy scanning !
