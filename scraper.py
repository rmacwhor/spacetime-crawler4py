import re
from urllib.parse import urlparse
import urllib
from bs4 import BeautifulSoup
from collections import defaultdict
import pickle
import os.path

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # safe_to_crawl is a large boolean expression that determines
    # whether we should crawl a link. It checks for the following:
    # there is actually a raw_response (handles 404 and similar errors)
    # the site has 'content-type' in its headers
    # the site is in a text format
    # the site does not redirect anywhere invalid (could be a malicious redirect)
    # the response status is successful (200-299)
    safe_to_crawl = (resp.raw_response and 'content-type' in resp.raw_response.headers
                     and resp.raw_response.headers['Content-Type'].startswith('text')
                     and is_valid(resp.raw_response.url) and 200 <= resp.status <= 299)
    if safe_to_crawl:
        if missing_slash(url, resp.raw_response.url):
            url = url + '/'
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        text = soup.get_text()
        next_links = []
        # ignore pages with low informational content (based on text)
        if len(text)/len(resp.raw_response.content) > .06 and len(text) >= 1000:
            num_words = count_words(text)
            with open('urls.txt', 'a') as urls:
                urls.write(f"{url} -> {num_words}\n")
            for link in soup.find_all('a'):
                # defrag it and address URL encoding
                link = link.get('href')
                if link != None:
                    link = re.sub(r'%7e', '~', link, flags = re.IGNORECASE)
                    link = urllib.parse.urldefrag(link).url
                    parsed_link = urlparse(link)
                    # if the link has a netloc, it's a direct link
                    if parsed_link.netloc:
                        # if it starts with '//', it needs scheme added
                        if link.startswith('//'):
                            link_to_append = 'https:' + link
                        else:
                            link_to_append = link
                    # if there's an '@' in the link, it's an e-mail, so ignore it
                    elif '@' in link:
                        link_to_append = url # better than an empty string
                    # otherwise, it's a relative link (a path)
                    else:
                        url_path = parsed_link.path
                        # if the path starts with a '/', it's relative to the main domain
                        if url_path.startswith('/'):
                            parsedurl = urlparse(url)
                            link_to_append = urllib.parse.urljoin(parsedurl.scheme + '://' + parsedurl.netloc,
                                                                  url_path)
                        # if not, path is relative to the full URL, so add it to end
                        else:
                            link_to_append = urllib.parse.urljoin(url, url_path)
                    # strip link of whitespace (can sometimes cause EOFError in download.py)        
                    next_links.append(link_to_append.strip())
                
        return next_links
    # if the URL is not safe to crawl, don't extract any links from it
    return []

def count_words(text: str) -> int:
    ''' Given a string of text, counts the amount of words in the text (word being
        defined by the tokenizer) and modifies our stored word frequencies. '''
    # if we don't have an existing pickle file, create it
    if not os.path.exists('wordfreqs.pickle'):
        with open('wordfreqs.pickle', 'wb') as wordfreqs:
            pickle.dump(defaultdict(int), wordfreqs, protocol=4)
    
    word_count = 0
    with open('wordfreqs.pickle', 'rb') as wordfreqs:
        word_freqs = pickle.load(wordfreqs)
    for word in re.findall(r'[a-zA-Z0-9]+', text):
        word = word.lower()
        word_count += 1
        word_freqs[word] += 1
    with open('wordfreqs.pickle', 'wb') as wordfreqs:
        pickle.dump(word_freqs, wordfreqs, protocol=4)
    return word_count

def missing_slash(url: str, resp_url: str) -> bool:
    # checks whether the url is missing a slash when it should have one
    parsed1 = urlparse(url)
    parsed2 = urlparse(resp_url)
    if parsed1.netloc == parsed2.netloc and parsed1.path + '/' == parsed2.path:
        return True
    return False
    

def is_valid(url):
    try:
        parsed = urlparse(url)

        if parsed.scheme not in set(["http", "https"]):
            return False

        if ('today.uci.edu' in parsed.netloc and 'department/information_computer_sciences' not in parsed.path):
            return False
        valid_domains = ['.ics.uci.edu', '.cs.uci.edu', '.informatics.uci.edu', '.stat.uci.edu']

        # if the url's domain doesn't include any of these valid domains
        if not any(domain in parsed.netloc for domain in valid_domains):
            return False

        # infinite trap checker: split the path by slashes and put into a set
        # if any part of the path appears more than once, it's probably an infinite trap
        directories = set()
        parts = parsed.path.strip('/').split('/')
        for part in parts:
            if part in directories:
                return False
            # there should only be a file at the end of a path
            if part != parts[-1] and '.' in part:
                return False
            directories.add(part)

        # fix your spam bot evoke >:(
        if 'replytocom' in parsed.query: return False

        # if the URL ends with an extension, check to make sure it's a valid file-type to read
        if re.search(r"\/*\.[^\.\/]*$", parsed.path.lower()):
            return re.match(
                r".*\.(htm|html|php|txt)$", parsed.path.lower())
            
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
