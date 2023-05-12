'''
This module contains the webscraper which extracts and stores necessary page information 
to go about crawling in a polite way with respect to site policies (robots.txt)
'''
import re
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urldefrag
from bs4 import BeautifulSoup
from hashlib import blake2b
import shelve
import time
from threading import RLock

GOOD_RESP = range(200,400)
USER_AGENT = 'my-user-agent'
DOMAINS = ["ics.uci.edu","cs.uci.edu","informatics.uci.edu","stat.uci.edu"]
LOW_INFO_THRES = 0.1


bad_url_count = dict()
banned_domains = set()
subdomains = dict()
info_value = 0


global_lock = RLock()

going_to_visit = set()

global_site = set()
robot_dict = dict()
longest_page = ""
total_words = 0
token_map = {}
fingerprints = set()
stopwords = ['a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves']


DEBUG = False
def debug(msg):
    if DEBUG:
        print(msg)
# checks if a string is ascii
def url_ascii(url):
    return all(ord(c) < 128 for c in url)

# build a dictionary of {domain:RobotFileParser} -- use to check if urlpath is valid
def build_robot(domains):
    global robot_dict
    for domain in domains:
        rp = RobotFileParser()
        rp.set_url('https://www.' + domain + '/robots.txt')
        rp.read()
        robot_dict[domain] = rp
build_robot(DOMAINS)

# check if we can fetch the url (permission from robots.txt)
def check_url_for_robots(url):
    global robot_dict
    parts = urlparse(url)
    return robot_dict[parts.hostname].can_fetch("*", url)

def gen_hash(token):
    NUM_BITS = 128
    digest_size = (NUM_BITS + 7) // 8

    token_b = token.encode('utf-8')
    hash_obj = blake2b(token_b, digest_size=digest_size)
    return int(hash_obj.hexdigest(), 16) # return the hash as an int

def gen_fingerprint(tokens_dict):
    NUM_BITS = 128 # number of bits generated for each hash

    hash_list = list() # list of tuples (hash, multiplier)
    vector_v = list() # to be formed by summing weights 
    total_count = sum(tokens_dict.values())
    for token, count in tokens_dict.items():
        hash_list.append((gen_hash(token), count)) # dividing to normalize counts

    
    mask = 1
    for i in range(NUM_BITS):
        weight = 0
        for hash_, multiplier in hash_list:
            masked_bit = hash_ & mask
            if masked_bit == 0:
                multiplier *= -1
            weight += multiplier
        mask <<= 1 # shift mask to the left by 1
        vector_v.append(weight)
    ret = ""
    for bit in vector_v:
        ret += "1" if bit > 0 else "0"
    return int(ret, 2)

def check_similarity(fingerprint): # returns a boolean, True if similiar, False if not similar
    global fingerprints
    NUM_BITS = 128
    SIMILARITY_THRESHOLD = 0.95
    
    if fingerprint in fingerprints: # Exact Match
        return True
    for fp in fingerprints: # Near-Duplication
        similarity = 1 - (bin(fingerprint ^ fp)[2:].count('1') / NUM_BITS)
        if similarity >= SIMILARITY_THRESHOLD:
            return True
    return False


def scraper(url, resp):
    global going_to_visit
    global global_site
    global token_map
    global fingerprints
    global global_lock

    global_lock.acquire()
    start_time = time.time()
    try:
        links = extract_next_links(url, resp)
        link_results = []
        for link in links:
            valid = is_valid(link)
            if valid and link not in going_to_visit and link not in global_site:
                link_results.append(link)
            with open("valid.txt", "a") as file1:
                file1.write(str(link) + " is " + str(valid) + "\n")
        end_time = time.time()
        debug("Scraping took " + str(end_time - start_time) + " seconds")
        for link in link_results:
            going_to_visit.add(link)
        return link_results
    except Exception as e:
        debug("Scraper failed")
        return list()
    finally:
        global_lock.release()




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

    debug("Writing results to file")

    
    with open("result1.txt", "w+") as file1:
        file1.write("Unique page count: " + str(len(global_site)) + "\n\n" )
        file1.write("Longest page with " + str(total_words) + " words is " + str(longest_page) + "\n\n")
        file1.write("50 most recurring words in order from greatest to least:\n")
        l = list(token_map.items())
        l = sorted(l, key=lambda z: (-z[1],z[0]))
        for i in range(0,min(50, len(l))):
            file1.write(str(l[i]) + "\n")
        # key= 
        file1.write("\nSubdomains of ics.uci.edu:\n")
        for k in sorted(subdomains.keys(), key=lambda z: urlparse(z).hostname):
            v = subdomains[k]
            file1.write(k + ": " + str(v) + "\n")

def tokenize(text):
    # declares list to return and compiles an re expression to match
    comp = re.compile(r"[a-zA-Z'’-]+")
    tokens = re.findall(comp, text)
    tokens = [t.lower() for t in tokens if len(t) > 1]
    return tokens

