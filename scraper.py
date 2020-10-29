import re
from urllib.parse import urlparse
import urllib
from bs4 import BeautifulSoup

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # VERY BASIC IMPLEMENTATION, only for testing

    # ADDED CONDITION TO CHECK IF CONTENT-TYPE IS 'text/html'
    if resp.raw_response and resp.raw_response.headers['Content-Type'].startswith('text/html'):
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        # TEXT TO CONTENT RATIO CHECK TO AVOID GRABBING LINKS FROM SEMI-EMPTY PAGES
        if len(soup.get_text())/len(resp.raw_response.content) > .05:
            return [urllib.parse.urldefrag(link.get('href')).url for link in soup.find_all('a')]
            
            # OLD RETURN STATEMENT DOES NOT REMOVE FRAGMENTS
            #return [link.get('href') for link in soup.find_all('a')]
    return []

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        if ('today.uci.edu' in parsed.netloc and 'department/information_computer_sciences' not in parsed.path):
            return False
        valid_domains = ['ics.uci.edu', 'cs.uci.edu', 'informatics.uci.edu', 'stat.uci.edu']

        # if the url's domain doesn't include any of these valid domains
        if not any(domain in parsed.netloc for domain in valid_domains):
            return False
        return not re.match(
            r".*\.|\/(css|js|bmp|gif|jpe?g|ico" # changed this line to check for either a '.' or a '/' instead
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
