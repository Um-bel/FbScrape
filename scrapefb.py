import re, sys, os, json, time, html
import urllib.request
import urllib.parse

USERAGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.109 Safari/537.36 OPR/84.0.4316.50"
TIMEOUT = 300
SLEEP = 5
MAXRESULTS = 15

def fprintf(i, string, *args): 
    [sys.stdout, sys.stderr][i].write(string%args)

def find_between(s, first, last): 
    start = s.index(first) + len(first)
    end = s.index(last, start)
    return s[start:end]

def find_between_r(s, first, last): 
    start = s.rindex(first) + len(first)
    end = s.rindex(last, start)
    return s[start:end]

def geturl(thisurl, json_output = False): 
    fprintf(1, "url: '%s'\n", thisurl)
    thishtml = urllib.request.urlopen(
        urllib.request.Request(
            thisurl, 
            headers = {
                'User-Agent': USERAGENT
            },    
        ), 
        timeout = TIMEOUT
    ).read().decode('utf-8').replace('\"', '"')
    if json_output: 
        return json.loads(
            thishtml[9:]
        )
    return thishtml

def generate_url_for_timeline(domain, page_id, timeline_cursor = None, maxresults = MAXRESULTS): 
    timeline_cursor_str = "null"
    if timeline_cursor is not None: 
        timeline_cursor_str = '"' + timeline_cursor + '"'
    
    return 'https://%s/pages_reaction_units/more/?page_id=%d&cursor={"timeline_cursor":%s,"timeline_section_cursor":{},"has_next_page":true,"card_id":"videos"}&surface=www_pages_posts&unit_count=%d&referrer&dpr=1&__user=0&__a=1'%(
        domain, 
        page_id, 
        timeline_cursor_str, 
        maxresults
    )

def get_new_url_from_json(obj): 
    return (
        urllib.parse.unquote(
            html.unescape(
                find_between_r(
                    obj['domops'][0][-1]['__html'], 
                    'ajaxify="', '" href'
                )
            )
        ) + '&referrer&dpr=1&__user=0&__a=1'
    )

def get_posts_from_json(j): 
    return j['domops'][0][-1]['__html']

def get_timeline_cursor_from_html(html): 
    return find_between_r(html, '&cursor=', '&unit_count=')

def scrapefacebook(page, output="./"): 
    allhtml = geturl(page)
    fbdomain = find_between(page, "https://", '/')
    pageid = int(find_between(allhtml, 'content="fb://page/','?'))
    base_url = "https://" + fbdomain + ""

    current_url = None

    linksfile = "%d.cache"%(pageid)
    if os.path.isfile(linksfile): 
        with open(linksfile, 'r', encoding='utf-8') as f: 
            alllinks = [line for line in f.read().split('\n')]
        alllinks = [link for link in alllinks if not re.match(r'^\s*$', link)]
        fprintf(1, "Restore from check point url: '%s'\n"%alllinks[-1])
        timeline_cursor = find_between(alllinks[-1], '"timeline_cursor":"', '"')
        current_url = generate_url_for_timeline(fbdomain, pageid, timeline_cursor=timeline_cursor)

    if current_url is None: 
        current_url = base_url + get_new_url_from_json(
            geturl(
                generate_url_for_timeline(fbdomain, pageid), 
                json_output = True
            )
        )

    while True: 
        newhtml = geturl(current_url, json_output=True)
        html_posts = get_posts_from_json(newhtml)
        fprintf(1, "Loaded %d posts\n", len(html_posts.split('p')))

        print(html_posts)

        with open(linksfile, "a", encoding='utf-8') as lfile: 
            lfile.write(current_url + "\n")
        current_url = base_url + get_new_url_from_json(newhtml)

        time.sleep(SLEEP)

    
if __name__ == '__main__': 
    if len(sys.argv) != 2: 
        fprintf(1, "Usage: ./scrapefb.py <url>\n")
        fprintf(1, "e.g. ./scrapefb.py 'https://it-it.facebook.com/foresthillseastern'\n")
        sys.exit(1)
    scrapefacebook(sys.argv[1])