import requests
import csv
import json
from io import StringIO
import scrapy
from scrapy.crawler import CrawlerProcess
import re

def fetch_gdelt_events(max_records=1000):
    """
    Fetches up to `max_records` news events from the latest GDELT 2.0 events file.
    Returns a list of event dicts.
    """
    # Get the latest GDELT 2.0 events file URL
    lastupdate_url = "http://data.gdeltproject.org/gdeltv2/lastupdate-translation.txt"
    resp = requests.get(lastupdate_url)
    # Find the first .translation.export.CSV.zip URL
    latest_file_url = None
    for line in resp.text.strip().split('\n'):
        parts = line.strip().split()
        if len(parts) >= 3 and parts[2].endswith('.translation.export.CSV.zip'):
            latest_file_url = parts[2]
            break
    if not latest_file_url:
        raise RuntimeError("Could not find a .translation.export.CSV.zip URL in lastupdate-translation.txt")
    print(f"Fetching: {latest_file_url}")
    # Download and unzip the CSV file
    import zipfile
    import tempfile
    csv_resp = requests.get(latest_file_url)
    with tempfile.NamedTemporaryFile(suffix='.zip') as tmp_zip:
        tmp_zip.write(csv_resp.content)
        tmp_zip.flush()
        with zipfile.ZipFile(tmp_zip.name, 'r') as zf:
            csv_name = zf.namelist()[0]
            with zf.open(csv_name) as csvfile:
                csv_text = csvfile.read().decode('utf-8')
    csv_file = StringIO(csv_text)
    reader = csv.reader(csv_file, delimiter='\t')
    events = []
    for i, row in enumerate(reader):
        if i == 0:
            headers = row
            continue
        event = dict(zip(headers, row))
        events.append(event)
        if len(events) >= max_records:
            break
    return events

def save_events_to_json(events, filename):
    with open(filename, "w") as f:
        json.dump(events, f, indent=2)
    print(f"Saved {len(events)} events to {filename}")

class GDELTEventParser:
    """
    Parses GDELT 2.0 event records into a structured format for content processing.
    """
    def __init__(self, events):
        self.events = events

    def parse(self):
        """
        Returns a list of parsed news items with selected fields for content processing.
        """
        parsed = []
        for event in self.events:
            # Example: extract key fields (customize as needed for your processor)
            parsed_item = {
                'GLOBALEVENTID': event.get('GLOBALEVENTID'),
                'SQLDATE': event.get('SQLDATE'),
                'Actor1Name': event.get('Actor1Name'),
                'Actor2Name': event.get('Actor2Name'),
                'EventCode': event.get('EventCode'),
                'EventBaseCode': event.get('EventBaseCode'),
                'EventRootCode': event.get('EventRootCode'),
                'NumMentions': event.get('NumMentions'),
                'NumSources': event.get('NumSources'),
                'NumArticles': event.get('NumArticles'),
                'AvgTone': event.get('AvgTone'),
                'SOURCEURL': event.get('SOURCEURL'),
            }
            parsed.append(parsed_item)
        return parsed

