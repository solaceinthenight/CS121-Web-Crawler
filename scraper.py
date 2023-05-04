'''
This module contains the webscraper which extracts and stores necessary page information 
to go about crawling in a polite way with respect to site policies (robots.txt)

# The implemented functions are:

def build_robot(array of string)
def check_url_for_robots(string)
def scraper(string, int)
def extract_scheme_and_domain(string)
def write_results(string)
def tokenize()
def compute_word_frequencies(list)
def compute_word_count(dict)
def append_word_count(dict)
def update_most_recent(dict) 
def extract_next_links(string, int)
def is_valid(string)

# below are functions that were sourced
def dot_product(dict, dict):
def angle_btwn_vectors(dict, dict):
def check_similarity(dict, dict):
def check_most_recent(dict) 

'''
import re
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urldefrag
from lxml import html
from bs4 import BeautifulSoup
from math import sqrt, acos # for document similarity
# from bs4 from importBeautifulSoup as Bst
GOOD_RESP = 200
USER_AGENT = 'my-user-agent'
DOMAINS = ["ics.uci.edu","cs.uci.edu","informatics.uci.edu","stat.uci.edu"]
LOW_INFO_THRES = 0.1

subdomains = dict()
global_site = set()
robot_dict = dict()
longest_page = ""
total_words = 0
token_map = {}
most_recent = list() # Five most recent 
stopwords = ['a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves']

# build a dictionary of {domain:RobotFileParser} -- use to check if urlpath is valid
def build_robot(domains):
    for domain in domains:
        rp = RobotFileParser()
        rp.set_url('https://www.' + domain + '/robots.txt')
        rp.read()
        robot_dict[domain] = rp

# check if we can fetch the url (permission from robots.txt)
def check_url_for_robots(url):
    parts = urlparse(url)
    return robot_dict[parts.hostname].can_fetch("*", url)


def scraper(url, resp):
    build_robot(DOMAINS)
    links = extract_next_links(url, resp)

    link_results = []
    for link in links:
        valid = is_valid(link)
        if valid:
            link_results.append(link)
        with open("valid.txt", "a") as file1:
            file1.write(str(link) + " is " + str(valid) + "\n")
    return link_results

    # return [link for link in links if is_valid(link)]

def extract__scheme_and_domain(url): 
    # return the scheme and domain of the url
    parts = urlparse(url)
    # getting the scheme and domain name
    scheme_and_domain  = f"{parts.scheme}://{parts.hostname}" 
    return scheme_and_domain

def write_results():
    global total_words
    global longest_page
    global global_site
    global token_map
    global subdomains
    global most_recent
    global info_value
    
    with open("result1.txt", "w+") as file1:
        file1.write("Unique page count: " + str(len(global_site)) + "\n\n" )
        file1.write("Longest page with " + str(total_words) + " words is " + str(longest_page) + "\n\n")
        file1.write("50 most recurring words in order from greatest to least:\n")
        l = list(token_map.items())
        l = sorted(l, key=lambda z: (-z[1],z[0]))
        for i in range(0,min(50, len(l))):
            file1.write(str(l[i]) + "\n")
        file1.write("\nSubdomains of ics.uci.edu:\n")
        for k in sorted(subdomains.keys()):
            v = subdomains[k]
            file1.write(k + ": " + str(v) + "\n")

    # calculate the information value of each page by comparing it's unique words to total words
    if total_words > 0:
        info_value = len(set(total_words)) / len(total_words) 
    else:
        info_value = 0
    
            
def tokenize(text):
    # declares list to return and compiles an re expression to match
    comp = re.compile(r"[a-zA-Z]+")
    tokens = re.findall(comp, text)
    tokens = [t.lower() for t in tokens if len(t) > 1]
    return tokens

def compute_word_frequencies(token_list): # Makes use of the global token_map
    # the for loop adds a token to the dict if it does not already exist as a key, and then increments an existing
    # token key if it shows up again
    for token in token_list:
        if token not in stopwords:
            if token_map.get(token):
                token_map[token] += 1
            else:
                token_map[token] = 1

def compute_word_count(token_list) -> dict:
    wc = dict()
    for token in token_list:
        if token not in stopwords:
            if token in wc:
                wc[token] += 1
            else:
                wc[token] = 1
    return wc

def append_word_count(wc) -> None:
    """Word count wc is appended onto token_map."""
    for word, count in wc.items():
        if word in token_map:
            token_map[word] += count
        else:
            token_map[word] = count

def update_most_recent(wc) -> None:
    """Given the current word count, add it to most_recent (list), keeping len(most_recent) <= 5."""
    most_recent.append(wc)
    if len(most_recent) > 5:
        del most_recent[0]


# START OF WEBPAGE SIMILARITY CHECK
# Modified from https://www.geeksforgeeks.org/measuring-the-document-similarity-in-python/
def dot_product(wc1, wc2):
    """Compute the dot product of two dictionary vectors."""
    dp = 0.0
    for key in wc1:
        if key in wc2:
            dp += wc1[key] * wc2[key]
    return dp

