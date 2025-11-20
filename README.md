# DataHawk - OSINT Web Crawler

DataHawk is a OSINT tool for scraping websites to identify sensitive information, designed for researchers and security professionals.

## Features
- Supports searching for emails, usernames, phone numbers, URLs, IP addresses, or custom regex patterns.
- Multithreading for faster crawling.
- Output results in TXT, CSV, or JSON formats.
- Proxy support for anonymous scraping.
- Dynamic user-agent rotation.
## Installation
1. **Download or clone the repo:**
   ```
   cd DataHawk
   ```
## Install the dependencies:
```
pip install -r requirements.txt
```
## Usage
```
python DataHawk.py
```
## Default (scrape emails):
```
python DataHawk.py
```
## Scrape usernames:
```
python DataHawk.py -q username
```
## Use a proxy:
```
python DataHawk.py --proxy http://proxyserver:port
```
## Output results in CSV:
```
python DataHawk.py --output csv
```
## Disclaimer

**DataHawk** *is for educational and research purposes only. Ensure compliance with legal and ethical guidelines when using this tool.*

## License
Licensed under the MIT License.
