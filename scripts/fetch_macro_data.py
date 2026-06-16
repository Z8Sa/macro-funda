"""
fetch_macro_data.py - VERSI LENGKAP
Mengambil data makro dengan interval daily untuk analisis perubahan
Sumber: FRED, Yahoo Finance, Twelve Data
"""

import os
import json
import pandas as pd
import numpy as np
from fredapi import Fred
import yfinance as yf
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

load_dotenv()
FRED_API_KEY = os.getenv('FRED_API_KEY')
TWELVEDATA_API_KEY = os.getenv('TWELVEDATA_API_KEY')

def fetch_fred_data(fred, series_id, name, start_date='2023-01-01'):
    """Ambil data dari FRED dengan periode yang cukup"""
    try:
        data = fred.get_series(series_id, observation_start=start_date)
        df = pd.DataFrame(data, columns=[name])
        df.index.name = 'date'
        df.index = df.index.tz_localize(None)
        return df
    except Exception as e:
        print(f"[ERROR] Gagal mengambil {series_id}: {e}")
        return None

def fetch_yahoo_data(symbol, name, start_date='2023-01-01'):
    """Ambil data harian dari Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, interval='1d')
        if not df.empty:
            df = df[['Close']].rename(columns={'Close': name})
            df.index.name = 'date'
            df.index = df.index.tz_localize(None)
            return df
    except Exception as e:
        print(f"[ERROR] Gagal mengambil {symbol}: {e}")
    return None

def fetch_gold_twelvedata(interval='1day', outputsize=365):
    """
    Ambil data XAUUSD harian dari Twelve Data
    interval: '1day' untuk data harian
    outputsize: 365 untuk 1 tahun
    """
    if not TWELVEDATA_API_KEY or TWELVEDATA_API_KEY == 'your_twelvedata_api_key_here':
        print("[WARNING] Twelve Data API Key tidak valid.")
        return None
    
    url = "https://api.twelvedata.com/time_series"
    params = {
        'symbol': 'XAU/USD',
        'interval': interval,
        'apikey': TWELVEDATA_API_KEY,
        'outputsize': outputsize,
        'format': 'JSON'
    }
    
    try:
        print(f"[INFO] Mengambil data XAUUSD dari Twelve Data (interval: {interval})...")
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if 'values' not in data:
            print(f"[ERROR] Twelve Data error: {data.get('message', 'Unknown error')}")
            return None
        
        df = pd.DataFrame(data['values'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        df = df.astype(float)
        df = df[['close']].rename(columns={'close': 'xauusd'})
        df.index.name = 'date'
        df.index = df.index.tz_localize(None)
        
        print(f"[OK] Twelve Data berhasil: {len(df)} baris (terakhir: {df.index[-1].strftime('%Y-%m-%d')}, harga: {df['xauusd'].iloc[-1]:.2f})")
        return df
        
    except Exception as e:
        print(f"[ERROR] Twelve Data error: {e}")
        return None

def main():
    print("="*60)
    print("DATA MAKRO FUNDAMENTAL DASHBOARD (HISTORIS)")
    print("="*60)
    print("[INFO] Memulai pengambilan data historis...")
    
    # CEK API KEYS
    if not FRED_API_KEY or FRED_API_KEY == 'your_fred_api_key_here':
        print("[WARNING] FRED API Key tidak valid.")
        fred = None
    else:
        fred = Fred(api_key=FRED_API_KEY)
        print("[OK] FRED API Key valid")
    
    all_data = {}
    
    # === 1. DATA DARI FRED (HISTORIS) ===
    if fred is not None:
        print("\n--- Mengambil data dari FRED ---")
        fred_data = {
            'FEDFUNDS': 'fed_funds_rate',
            'CPIAUCSL': 'cpi',
            'UNRATE': 'unemployment',
            'DGS10': 'treasury_10y',
            'M2SL': 'money_supply',
            'DTWEXBGS': 'dxy_fred',
        }
        
        for series_id, name in fred_data.items():
            df = fetch_fred_data(fred, series_id, name, start_date='2023-01-01')
            if df is not None and not df.empty:
                all_data[name] = df
                print(f"[OK] {name} berhasil diambil")
    
    # === 2. DATA DARI YAHOO FINANCE (DXY) ===
    print("\n--- Mengambil data dari Yahoo Finance ---")
    dxy_data = fetch_yahoo_data('DX-Y.NYB', 'dxy', start_date='2023-01-01')
    if dxy_data is not None and not dxy_data.empty:
        all_data['dxy'] = dxy_data
        print("[OK] dxy berhasil diambil")
    
    # === 3. DATA XAUUSD DARI TWELVE DATA (HARIAN) ===
    print("\n--- Mengambil data XAUUSD ---")
    gold_data = fetch_gold_twelvedata(interval='1day', outputsize=365)
    if gold_data is not None and not gold_data.empty:
        all_data['xauusd'] = gold_data
        print(f"[OK] xauusd berhasil diambil")
    else:
        print("[INFO] Fallback ke Yahoo Finance...")
        gold_data = fetch_yahoo_data('GC=F', 'xauusd', start_date='2023-01-01')
        if gold_data is not None and not gold_data.empty:
            all_data['xauusd'] = gold_data
            print("[OK] xauusd dari Yahoo Finance berhasil diambil")
    
    # === 4. GABUNGKAN SEMUA DATA ===
    if not all_data:
        print("[ERROR] Tidak ada data yang berhasil diambil!")
        return
    
    print("\n--- Menggabungkan data ---")
    
    # Gabungkan dengan outer join
    all_indices = sorted(set().union(*[set(df.index) for df in all_data.values()]))
    combined_df = pd.DataFrame(index=all_indices)
    
    for name, df in all_data.items():
        combined_df = combined_df.join(df, how='left')
    
    # Resample ke daily (pastikan semua data daily)
    combined_df = combined_df.resample('D').last()
    
    # Forward fill untuk data yang hilang
    combined_df = combined_df.ffill()
    
    # === 5. TAMBAHKAN PERHITUNGAN PERUBAHAN ===
    print("--- Menambahkan perhitungan perubahan ---")
    for col in combined_df.columns:
        if col in ['xauusd', 'dxy', 'treasury_10y', 'cpi']:
            combined_df[f'{col}_change_1d'] = combined_df[col].pct_change() * 100
            combined_df[f'{col}_change_5d'] = combined_df[col].pct_change(periods=5) * 100
            combined_df[f'{col}_change_20d'] = combined_df[col].pct_change(periods=20) * 100
    
    # === 6. SIMPAN DATA ===
    os.makedirs('data', exist_ok=True)
    combined_df.to_parquet('data/macro_data.parquet')
    print("[OK] Data disimpan: data/macro_data.parquet")
    
    # === 7. SIMPAN DATA TERAKHIR ===
    if not combined_df.empty:
        latest_data = combined_df.iloc[-1:].reset_index()
        first_col = latest_data.columns[0]
        if first_col != 'date':
            latest_data = latest_data.rename(columns={first_col: 'date'})
        latest_data['date'] = latest_data['date'].dt.strftime('%Y-%m-%d')
        latest_json = latest_data.to_dict(orient='records')[0]
        
        with open('data/latest_macro.json', 'w') as f:
            json.dump(latest_json, f, indent=2, default=str)
        
        print("[OK] Data terakhir disimpan: data/latest_macro.json")
        
        # === 8. CETAK RINGKASAN ===
        print("\n" + "="*60)
        print("RINGKASAN DATA")
        print("="*60)
        print(f"Total baris data: {len(combined_df)}")
        print(f"Tanggal terakhir: {latest_json['date']}")
        print(f"Harga Emas (XAUUSD): ${latest_json.get('xauusd', 'N/A')}")
        print(f"Perubahan 1 hari: {latest_json.get('xauusd_change_1d', 'N/A')}%")
        print(f"Perubahan 5 hari: {latest_json.get('xauusd_change_5d', 'N/A')}%")
        print(f"DXY: {latest_json.get('dxy', 'N/A')}")
        print(f"DXY 5D Change: {latest_json.get('dxy_change_5d', 'N/A')}%")
        print(f"Fed Funds Rate: {latest_json.get('fed_funds_rate', 'N/A')}%")
        print(f"CPI: {latest_json.get('cpi', 'N/A')}")
        print(f"CPI 5D Change: {latest_json.get('cpi_change_5d', 'N/A')}%")
        print(f"Treasury 10Y: {latest_json.get('treasury_10y', 'N/A')}%")
        print("="*60)

if __name__ == "__main__":
    main()