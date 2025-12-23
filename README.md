# 🇿🇼 RBZ Rates API

Free, open-source API for Zimbabwe exchange rates from the Reserve Bank of Zimbabwe.

![License](https://img.shields.io/badge/license-MIT-green)
![Vercel](https://img.shields.io/badge/deployed%20on-Vercel-black)

## Features

- ✅ **Daily Updates** - Automated scraping via GitHub Actions
- ✅ **Historical Data** - Query rates for any past date
- ✅ **Percentage Changes** - Calculate rate changes over custom periods
- ✅ **Free & Open Source** - No API keys required
- ✅ **Fast & Reliable** - Deployed on Vercel Edge

## API Endpoints

### Get Current Rates

```
GET /api/rates
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `date` | string | Specific date (YYYY-MM-DD) |
| `currency` | string | Filter by currency (e.g., USD) |

**Example Response:**
```json
{
  "success": true,
  "date": "2025-01-15",
  "source": "rbz.co.zw",
  "rates": {
    "USD": { "bid": 24.9, "ask": 25.1, "avg": 25.0 },
    "GBP": { "bid": 31.4, "ask": 31.6, "avg": 31.5 }
  }
}
```

### Get Rate Changes

```
GET /api/changes
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `period` | string | Preset: `1d`, `7d`, `30d`, `90d`, `1y` |
| `from` | string | Custom start date (YYYY-MM-DD) |
| `to` | string | Custom end date (YYYY-MM-DD) |
| `currency` | string | Filter by currency |

**Example Response:**
```json
{
  "success": true,
  "period": "7d",
  "from": "2024-01-08",
  "to": "2024-01-15",
  "changes": {
    "USD": {
      "start": { "date": "2024-01-08", "rate": 24.5 },
      "end": { "date": "2024-01-15", "rate": 25.0 },
      "change": 0.5,
      "percent_change": 2.04,
      "direction": "up"
    }
  }
}
```

### Get Historical Rates

```
GET /api/historical
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from` | string | - | Start date (YYYY-MM-DD) |
| `to` | string | - | End date (YYYY-MM-DD) |
| `currency` | string | - | Filter by currency |
| `limit` | number | 30 | Max results (max: 365) |
| `skip` | number | 0 | Offset for pagination |

### List Available Dates

```
GET /api/dates
```

### List Available Currencies

```
GET /api/currencies
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/rbz-rates-api.git
cd rbz-rates-api
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

## Deployment

### Deploy to Vercel

1. Push to GitHub
2. Import project in [Vercel](https://vercel.com)
3. Add environment variable:
   - `MONGODB_URI` = your MongoDB connection string
4. Deploy!

### Set Up GitHub Actions

1. Go to **Settings > Secrets and variables > Actions**
2. Add secret:
   - `MONGODB_URI` = your MongoDB connection string
3. The scraper runs daily at 10:00 UTC

To run manually: **Actions > Scrape RBZ Rates > Run workflow**

## Project Structure

```
rbz-rates-api/
├── .github/workflows/
│   └── scrape.yml          # Daily scraper workflow
├── api/
│   ├── rates.js            # Current/dated rates
│   ├── changes.js          # Percentage changes
│   ├── historical.js       # Historical data
│   ├── dates.js            # Available dates
│   └── currencies.js       # Available currencies
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
// Fetch latest rates
const response = await fetch('https://your-app.vercel.app/api/rates');
const { rates } = await response.json();
console.log(`USD Rate: ${rates.USD.avg}`);

// Get 30-day change for USD
const changes = await fetch('https://your-app.vercel.app/api/changes?period=30d&currency=USD');
const data = await changes.json();
console.log(`USD changed ${data.changes.USD.percent_change}% over 30 days`);
```

### Python

```python
import requests

# Get rates for specific date
response = requests.get(
    'https://your-app.vercel.app/api/rates',
    params={'date': '2024-01-15'}
)
data = response.json()
print(data['rates'])
```

### cURL

```bash
# Latest rates
curl https://your-app.vercel.app/api/rates

# Historical with date range
curl "https://your-app.vercel.app/api/historical?from=2024-01-01&to=2024-01-31"
```

## Rate Limits

No rate limits currently. Please be respectful and cache responses when possible.

## Data Source

All exchange rate data is sourced from the [Reserve Bank of Zimbabwe](https://www.rbz.co.zw) official website.

