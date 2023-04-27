import re
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
from lxml import html
from math import sqrt, acos # for document similarity
# from bs4 from importBeautifulSoup as Bst
GOOD_RESP = 200
USER_AGENT = 'my-user-agent'
DOMAINS = ["ics.uci.edu","cs.uci.edu","informatics.uci.edu","stat.uci.edu"]

global_site = set()
robot_dict = dict()

# build a dictionary of {domain:RobotFileParser} -- use to check if urlpath is valid
def build_robot(domains):
    for domain in domains:
        rp = RobotFileParser()
        rp.set_url(domain + '/robots.txt')
        rp.read()
        robot_dict[domain] = rp

# check if we can fetch the url (permission from robots.txt)
def check_url_for_robots(url):
    parts = urlparse(url)
    return robot_dict[parts.hostname].can_fetch(*, url)


def scraper(url, resp):
    build_robot(DOMAINS)
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

# 
def extract__scheme_and_domain(url): 
    # return the scheme and domain of the url
    parts = urlparse(url)
    # getting the scheme and domain name
    scheme_and_domain  = f"{parts.scheme}://{parts.netloc}" 
    return scheme_and_domain


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

def check_similarity(wc1, wc2) # Threshold for similar document: 90%
    """Check the similarity between two word count dictionaries.

    Args:
        wc1 (dict): A dictionary of {token:count} pairs denoting word count.
        wc2 (dict): A dictionary of {token:count} pairs denoting word count.    

    Return:
        boolean: true if document similarity is greater than or equal to similarity threshold; false otherwise.
    """

    similarity_threshold = 0.90
    return (angle_btwn_vectors(wc1, wc2) >= similarity_threshold)

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
    if is_valid(url) == False:
        return list()

    if resp.raw_response is None:
        return list()
    
    if resp.status != GOOD_RESP:
        return list()

    # Ensure content header type is html
    
    if resp.raw_response.headers.get_content_type() != "text/html":
        return list()

    string_document = html.fromstring(resp.raw_response.content)
    # get raw text from the html
    raw_text = string_document.text_content()
    links = list(string_document.iterlinks())
    links_set = set()
    for link in links:
    
        link_to_add = link[2]
        if link_to_add.startswith("/") and not link_to_add.startswith("//") and not link_to_add.startswith(".."):
            scheme_and_domain = extract__scheme_and_domain(url)
            appended_link = scheme_and_domain + link_to_add
            link_to_add = appended_link

        global_site.add(url)

        links_set.add(link_to_add.split("#")[0])

    print("Links for " + url + " :")
    # [print(link) for link in links_set]
    return [link for link in links_set]

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        url = normalize(url)
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
        
        # check if the url is a valid domain
        domain_should_match = ["ics.uci.edu","cs.uci.edu","informatics.uci.edu","stat.uci.edu"]
        if not re.match(r".*\.ics\.uci\.edu|.*\.cs\.uci\.edu|.*\.informatics\.uci\.edu|.*\.stat\.uci\.edu", parsed.netloc.lower()):
            return False
        
        if re.match(r"^.*?(/.+?/).*?\1.*$|^.*?/(.+?/)\2.*$", url):
            return False

        if global_site.__contains__(url):
            return False
        

            
        return True


    except TypeError:
        print ("TypeError for ", parsed)
        raise