def angle_btwn_vectors(wc1, wc2):
    """Compute the angle between two dictionary vectors."""
    numerator = dot_product(wc1, wc2)
    denominator = sqrt(dot_product(wc1, wc1) * dot_product(wc2, wc2))
    return acos(numerator / denominator)

def check_similarity(wc1, wc2): # Threshold for similar document: 90%
    """Check the similarity between two word count dictionaries.

    Args:
        wc1 (dict): A dictionary of {token:count} pairs denoting word count.
        wc2 (dict): A dictionary of {token:count} pairs denoting word count.    

    Return:
        boolean: true if document similarity is greater than or equal to similarity threshold; false otherwise.
    """

    similarity_threshold = 0.90
    return (angle_btwn_vectors(wc1, wc2) >= similarity_threshold)

def check_most_recent(wc) -> bool:
    """Check the similarity of the word count with the most_recent (list)."""
    for recent in most_recent:
        if check_similarity(recent, wc):
            return True # Similar
    return False # Not similar
# END OF WEBPAGE SIMILARITY CHECK


def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    # append "/robots.txt"
    # print("url: ", url) 
    global total_words
    global longest_page
    global global_site
    global token_map
    global subdomains
    global most_recent
    

    try:
        # checks if the starting frontier url is valid
        if is_valid(url) == False:
            return list()

        # checks if the raw response has actual content (pages with no content are low information value)
        if resp.raw_response is None:
            return list()
        # if less than the low information value (25), then the page is not counted
        elif info_value >= LOW_INFO_THRES:
            return list()

        # checks to ensure a 200 status
        if resp.status != GOOD_RESP:
            return list()

        # checks to ensure page is in html 
        # TODO: AttributeError: 'CaseInsensitiveDict' object has no attribute 'get_content_type'
        # if resp.raw_response.headers.get_content_type() != "text/html":
        #     return list()

        # add url after it passes all checks, but remove fragment
        final_url = urldefrag(resp.url)[0]
        #final_url = normalize(final_url) # NameError: name 'normalize' is not defined
        global_site.add(final_url)


        # get raw text from the html
        string_document = BeautifulSoup(resp.raw_response.content, "html.parser") #html.fromstring(resp.raw_response.content)

        # get word count by using tokenizer
        raw_text = string_document.get_text() #string_document.text_content()
        words = tokenize(raw_text)
        if len(words) > total_words:
            total_words = len(words)
            longest_page = final_url
        
        # update token map without stop words
        compute_word_frequencies(words)

        # compute a word count dictionary
        # wc = compute_word_count(words) # NEED LOGIC CHECKINGs
        
        parsed_domain =  urlparse(final_url)
        sub_hostname = parsed_domain.hostname
        sub_scheme = parsed_domain.scheme

        if sub_hostname[0:4] == "www.":
            sub_hostname = sub_hostname[4:]

        if re.match(r".+\.ics\.uci\.edu", sub_hostname):

            final_url_domain =  f"{sub_scheme}://{sub_hostname}"

            if subdomains.get(final_url_domain):
                subdomains[final_url_domain] += 1
            else:
                subdomains[final_url_domain] = 1

        # write results
        write_results()

        # retrieve the links from the text and return it
        links =  string_document.find_all("a") #list(string_document.iterlinks())
        final_list = list()
        for link in links:
            link = link.get("href") #link = link[2]
            link = urldefrag(link)[0]
            if link.startswith("/") and not link.startswith("//") and not link.startswith(".."):
                scheme_and_domain = extract__scheme_and_domain(url)
                link = scheme_and_domain + link
            final_list.append(link)
        return final_list
    except Exception as e:
        print("Hello im here: ")
        print(e)
        write_results()
        return []


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        #url = normalize(url) # NameError: name 'normalize' is not defined

        # remove the fragment
        url = urldefrag(url)[0]

        # parse string into scheme, domain, path, query, and fragment
        parsed = urlparse(url)

        # return fals eif not in http or https
        if parsed.scheme not in set(["http", "https"]):
            return False

        # return false if there is a non text file
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False
        
        # check if the url is a valid domain
        if not re.match(r"(.+\.)?ics\.uci\.edu|(.+\.)?cs\.uci\.edu|(.+\.)?informatics\.uci\.edu|(.+\.)?stat\.uci\.edu", parsed.hostname.lower()):
            return False
        
        # checks if the url has a repeating directory in the path to prevent traps
        # does not cover pages that may have been revisted before the second occurence of the directory in question
        if re.match(r"^.*?(/.+?/).*?\1.*$|^.*?/(.+?/)\2.*$", parsed.path.lower()):
            return False

        # checks if the url is already in the global set to prevent traps
        if url in global_site:
            return False
        
        # return true if nothing fails in the if checks
        return True


    except TypeError:
        print ("TypeError for ", parsed)
        raise
