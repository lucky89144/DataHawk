import scrapy
import re
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
import argparse
from datetime import datetime, timezone
import logging
import threading
import time
import random
import json
import csv
from scrapy_selenium import SeleniumRequest
from urllib.parse import urlparse
import requests

# Banner
def display_banner():
    banner = """
    DataHawk - OSINT Web Crawler
    ---------------------------------
    Automatic data scraping for sensitive information leaks

    Example usage:
    1. Default (emails):          python DataHawk.py
    2. Usernames:                 python DataHawk.py -q username
    3. Phone numbers:             python DataHawk.py -q phone
    4. URLs:                      python DataHawk.py -q url
    5. IP addresses:              python DataHawk.py -q ip
    6. Custom regex:              python DataHawk.py -q "regex"
    7. Multithreading (4):        python DataHawk.py --threads 4
    8. Output in CSV:             python DataHawk.py --output csv
    9. Output in JSON:            python DataHawk.py --output json
    10. Search all types:         python DataHawk.py -q all

    Default settings:
    - Threads: 1
    - Output format: txt
    - Verbose: False
    - Proxy: None

    Use -h or --help for more options.
    """
    print(banner)


# Scrapy Spider class for crawler
class OSINTSpider(scrapy.Spider):
    name = "datahawk_spider"
    
    def __init__(self, start_urls=None, query=None, proxy=None, verbose=False, output_format='txt', *args, **kwargs):
        super(OSINTSpider, self).__init__(*args, **kwargs)
        self.start_urls = start_urls if start_urls else ["http://example.com"]
        self.query = query if query else "email"
        self.proxy = proxy
        self.verbose = verbose
        self.output_format = output_format

        # Create unique output file name based on the domain of the first URL
        parsed_url = urlparse(self.start_urls[0])
        self.output_file = f"datahawk_results_{parsed_url.netloc.replace('.', '_')}.{self.output_format}"  # Output file name

        self.user_agents = self.get_user_agents()  # Dynamic user agent list

    def get_user_agents(self):
        # Fetch user agents 
        try:
            response = requests.get("https://user-agents.net/")  # Example URL, replace with a real one if needed
            user_agents = re.findall(r'User-Agent: (.+?)\n', response.text)  # Extract user agents
            return user_agents or ['Mozilla/5.0']  # Fallback if no user agents found
        except Exception as e:
            self.log(f"Error fetching user agents: {e}", level=logging.ERROR)
            return ['Mozilla/5.0']  # Fallback user agent

    def start_requests(self):
        for url in self.start_urls:
            user_agent = random.choice(self.user_agents)
            headers = {'User-Agent': user_agent}
            if self.proxy:
                yield SeleniumRequest(url=url, callback=self.parse, headers=headers, meta={"proxy": self.proxy}, errback=self.error_handler)
            else:
                yield SeleniumRequest(url=url, callback=self.parse, headers=headers, errback=self.error_handler)
            sleep_time = random.uniform(3, 6)  # Adjusted rate limiting
            self.log(f"Sleeping for {sleep_time:.2f} seconds before next request.", level=logging.DEBUG)
            time.sleep(sleep_time)

    def parse(self, response):
        if response.status != 200:
            self.log(f"Error: Received {response.status} for URL {response.url}", level=logging.ERROR)
            return

        page_url = response.url
        page_content = response.text

        # Define regex patterns for queries
        patterns = {
            'email': r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
            'username': r'@\w+',
            'phone': r'\+?\d[\d -]{8,}\d',  # Example for phone numbers
            'url': r'https?://[^\s]+',
            'ip': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',  # IPv4 addresses
        }

        found_items = []
        if self.query in patterns:
            found_items = re.findall(patterns[self.query], page_content)
        elif self.query == 'all':
            for key, pattern in patterns.items():
                found_items.extend(re.findall(pattern, page_content))
        else:
            found_items = re.findall(self.query, page_content)

        if found_items:
            for item in found_items:
                self.save_finding(item, page_url)
        else:
            self.log(f"No data matching query '{self.query}' found on {page_url}", level=logging.INFO)
        
        # Follow pagination links
        next_pages = response.css('a.next::attr(href)').getall()  # Get all pagination links
        for next_page in next_pages:
            yield response.follow(next_page, self.parse)

    def save_finding(self, data, source_url):
        # Save findings to text file, CSV, or JSON 
        if self.output_format == 'txt':
            with open(self.output_file, 'a') as f:
                f.write(f"Data: {data}\nSource URL: {source_url}\nScraped At: {datetime.now(timezone.utc).isoformat()}\n{'-'*40}\n")
        elif self.output_format == 'csv':
            with open(self.output_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([data, source_url, datetime.now(timezone.utc).isoformat()])
        elif self.output_format == 'json':
            with open(self.output_file, 'a') as f:
                json.dump({"data": data, "source_url": source_url, "scraped_at": datetime.now(timezone.utc).isoformat()}, f)
                f.write('\n')  # Newline for each JSON object

        self.log(f"Data saved: {data}", level=logging.INFO)

    def error_handler(self, failure):
        self.log(f"Request failed: {failure}", level=logging.ERROR)

    def log(self, message, level=logging.INFO):
        if self.verbose or level == logging.ERROR:
            super().log(message, level)

# Run crawler programmatically
def run_osint_crawler(start_urls, query, proxy=None, threads=1, verbose=False, output_format='txt'):
    process = CrawlerProcess(settings={
        "USER_AGENT": random.choice(['Mozilla/5.0', 'ScrapyBot/1.0']),
        "LOG_LEVEL": logging.INFO,
        "DOWNLOAD_DELAY": random.uniform(3, 6),  # Dynamic delay between requests
    })
    
    # Run with multiple threads
    def crawl_with_threads():
        process.crawl(OSINTSpider, start_urls=start_urls, query=query, proxy=proxy, verbose=verbose, output_format=output_format)
        process.start()
    
    # Run threads in parallel
    for _ in range(threads):
        thread = threading.Thread(target=crawl_with_threads)
        thread.start()
        thread.join()

# Argument parser for CLI options
def parse_arguments():
    parser = argparse.ArgumentParser(description="DataHawk Web Crawler: Scrape websites for data with optional proxy support.")
    parser.add_argument('-q', '--query', help='Custom query to search for (e.g., email, username, phone, url, ip, or custom regex)', default='email')
    parser.add_argument('--output', help='Output format (txt, csv, json)', default='txt', choices=['txt', 'csv', 'json'])
    parser.add_argument('--proxy', help='HTTP/HTTPS proxy to use (e.g., http://proxyserver:port)', default=None)
    parser.add_argument('--threads', type=int, help='Number of threads for multithreading', default=1)
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    return parser.parse_args()

# Function to get URLs
def get_urls_from_user():
    urls = input("Please enter the URLs to crawl, separated by spaces: ")
    return urls.split()

# Main function
if __name__ == "__main__":
    # Display banner
    display_banner()
    
    # Parse arguments
    args = parse_arguments()
    
    # Get URLs from user if not provided in arguments
    urls = get_urls_from_user()
    
    # Run crawler with arguments and multithreading
    run_osint_crawler(start_urls=urls, query=args.query, proxy=args.proxy, threads=args.threads, verbose=args.verbose, output_format=args.output)
