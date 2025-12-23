#!/usr/bin/env python3
"""
RBZ Exchange Rates Scraper
Scrapes exchange rates from Reserve Bank of Zimbabwe and stores in MongoDB
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime, timezone
from pymongo import MongoClient
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_mongodb_client():
    """Get MongoDB client from environment variable"""
    mongo_uri = os.environ.get('MONGODB_URI')
    if not mongo_uri:
        raise ValueError("MONGODB_URI environment variable not set")
    return MongoClient(mongo_uri)


def scrape_rbz_rates():
    """Scrape current exchange rates from RBZ website"""
    url = "https://www.rbz.co.zw/"

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Ch-Ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
    })

    try:
        response = session.get(url, verify=False, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        page_title = soup.title.string.strip() if soup.title else "No Title"

        target_tab = soup.find('div', id='baTab0')

        if not target_tab:
            return {
                "success": False,
                "error": "Container 'baTab0' not found.",
                "debug_info": f"Page title: '{page_title}'",
                "suggestion": "Site may be blocked by WAF"
            }

        # Extract date
        date_text = None
        header_text = target_tab.get_text(" ", strip=True)
        date_match = re.search(r'EXCHANGE RATES\s+([\d-]+)', header_text)
        if date_match:
            date_text = date_match.group(1)

        # Parse rates
        rates = {}
        rows = target_tab.find_all('tr')

        for row in rows:
            cols = row.find_all('td')

            if len(cols) >= 4:
                def get_clean_val(element):
                    return element.get_text(strip=True).replace('\u00a0', '').strip()

                raw_currency = get_clean_val(cols[0])

                if "CURRENCY" in raw_currency.upper() or not raw_currency:
                    continue

                currency_key = raw_currency.replace(":", "").strip()

                bid = get_clean_val(cols[1]).replace(" ", "").replace(",", "")
                ask = get_clean_val(cols[2]).replace(" ", "").replace(",", "")
                avg = get_clean_val(cols[3]).replace(" ", "").replace(",", "")

                if re.match(r'[\d.]+', avg):
                    rates[currency_key] = {
                        "bid": float(bid) if bid else 0,
                        "ask": float(ask) if ask else 0,
                        "avg": float(avg) if avg else 0
                    }

        return {
            "success": True,
            "date": date_text,
            "rates": rates,
            "scraped_at": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def save_to_mongodb(data):
    """Save scraped rates to MongoDB"""
    if not data.get("success"):
        print(f"Scraping failed: {data.get('error')}")
        return False

    try:
        client = get_mongodb_client()
        db = client.rbz_rates
        collection = db.daily_rates

        # Create document
        doc = {
            "date": data["date"],
            "date_parsed": datetime.strptime(data["date"], "%Y-%m-%d") if data["date"] else None,
            "rates": data["rates"],
            "scraped_at": datetime.now(timezone.utc),
            "source": "rbz.co.zw"
        }

        # Upsert by date (update if exists, insert if not)
        result = collection.update_one(
            {"date": data["date"]},
            {"$set": doc},
            upsert=True
        )

        # Create index on date for fast queries
        collection.create_index("date", unique=True)
        collection.create_index("date_parsed")

        print(f"✅ Saved rates for {data['date']}")
        print(f"   Currencies: {', '.join(data['rates'].keys())}")

        if result.upserted_id:
            print(f"   Action: Inserted new document")
        else:
            print(f"   Action: Updated existing document")

        client.close()
        return True

    except Exception as e:
        print(f"❌ MongoDB Error: {e}")
        return False


def main():
    """Main entry point"""
    print("🏦 RBZ Exchange Rates Scraper")
    print("=" * 40)

    # Scrape rates
    print("\n📡 Fetching rates from RBZ...")
    data = scrape_rbz_rates()

    if data["success"]:
        print(f"✅ Successfully scraped rates for {data['date']}")
        print(f"   Found {len(data['rates'])} currencies")

        # Print rates summary
        print("\n📊 Rates Summary:")
        for currency, rate in data["rates"].items():
            print(f"   {currency}: {rate['avg']}")

        # Save to MongoDB
        print("\n💾 Saving to MongoDB...")
        save_to_mongodb(data)

        # Output JSON for GitHub Actions
        print("\n📄 JSON Output:")
        print(json.dumps(data, indent=2, default=str))
    else:
        print(f"❌ Scraping failed: {data.get('error')}")
        print(json.dumps(data, indent=2))
        exit(1)


if __name__ == "__main__":
    main()
