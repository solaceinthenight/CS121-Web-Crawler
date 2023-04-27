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



def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

# 
def extract__scheme_and_domain(url): 
    # return the scheme and domain of the url
    parts = urlparse(url)
    # getting the scheme and domain name
    scheme_and_domain  = f"{parts.scheme}://{parts.netloc}" 
    return scheme_and_domain

# # build a dictionary of {domain:RobotFileParser} -- use to check if urlpath is valid
# def build_robot(domains): # TODO: focus on later.. since it's extra credit
#     pass


# # checking the robots.txt file using robotparser
# def check_robots(url): # TODO: need path & base url ++ fix later if time
#     rp = RobotFileParser()
#     rp.set_url(url + '/robots.txt')
#     rp.read()
#     return rp.can_fetch("*", url)
#     # rp.can_fetch(USER_AGENT, url)
#     # if return true, then we can fetch
#     # if return false, then we can't fetch

    ''' # code to access the robots.txt 
    # if resp.error == GOOD_RESP:
    #     parsed = Bst(response.text, 'html.parser')
    #     agent = 'user_agent'
          policies = {}
          for rule ini soup.get_text().split('\n'):
    '''



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
{
    similarity_threshold = 0.90
    return (angle_btwn_vectors(wc1, wc2) >= similarity_threshold)
}
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


    domain_should_match = ["ics.uci.edu","cs.uci.edu","informatics.uci.edu","stat.uci.edu"]
    
    
    if resp.raw_response is None:
        return list()
    
    if resp.status != GOOD_RESP:
        return list()

    string_document = html.fromstring(resp.raw_response.content)
    links = list(string_document.iterlinks())
    links_set = set()
    for link in links:
        

        link_to_add = link[2]
        # link is a tuple from lxml and the 2 index is the url string
        # check if a link is a relative link
        if link_to_add.startswith("/") and not link_to_add.startswith("//") and not link_to_add.startswith(".."):
            # strip away the path from the url
            scheme_and_domain = extract__scheme_and_domain(url)
            appended_link = scheme_and_domain + link_to_add
            link_to_add = appended_link
        
        # Checking if the link has a domain that matches the domain
        if not any([urlparse(link_to_add).netloc.endswith(domain) for domain in domain_should_match]):
            print("Not a valid domain: " + link_to_add)
            continue 
        if global_site.__contains__(link_to_add):
            print("Already visited: " + link_to_add)
            continue
        else:
            global_site.add(link_to_add)
        links_set.add(link_to_add.split("#")[0])
    print("Links for " + url + " :")
    # [print(link) for link in links_set]
    return [link for link in links_set]

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
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

    except TypeError:
        print ("TypeError for ", parsed)
        raise