def compute_word_frequencies(token_list): # Makes use of the global token_map
    # the for loop adds a token to the dict if it does not already exist as a key, and then increments an existing
    # token key if it shows up again
    global token_map
    global stopwords
    
    
    for token in token_list:
        if token not in stopwords:
            if token_map.get(token):
                token_map[token] += 1
            else:
                token_map[token] = 1

def compute_word_count(token_list) -> dict:
    global stopwords

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
    global token_map

    for word, count in wc.items():
        if word in token_map:
            token_map[word] += count
        else:
            token_map[word] = count


def extract_next_links(url, resp):
    global subdomains
    global longest_page
    global total_words
    global fingerprints
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.raw_response.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.content
    # append "/robots.txt"
    # debug("url: ", url) 
    try:
        # change to actual url

        # checks if the raw response has actual content (pages with no content are low information value)
        if resp is None:
            debug("resp is None")
            return list()

        # change to actual url
        if resp.raw_response.url:
            url = resp.raw_response.url

        # checks if the starting frontier url is valid
        if is_valid(url) == False:
            debug("url is not valid at frontier")
            return list()



        # checks to ensure a 200 status
        if resp.status < GOOD_RESP[0] or resp.status > GOOD_RESP[-1]:
            debug("resp status is not 200")
            return list()

        # add url after it passes all checks, but remove fragment
        final_url = urldefrag(resp.raw_response.url)[0]
        #final_url = normalize(final_url) # NameError: name 'normalize' is not defined
        


        # get raw text from the html
        string_document = BeautifulSoup(resp.raw_response.content, "html.parser") #html.fromstring(resp.content)

       
        raw_text = string_document.get_text() #string_document.text_content()
        # remove whitespace extra whitespace 
        
        raw_text = re.sub(r'\s+', ' ', raw_text)
      
        # if word count too low or high, disregard file, used link below to determine minimum, and maximum is 100x that
        # https://whiteboard-mktg.com/blog/how-much-content-is-good-for-seo-rankings/#:~:text=Forbes%20indicates%20that%20an%20average,rank%20as%20highly%20in%20search.

        
        
        # if it is bigger than 4 mb, disregard
        # using this as a reference for 4mb https://www.seoptimer.com/blog/webpage-size/#:~:text=Fast%20forward%20to%20September%202022,and%201%2C818%20KB%20for%20images
        
        if len(raw_text.encode('utf-8')) > 4000000:
            debug("File size too large")
            return list()
        # get word count by using tokenizer
        words = tokenize(raw_text)


        if(not (30 < len(words) < 30000)):
            debug("Word count too low or high")
            return list()
        
        if len(words) > total_words:
            total_words = len(words)
            longest_page = final_url

        
        global_site.add(final_url)
        

        # calculate the information value of each page by comparing it's unique words to total words
        # if total_words > 0:
        #     info_value = len(set(total_words)) / len(total_words) 
        # else:
        #     info_value = 0
        
        # update token map without stop words
        wc = compute_word_count(words)
        append_word_count(wc)

        # Check if duplicate/near-duplicate
        fingerprint = gen_fingerprint(wc)
        
        if check_similarity(fingerprint):
            debug("Duplicate/near-duplicate detected")
            return list()
        fingerprints.add(fingerprint)

        
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
            link = str(link)
            if link.startswith("/") and not link.startswith("//"):
                scheme_and_domain = extract__scheme_and_domain(url)
                link = scheme_and_domain + link
            elif link.startswith("//"):
                link = sub_scheme + ":" + link
            elif link.startswith(".."):
                new_url = sub_scheme + "://" + parsed_domain.hostname + parsed_domain.path
                if new_url[-1] != "/":
                    new_url += "/"
                link = new_url + link
            
            final_list.append(link)
        return final_list
    except Exception as e:
        debug("Hello im here: ")
        print(e)
        write_results()
        return []


def is_valid(url):
    global global_site
    
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
        if parsed.scheme not in set(["http", "https"]) or not parsed.hostname:
            debug("scheme not in http or https")
            return False

        if parsed.hostname in banned_domains:
            debug("hostname in banned domains")
            return False
        
        if url_ascii(url) == False:
            debug("url is not ascii")
            return False
        

        if not check_url_for_robots:
            debug("url is not robots.txt")
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
            debug("url is not a text file")
            return False
        
        # check if the url is a valid domain
        if not re.match(r"(.+\.)?ics\.uci\.edu|(.+\.)?cs\.uci\.edu|(.+\.)?informatics\.uci\.edu|(.+\.)?stat\.uci\.edu", parsed.hostname.lower()):
            debug("url is not a valid domain")
            return False
        
        # checks if the url has a repeating directory in the path to prevent traps
        # does not cover pages that may have been revisted before the second occurence of the directory in question
        if re.match(r"^.*?(/.+?/).*?\1.*$|^.*?/(.+?/)\2.*$", parsed.path.lower()):
            debug("url has a repeating directory")
            return False

        # checks if the url is already in the global set to prevent traps
        if url in global_site:
            debug("url is already in global set")
            return False
        
        # return true if nothing fails in the if checks
        return True


    except TypeError:
        print ("TypeError for ", parsed)
        return False
