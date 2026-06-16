# Macro Dashboard XAUUSD

Professional macroeconomic analysis dashboard for XAUUSD (Gold), combining macroeconomic indicators, market sentiment, and automated signal generation.

## Live Dashboard

Dashboard dapat diakses melalui:

**https://macro-funda-y78fxheadaexww3qvfmygp.streamlit.app/**

---

## Quick Start

### Cara Update Data Dashboard

Data dashboard tidak diperbarui secara otomatis dari Streamlit. Untuk memperbarui data terbaru:

1. Buka repository GitHub.
2. Klik tab **Actions**.
3. Pilih workflow **Macro Dashboard XAUUSD** di panel sebelah kiri.
4. Klik tombol **Run workflow** (warna hijau).
5. Klik **Run workflow** untuk memulai proses.
6. Tunggu sekitar **1-2 menit** hingga status berubah menjadi **Success**.
7. Setelah workflow selesai, buka dashboard:

https://macro-funda-y78fxheadaexww3qvfmygp.streamlit.app/

Dashboard akan menampilkan data, sentimen, dan sinyal terbaru.

---

## What This Project Does

Sistem ini mengumpulkan dan menganalisis:

* Federal Funds Rate
* CPI (Inflation)
* Unemployment Rate
* Treasury Yield 10Y
* Money Supply (M2)
* Dollar Index (DXY)
* XAUUSD (Gold Price)
* News Sentiment

Kemudian menghasilkan:

* BUY Signal
* SELL Signal
* NEUTRAL Signal
* Composite Macro Score
* Market Bias Analysis

---

## Workflow

```text
GitHub Actions
        ↓
Fetch Macro Data
        ↓
News Sentiment Analysis
        ↓
Generate Signals
        ↓
Save Results
        ↓
Update Dashboard
```

---

## Project Structure

```text
macro_dashboard/
├── .github/
│   └── workflows/
│       └── daily_update.yml
│
├── scripts/
│   ├── fetch_macro_data.py
│   ├── filter_news.py
│   ├── generate_signals.py
│   └── run_all.py
│
├── dashboard/
│   └── app.py
│
├── data/
│
├── requirements.txt
└── README.md
```

---

## Local Installation

Clone repository:

```bash
git clone https://github.com/Z8Sa/macro-funda.git
cd macro-funda
```

Create virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` file:

```env
FRED_API_KEY=your_fred_api_key
NEWS_API_KEY=your_newsapi_key
TWELVEDATA_API_KEY=your_twelvedata_key
```

Run pipeline:

```bash
python scripts/run_all.py
```

Run dashboard:

```bash
streamlit run dashboard/app.py
```

---

## Disclaimer

This project is intended for educational and research purposes only.

It does not constitute financial advice, investment advice, or trading recommendations.

Always conduct your own analysis before making trading decisions.

---

## Author

Rafi

GitHub: https://github.com/Z8Sa
