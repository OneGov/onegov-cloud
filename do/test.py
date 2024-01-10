# checks to see if all urls are valid
# Usage example:
# python check_urls.py /path/to/file.csv --column 2


import argparse
import csv
import concurrent.futures
import requests
import time


def check_url_status(url):
    try:
        response = requests.get(url, timeout=5)
        status = response.status_code == 200
        return url, status, response.elapsed.total_seconds()
    except requests.RequestException as e:
        print(e)
        return url, False, 0


def check_urls_sequentially(urls):
    results = []
    for url in urls:
        time.sleep(0.01)
        url, status, response_time = check_url_status(url)
        results.append((url, status, response_time))
    return results


parser = argparse.ArgumentParser(
    description='Check URLs in a CSV file for their status.'
)
parser.add_argument(
    'csv_file', type=str, help='Path to the CSV file containing URLs'
)
parser.add_argument(
    '--column',
    type=int,
    default=2,
    help='Column number containing the URLs (default: 2)',
)
args = parser.parse_args()

url_list = []

with open(args.csv_file, mode='r', encoding='utf-8') as file:
    reader = csv.reader(file)
    next(reader, None)  # Skip the header row if there is one
    for row in reader:
        if len(row) >= args.column:
            url_list.append(row[args.column - 1])

# results = check_urls_sequentially(url_list)
results = check_urls_sequentially(url_list)

for url, status, response_time in results:
    status_text = 'OK' if status else 'Not OK'
    if not status:
        print(
            f"{url}: {status_text} (Response Time: {response_time:.2f} seconds)"
        )


# Usage example:
# python check_urls.py /path/to/your/csv/file.csv --column 2
