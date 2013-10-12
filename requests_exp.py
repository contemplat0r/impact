import urlparse
import requests

def web_get_html(url, headers, proxies):
    req = None 
    html = ''
    try:
        req = requests.get(url, proxies=proxies,  headers=headers)
    except requests.exceptions.ConnectionError:
        print 'Catch ConnectionError'
    if req != None:
        html = req.text
    return html

if __name__ == "__main__":

    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:10.0.7) Gecko/20100101 Firefox/10.0.7 Iceweasel/10.0.7'}

proxies = {
          "http": "http://192.168.2.1:5432",
            "https": "http://192.168.2.1:443",
            }

html = web_get_html('https://www.jim.or.jp', proxies, headers)

print html
