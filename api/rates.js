const clientPromise = require('../lib/mongodb');

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  const { date, currency, period = '1d' } = req.query;

  try {
    const db = (await clientPromise).db('rbz_rates');
    const col = db.collection('daily_rates');

    const doc = date
    ? await col.findOne({ date })
    : await col.findOne({}, { sort: { date_parsed: -1 } });

    if (!doc) return res.status(404).json({ success: false, error: "No data" });

    const days = { '1d': 1, '7d': 7, '30d': 30, '1y': 365 }[period] || 1;
    const compareDate = new Date(new Date(doc.date_parsed).getTime() - (days * 86400000));
    const pastDoc = await col.findOne({ date_parsed: { $lte: compareDate } }, { sort: { date_parsed: -1 } });

    const rates = {};
    for (const [code, val] of Object.entries(doc.rates)) {
      if (currency && !code.includes(currency.toUpperCase())) continue;
      const pastAvg = pastDoc?.rates[code]?.avg;
      rates[code] = {
        ...val,
        percent_change: pastAvg ? parseFloat(((val.avg - pastAvg) / pastAvg * 100).toFixed(2)) : 0
      };
    }

    res.json({
      success: true,
      base: "ZWG",
      date: doc.date,
      last_updated: doc.scraped_at,
      rates
    });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message });
  }
};
