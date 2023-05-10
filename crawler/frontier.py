import os
import shelve
import urllib
from threading import Thread, RLock
from queue import Queue, Empty

from utils import get_logger, get_urlhash, normalize
from scraper import is_valid

class Frontier(object):
    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config

        # Make to_be_downloaded a dictionary of queues, where the key is the hostname
        self.to_be_downloaded = dict()

        DOMAINS = ["ics.uci.edu","cs.uci.edu","informatics.uci.edu","stat.uci.edu"]
        for domain in DOMAINS:
            self.to_be_downloaded[domain] = Queue()
            self.to_be_downloaded[domain].put("https://www." + domain)

        # Make a counter to keep track of which hostname to get from the dictionary
        self.current_hostname_key_counter = 0

        
        if not os.path.exists(self.config.save_file) and not restart:
            # Save file does not exist, but request to load save.
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif os.path.exists(self.config.save_file) and restart:
            # Save file does exists, but request to start from seed.
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)
        # Load existing save file, or create one if it does not exist.
        self.save = shelve.open(self.config.save_file)
        if restart:
            for url in self.config.seed_urls:
                self.add_url(url)
        else:
            # Set the frontier state with contents of save file.
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    self.add_url(url)
    
    def add_to_to_be_downloaded(self, url):
        print("Adding to to_be_downloaded: " + url)
        hostname = urllib.parse.urlparse(url).hostname
        if hostname not in self.to_be_downloaded.keys():
            self.to_be_downloaded[hostname] = Queue()
        self.to_be_downloaded[hostname].put(url)


    def _parse_save_file(self):
        ''' This function can be overridden for alternate saving techniques. '''
        total_count = len(self.save)
        tbd_count = 0
        for url, completed in self.save.values():
            if not completed and is_valid(url):                
                self.add_to_to_be_downloaded(url)
                tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")

    def get_tbd_url(self):
        try:
            if len(self.to_be_downloaded.keys()) == 0:
                return None
            # Get the index from the dictionary using the counter ran as a modulo of the length of the dictionary
            index = self.current_hostname_key_counter % len(self.to_be_downloaded.keys())

            # Get the hostname from the dictionary using the counter as the index
            hostname = list(self.to_be_downloaded.keys())[index]
            
            # Initialize the value to None
            value = None
            try: 
                # Try to get the value from the queue
                value = self.to_be_downloaded[hostname].get_nowait()
            except Empty:
                # If the queue is empty, delete the queue and return None
                del self.to_be_downloaded[hostname]
                # Return another call to get_tbd_url
                return self.get_tbd_url()
            
            self.current_hostname_key_counter += 1
            
            return value
        except IndexError:
            return None

    def add_url(self, url):
        url = normalize(url)
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            self.save[urlhash] = (url, False)
            self.save.sync()
            self.add_to_to_be_downloaded(url)
    
    def mark_url_complete(self, url):
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            # This should not happen.
            self.logger.error(
                f"Completed url {url}, but have not seen it before.")

        self.save[urlhash] = (url, True)
        self.save.sync()
