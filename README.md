# RBZ Rates API

Free API for Zimbabwe exchange rates from the Reserve Bank of Zimbabwe.

![License](https://img.shields.io/badge/license-MIT-green)
![Vercel](https://img.shields.io/badge/deployed%20on-Vercel-black)

## Features

- ✅ **Daily Updates** - Automated scraping via GitHub Actions
- ✅ **Historical Data** - Query rates for any past date
- ✅ **Flexible Period Comparisons** - Calculate rate changes over custom periods

## API Endpoints

### Get Current or Historical Rates

```
GET /api/rates
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `date` | string | Specific date (YYYY-MM-DD) for historical data |
| `currency` | string | Filter by currency code (e.g., USD) |
| `period` | string | Percentage change period: `1d`, `7d`, `30d`, `1y` (default: `1d`) |

**Example Response:**
```json
{
  "success": true,
  "base": "ZWG",
  "date": "2025-01-15",
  "last_updated": "2025-01-15T08:30:00.000Z",
  "rates": {
    "USD": {
      "bid": 24.9810,
      "ask": 25.3210,
      "avg": 25.1234,
      "percent_change": 1.05
    },
    "ZAR": {
      "bid"	1.5191,
      "ask"	1.5977,
      "avg":	1.5574,
      "percent_change": -0.32
    }
  }
}
```

**Usage Examples:**

```bash
# Get latest rates with 24h change
curl https://localhost:3000/api/rates

# Get rates for specific date
curl https://localhost:3000/api/rates?date=2024-12-25

# Get latest rates with 7-day percentage change
curl https://localhost:3000/api/rates?period=7d

# Filter by currency
curl https://localhost:3000/api/rates?currency=USD

# Combine parameters
curl https://localhost:3000/api/rates?period=30d&currency=USD
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/brendmung//rbz-exchange-rates-api.git
cd rbz-exchange-rates-api
```

### 2. Set Up MongoDB

1. Create a free cluster at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Get your connection string
3. Create `.env` file:

```bash
cp .env.example .env
# Edit .env with your MongoDB URI
```

### 3. Install Dependencies

```bash
npm install
```

### 4. Run Locally

```bash
npm run dev
```

Visit `http://localhost:3000` to see the landing page.

### Set Up GitHub Actions

1. Go to **Settings > Secrets and variables > Actions**
2. Add secret:
   - `MONGODB_URI` = your MongoDB connection string
3. The scraper runs weekdays at 8:00 AM UTC

To run manually: **Actions > Scrape RBZ Rates > Run workflow**

## Project Structure

```
rbz-rates-api/
├── .github/workflows/
│   └── scrape.yml          # Daily scraper workflow
├── api/
│   └── rates.js            # Main API endpoint
├── lib/
│   └── mongodb.js          # Database connection
├── public/
│   └── index.html          # Landing page
├── scraper/
│   ├── scrape.py           # Python scraper
│   └── requirements.txt    # Python deps
├── package.json
├── vercel.json
└── README.md
```

## Usage Examples

### JavaScript/TypeScript

```javascript
// Fetch latest rates with 24h change
const response = await fetch('https://localhost:3000/api/rates');
const { rates } = await response.json();
console.log(`USD Rate: ${rates.USD.avg}`);

// Get 30-day change for USD
const changes = await fetch('https://localhost:3000/api/rates?period=30d&currency=USD');
const data = await changes.json();
console.log(`USD changed ${data.rates.USD.percent_change}% over 30 days`);

// Get historical rates for specific date
const historical = await fetch('https://localhost:3000/api/rates?date=2024-01-15');
const histData = await historical.json();
console.log(`USD on 2024-01-15: ${histData.rates.USD.avg}`);
```

### Python

```python
import requests

# Get latest rates
response = requests.get('https://localhost:3000/api/rates')
data = response.json()
print(data['rates'])

# Get rates for specific date with 7-day change
response = requests.get(
    'https://localhost:3000/api/rates',
    params={'date': '2024-01-15', 'period': '7d'}
)
data = response.json()
print(f"USD: {data['rates']['USD']['avg']} ({data['rates']['USD']['percent_change']}%)")
```

### cURL

```bash
# Latest rates
curl https://localhost:3000/api/rates

# Specific date with 30-day comparison
curl "https://localhost:3000/api/rates?date=2024-01-31&period=30d"

# Filter by currency with yearly change
curl "https://localhost:3000/api/rates?currency=USD&period=1y"
```

## Rate Limits

No rate limits currently. Please be respectful and cache responses when possible.

## Data Source

All exchange rate data is sourced from the [Reserve Bank of Zimbabwe](https://www.rbz.co.zw) official website.

## License

MIT