def fetch_articles_with_scrapy(urls, max_articles=10):
    """
    Fetches article text for a list of URLs using Scrapy. Returns a list of dicts with 'url' and 'text'.
    Limits to max_articles for speed.
    """
    import scrapy
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings
    import logging

    class ArticleSpider(scrapy.Spider):
        name = "article_spider"
        custom_settings = {
            'LOG_ENABLED': False,
            'DOWNLOAD_TIMEOUT': 15,
            'RETRY_TIMES': 1,
        }
        def __init__(self, urls, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.start_urls = urls
            self.articles = []
        def parse(self, response):
            text = response.xpath('//article//text()').getall()
            if not text:
                text = response.xpath('//p//text()').getall()
            article_text = ' '.join(text).strip()
            self.articles.append({
                'url': response.url,
                'text': article_text
            })

    # Only fetch up to max_articles URLs and filter out empty/None
    urls = [u for u in urls if u and isinstance(u, str) and u.startswith('http')][:max_articles]
    if not urls:
        return []
    process = CrawlerProcess(settings={
        'LOG_ENABLED': False,
        'FEED_FORMAT': 'json',
        'DOWNLOAD_TIMEOUT': 15,
        'RETRY_TIMES': 1,
    })
    spider = ArticleSpider
    results = []
    def collect_results():
        nonlocal results
        results = process.spider.articles
    process.crawl(spider, urls=urls)
    process.start()
    # Scrapy spiders store results in the spider instance
    return spider.articles if hasattr(spider, 'articles') else []

# GDELT 2.0 event field indexes (tab-separated columns)
GDELT_EVENT_FIELDS = [
    'GLOBALEVENTID', 'SQLDATE', 'MonthYear', 'Year', 'FractionDate',
    'EDU', 'UNIVERSITY', '', 'USAGOV', 'AMERICAN', 'USA', 'GOV', '0', '043', '04', '1', '2.8', '10', '-5.88235294117647', 'United States', 'US', '39.828175', '-98.5795', '20250425024500',
    # The rest are not standard, but we use the observed keys
]

# For your sample, the keys are not standard GDELT fields, so we must map by index
GDELT_EVENT_INDEX_MAP = [
    'event_id', 'date', 'month_year', 'year', 'fraction_date',
    'edu', 'university', 'empty', 'usagov', 'american', 'usa', 'gov', 'zero', 'event_code', 'event_base_code', 'num_articles', 'goldstein_scale', 'num_mentions', 'avg_tone',
    'country', 'country_code', 'latitude', 'longitude', 'date_added', 'source_url_key'
]

def extract_url_and_normalize(record):
    # Map the record's keys to a list by their order
    keys = list(record.keys())
    values = list(record.values())
    # If the record is a single key-value (URL mapping), handle that
    if len(keys) == 1 and keys[0].startswith('http'):
        return {'url': values[0]}
    # Otherwise, map by index
    mapped = {}
    for idx, field in enumerate(GDELT_EVENT_INDEX_MAP):
        if idx < len(values):
            mapped[field] = values[idx]
    # Find the first key that looks like a URL and use its value as 'url'
    url = None
    for k, v in record.items():
        if isinstance(k, str) and k.startswith('http'):
            url = v
            break
    mapped['url'] = url
    return mapped

def parse_gdelt_news_sample(input_path, output_path):
    import json
    with open(input_path, 'r') as f:
        data = json.load(f)
    parsed = [extract_url_and_normalize(rec) for rec in data if isinstance(rec, dict)]
    with open(output_path, 'w') as f:
        json.dump(parsed, f, indent=2)
    print(f"Parsed {len(parsed)} records to {output_path}")

# Example usage (add to main or test):
# parser = GDELTEventParser(news_events)
# parsed_news = parser.parse()
# print(parsed_news[0])

if __name__ == "__main__":
    news_events = fetch_gdelt_events(1000)
    save_events_to_json(news_events, "gdelt_news_sample.json")
    # Normalize and parse events using field indexes
    parse_gdelt_news_sample("gdelt_news_sample.json", "gdelt_news_sample_parsed.json")
    # Load normalized file and extract URLs
    with open("gdelt_news_sample_parsed.json", "r") as f:
        normalized = json.load(f)
    # Extract only valid URLs (non-empty, string, startswith http)
    urls = [item['url'] for item in normalized if isinstance(item, dict) and 'url' in item and isinstance(item['url'], str) and item['url'].startswith('http')]
    if urls:
        articles = fetch_articles_with_scrapy(urls, max_articles=10)
        with open("gdelt_articles_sample.json", "w") as f:
            json.dump(articles, f, indent=2)
        print(f"Fetched {len(articles)} articles and saved to gdelt_articles_sample.json")
    else:
        print("No valid URLs found in normalized news.")
