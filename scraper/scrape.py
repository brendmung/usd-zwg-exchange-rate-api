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

        # Extract date (existing fix)
        date_text_raw = None
        header_text = target_tab.get_text(" ", strip=True)
        date_match = re.search(r'EXCHANGE RATES\s+([\d-]+)', header_text)
        if date_match:
            date_text_raw = date_match.group(1)

        formatted_date = None
        if date_text_raw:
            try:
                parsed_dt = datetime.strptime(date_text_raw, "%d-%m-%Y")
                formatted_date = parsed_dt.strftime("%Y-%m-%d")
            except ValueError:
                print(f"Warning: Could not parse date '{date_text_raw}' with %d-%m-%Y format. Keeping original.")
                formatted_date = date_text_raw

        # Parse rates
        rates = {}
        rows = target_tab.find_all('tr')

        for row in rows:
            cols = row.find_all('td')

            if len(cols) >= 4:
                def get_clean_val(element):
                    return element.get_text(strip=True).replace('\u00a0', '').strip()

                raw_currency_label = get_clean_val(cols[0])

                if "CURRENCY" in raw_currency_label.upper() or not raw_currency_label:
                    continue

                # --- NEW FIX STARTS HERE (Currency Consistency) ---
                currency_code = raw_currency_label.replace(":", "").strip().upper()
                is_inverse_pair = False # Flag if the rate is 1 ZWG = X Foreign (needs inversion)

                if "/" in currency_code:
                    parts = currency_code.split('/')
                    if len(parts) == 2:
                        first_part = parts[0].strip()
                        second_part = parts[1].strip()

                        if second_part == "ZWG": # e.g., "USD/ZWG" -> target "USD"
                            currency_code = first_part
                            is_inverse_pair = False
                        elif first_part == "ZWG": # e.g., "ZWG/ZAR" -> target "ZAR", needs inversion
                            currency_code = second_part
                            is_inverse_pair = True
                        else:
                            # Unexpected format, fallback to original key (e.g. "AUD/CAD") but simplified
                            print(f"Warning: Unexpected currency pair format: {raw_currency_label}")
                            currency_code = currency_code.replace("/ZWG", "").replace("ZWG/", "")
                    else:
                        print(f"Warning: Unexpected currency label format with multiple slashes: {raw_currency_label}")
                        # Fallback for malformed strings
                        currency_code = currency_code.replace("/ZWG", "").replace("ZWG/", "")

                # Parse numeric values, ensuring they are valid numbers
                bid_str = get_clean_val(cols[1]).replace(" ", "").replace(",", "")
                ask_str = get_clean_val(cols[2]).replace(" ", "").replace(",", "")
                avg_str = get_clean_val(cols[3]).replace(" ", "").replace(",", "")

                # Only proceed if avg_str is a valid number to avoid errors
                if not re.match(r'^-?\d+(\.\d+)?$', avg_str):
                    print(f"Warning: Invalid average rate '{avg_str}' for {raw_currency_label}. Skipping.")
                    continue

                original_bid = float(bid_str) if re.match(r'^-?\d+(\.\d+)?$', bid_str) else 0
                original_ask = float(ask_str) if re.match(r'^-?\d+(\.\d+)?$', ask_str) else 0
                original_avg = float(avg_str)

                if is_inverse_pair:
                    # If original rate is 1 ZWG = X Foreign (e.g., ZWG/ZAR = 0.6421),
                    # we want 1 Foreign = 1/X ZWG.
                    #
                    # old_bid: RBZ pays this much FOREIGN for 1 ZWG. (1 ZWG = old_bid FOREIGN)
                    # old_ask: RBZ sells 1 ZWG for this much FOREIGN. (1 ZWG = old_ask FOREIGN)
                    #
                    # For 1 FOREIGN = X ZWG:
                    # New bid (what ZWG gets for 1 Foreign): 1 / old_ask (of ZWG/FOREIGN)
                    # New ask (what ZWG pays for 1 Foreign): 1 / old_bid (of ZWG/FOREIGN)

                    # Guard against division by zero
                    new_bid = 1 / original_ask if original_ask != 0 else 0
                    new_ask = 1 / original_bid if original_bid != 0 else 0
                    new_avg = 1 / original_avg if original_avg != 0 else 0

                    rates[currency_code] = {
                        "bid": float(f"{new_bid:.4f}"),
                        "ask": float(f"{new_ask:.4f}"),
                        "avg": float(f"{new_avg:.4f}")
                    }
                else:
                    # Rates are already in the 1 FOREIGN_CURRENCY = X ZWG format
                    rates[currency_code] = {
                        "bid": float(f"{original_bid:.4f}"),
                        "ask": float(f"{original_ask:.4f}"),
                        "avg": float(f"{original_avg:.4f}")
                    }
                # --- NEW FIX ENDS HERE ---

        return {
            "success": True,
            "date": formatted_date,
            "base": "ZWG", # Added for consistency with API response
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
            "date": data["date"], # This is now already YYYY-MM-DD
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
            print(f"   {currency}: Bid={rate['bid']:.4f}, Ask={rate['ask']:.4f}, Avg={rate['avg']:.4f}")

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
