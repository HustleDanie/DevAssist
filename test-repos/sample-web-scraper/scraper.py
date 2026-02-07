#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web Scraper - Python 2 Legacy Code
A simple web scraping utility with various Python 2 patterns.
"""

import urllib2
import urlparse
import HTMLParser
import cPickle as pickle
import StringIO


class WebScraper:
    """A simple web scraper class."""
    
    def __init__(self, base_url):
        self.base_url = base_url
        self.visited = set()
        self.data = {}
    
    def fetch_page(self, url):
        """Fetch a web page and return its content."""
        try:
            print "Fetching: %s" % url
            request = urllib2.Request(url)
            request.add_header('User-Agent', 'Mozilla/5.0')
            response = urllib2.urlopen(request, timeout=10)
            content = response.read()
            print "Successfully fetched %d bytes" % len(content)
            return content
        except urllib2.URLError, e:
            print "Error fetching URL: %s" % e
            return None
        except urllib2.HTTPError, e:
            print "HTTP Error %d: %s" % (e.code, e.reason)
            return None
    
    def parse_links(self, html, base_url):
        """Extract all links from HTML content."""
        links = []
        # Simple regex-like extraction (Python 2 style)
        import re
        pattern = r'href=["\']([^"\']+)["\']'
        matches = re.findall(pattern, html)
        
        for match in matches:
            full_url = urlparse.urljoin(base_url, match)
            if full_url not in self.visited:
                links.append(full_url)
        
        print "Found %d new links" % len(links)
        return links
    
    def save_results(self, filename):
        """Save scraped data to a pickle file."""
        print "Saving results to %s..." % filename
        with open(filename, 'wb') as f:
            pickle.dump(self.data, f)
        print "Done!"
    
    def load_results(self, filename):
        """Load previously scraped data."""
        print "Loading results from %s..." % filename
        with open(filename, 'rb') as f:
            self.data = pickle.load(f)
        print "Loaded %d items" % len(self.data)
    
    def scrape(self, max_pages=10):
        """Main scraping method."""
        queue = [self.base_url]
        pages_scraped = 0
        
        while queue and pages_scraped < max_pages:
            url = queue.pop(0)
            if url in self.visited:
                continue
            
            self.visited.add(url)
            content = self.fetch_page(url)
            
            if content is not None:
                self.data[url] = content
                new_links = self.parse_links(content, url)
                queue.extend(new_links)
                pages_scraped += 1
        
        print "Scraping complete. Scraped %d pages." % pages_scraped


def main():
    url = raw_input("Enter URL to scrape: ")
    max_pages = raw_input("Enter max pages (default 10): ")
    
    if not max_pages:
        max_pages = 10
    else:
        max_pages = int(max_pages)
    
    scraper = WebScraper(url)
    scraper.scrape(max_pages)
    
    save = raw_input("Save results? (y/n): ")
    if save.lower() == 'y':
        filename = raw_input("Enter filename: ")
        scraper.save_results(filename)


if __name__ == '__main__':
    main()
