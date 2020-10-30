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
    # ADDED CONDITION TO CHECK IF CONTENT-TYPE IS 'text/html'
    if resp.raw_response and resp.raw_response.headers['Content-Type'].startswith('text'):
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
                    # if the link has a netloc, add it directly
                    if parsed_link.netloc:
                        next_links.append(link)
                    # otherwise, treat it as a path and join it to the given url
                    # UNLESS end path is already the same (could result in infinite trap)
                    else:
                        # trim leading/trailing slashes for easy urljoin
                        url_path = parsed_link.path.lstrip('/').rstrip('/')
                        if not url.endswith(url_path):
                            # if there's a . in the url.path, we're at the "end" of a path (.html)
                            # the '/' determines whether we append a new path to the URL
                            # or change the last section of path
                            url = url if '.' in url_path else url + '/'
                            joined_url = urllib.parse.urljoin(url, url_path)
                            next_links.append(joined_url) 
        return next_links
            
            # OLD RETURN STATEMENT DOES NOT REMOVE FRAGMENTS
            #return [link.get('href') for link in soup.find_all('a')]
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
        valid_domains = ['ics.uci.edu', 'cs.uci.edu', 'informatics.uci.edu', 'stat.uci.edu']

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
