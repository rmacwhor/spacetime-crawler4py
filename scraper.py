import re
from urllib.parse import urlparse
import urllib
from bs4 import BeautifulSoup
import urllib.robotparser # Import for robots.txt implmentation
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
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        text = soup.get_text()
        # TEXT TO CONTENT RATIO CHECK TO AVOID GRABBING LINKS FROM SEMI-EMPTY PAGES
        next_links = []
        if len(text)/len(resp.raw_response.content) > .05:
            num_words = count_words(text)
            with open('urls.txt', 'a') as urls:
                urls.write(f"{url} -> {num_words}\n")
            for link in soup.find_all('a'):
                # defrag it and remove trailing slash
                link = link.get('href')
                if link != None:
                    link = urllib.parse.urldefrag(link).url.rstrip('/')
                    parsed_link = urlparse(link)
                    # if the link has a netloc, it's a direct link
                    if parsed_link.netloc:
                        # if it starts with '//', it needs scheme added
                        if link.startswith('//'):
                            link_to_append = 'https:' + link
                        else:
                            link_to_append = link
                    # otherwise, it's a relative link (a path)
                    else:
                        # trim leading/trailing slash for easier parsing
                        url_path = parsed_link.path.lstrip('/').rstrip('/')
                        # wacky regex to test if path ends with extension
                        if re.match(r"\/*\.[^\.\/]*$", url_path):
                            # if path ends with an extension
                            # -if link also has extension, only swap the extensions for path
                            if re.match(r"\/*\.[^\.\/]*$", url):
                                link_to_append = urllib.parse.urljoin(url, url_path)
                            # otherwise, add file to end of link path (/ is important!)
                            else:
                                link_to_append = urllib.parse.urljoin(url + '/', url_path)
                        # check for infinite trap
                        elif url.endswith(url_path):
                            link_to_append = url
                        else:
                            link_to_append = urllib.parse.urljoin(url + '/', url_path)
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
            pickle.dump(dict(), wordfreqs, protocol=4)
    
    word_count = 0
    with open('wordfreqs.pickle', 'rb') as wordfreqs:
        word_freqs = pickle.load(wordfreqs)
    for word in re.findall(r'[a-zA-Z0-9]+', text):
        word = word.lower()
        word_count += 1
        if word not in word_freqs:
            word_freqs[word] = 0
        word_freqs[word] += 1
    with open('wordfreqs.pickle', 'wb') as wordfreqs:
        pickle.dump(word_freqs, wordfreqs, protocol=4)
    return word_count

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

        ''' robot_parser = urllib.robotparser.RobotFileParser() # robotparser object to parse the robots.txt file
        robot_parser.set_url(parsed.scheme + "://" + parsed.netloc + "/robots.txt") # set the url to include "robots.txt" at the end
        robot_parser.read() # read in the robot.txt file 

        if(robot_parser.can_fetch("*", url) == False): # if the crawler is not allowed to crawl the site return False
            return False '''

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
