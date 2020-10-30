''' This module helps calculate the report problems for Assignment
2. It relies on two files to function properly:
-urls.txt, a text file that includes a list of all the URLs crawled with
 their respective word counts.
-wordfreqs.pickle, a pickled version of a dictionary of word frequencies
 across all URL web pages. '''

from collections import defaultdict
from urllib.parse import urlparse
import pickle

URLS_PATH = 'urls.txt'
WORDFREQS_PATH = 'wordfreqs.pickle'

''' This is the stopwords set from nltk.corpus, but I
didn't want to bother with the optics of installing an entire module
just for this. '''
STOPWORDS = {'ourselves', 'hers', 'between', 'yourself', 'but',
             'again', 'there', 'about', 'once', 'during', 'out',
             'very', 'having', 'with', 'they', 'own', 'an', 'be',
             'some', 'for', 'do', 'its', 'yours', 'such', 'into',
             'of', 'most', 'itself', 'other', 'off', 'is', 's', 'am',
             'or', 'who', 'as', 'from', 'him', 'each', 'the', 'themselves',
             'until', 'below', 'are', 'we', 'these', 'your', 'his', 'through',
             'don', 'nor', 'me', 'were', 'her', 'more', 'himself', 'this',
             'down', 'should', 'our', 'their', 'while', 'above', 'both', 'up',
             'to', 'ours', 'had', 'she', 'all', 'no', 'when', 'at', 'any',
             'before', 'them', 'same', 'and', 'been', 'have', 'in', 'will',
             'on', 'does', 'yourselves', 'then', 'that', 'because', 'what',
             'over', 'why', 'so', 'can', 'did', 'not', 'now', 'under', 'he',
             'you', 'herself', 'has', 'just', 'where', 'too', 'only', 'myself',
             'which', 'those', 'i', 'after', 'few', 'whom', 't', 'being', 'if',
             'theirs', 'my', 'against', 'a', 'by', 'doing', 'it', 'how',
             'further', 'was', 'here', 'than'} 


def convert_urls_to_dict(path: str) -> dict:
    ''' Given the path to urls.txt, returns a dictionary
    where the keys are URL strings and the values are their
    respective word counts, in integer form. '''
    urls_dict = dict()
    with open(path) as urls:
        for line in urls:
            url, word_count = line.rstrip().split(' -> ')
            urls_dict[url] = int(word_count)
    return urls_dict

def num_unique_pages(urls: dict) -> int:
    ''' Given the dict representing urls.txt, returns the number
    of unique pages in the dict. '''
    return len(urls.keys())

def url_with_max_words(urls: dict) -> tuple:
    ''' Given the dict representing urls.txt, returns the key-value
    pair with the highest word count. '''
    return max((url for url in urls.items()), key = lambda x: x[1])

def most_common_words(path: str) -> list:
    ''' Given the path to the pickled word frequencies dictionary,
    returns a list of the 50 most common words, excluding stop words. '''
    with open(path, 'rb') as wordfreqs:
        word_freqs = pickle.load(wordfreqs)
    word_freqs = {word: count for word, count in sorted(word_freqs.items(),
                  key = lambda item: -item[1]) if (word not in STOPWORDS
                  and not word.isnumeric() and len(word) >= 3)}
    return list(word_freqs.items())[:50]

def all_ics_subdomains(urls: dict) -> list:
    ''' Given the dict representing urls.txt, returns a sorted list
    of 2-tuples with the first item of a tuple being an ICS subdomain
    and the second item being the number of times that subdomain appears
    in urls.txt. '''
    subdomains = defaultdict(int)
    for url in urls.keys():
        subdomain = urlparse(url).netloc
        if 'ics.uci.edu' in subdomain:
            subdomains[subdomain] += 1
    return sorted(subdomains.items())

    


if __name__ == '__main__':
    urls = convert_urls_to_dict(URLS_PATH)
    print(f"Number of unique pages: {num_unique_pages(urls)}")
    max_url, max_word_count = url_with_max_words(urls)
    print(f"Page with most words: {max_url} with {max_word_count} words")
    common_words = most_common_words(WORDFREQS_PATH)
    print("50 most common words: ")
    for i in range(50):
        print(f"{i+1}. {common_words[i][0]}, {common_words[i][1]}")
    print("Subdomains:")
    for subdomain, num_times in all_ics_subdomains(urls):
        print(f"{subdomain}, {num_times}")
    
