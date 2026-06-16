"""
generate_signals.py
Menggabungkan data makro dan sentimen berita untuk menghasilkan sinyal trading
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from macro_filters import MacroFilter
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# FUNGSI LOAD DATA
# ============================================================

def load_data():
    """Muat data makro dan sentimen"""
    try:
        macro_df = pd.read_parquet('data/macro_data.parquet')
        print(f"[INFO] Data makro dimuat: {len(macro_df)} baris")
        print(f"[INFO] Kolom makro: {list(macro_df.columns)}")
    except Exception as e:
        print(f"[ERROR] Gagal memuat data makro: {e}")
        return None, None
    
    try:
        sentiment_df = pd.read_parquet('data/news_sentiment.parquet')
        sentiment_df['date'] = pd.to_datetime(sentiment_df['date'])
        sentiment_df.set_index('date', inplace=True)
        print(f"[INFO] Data sentimen dimuat: {len(sentiment_df)} baris")
    except Exception as e:
        print(f"[INFO] Data sentimen belum tersedia: {e}")
        sentiment_df = None
    
    return macro_df, sentiment_df

# ============================================================
# FUNGSI AMBIL NILAI DENGAN AMAN
# ============================================================

def safe_get_value(df, col_name):
    """
    Ambil nilai dari kolom DataFrame dengan aman
    Mengatasi NaN, None, dan kolom yang tidak ada
    """
    try:
        if col_name not in df.columns:
            return None
        val = df[col_name].values[0]
        if pd.isna(val) or np.isnan(val):
            return None
        return val
    except (IndexError, KeyError, ValueError, TypeError):
        return None

def safe_get_series(df, col_name):
    """
    Ambil series dari kolom DataFrame dengan aman
    Menghapus NaN sebelum dikembalikan
    """
    try:
        if col_name not in df.columns:
            return pd.Series(dtype=float)
        series = df[col_name].dropna()
        return series
    except:
        return pd.Series(dtype=float)

def safe_pct_change(series):
    """
    Hitung persentase perubahan terakhir dengan aman
    """
    try:
        if series.empty or len(series) < 2:
            return 0.0
        pct = series.pct_change().iloc[-1]
        if pd.isna(pct) or np.isnan(pct) or not np.isfinite(pct):
            return 0.0
        return pct
    except:
        return 0.0

# ============================================================
# FUNGSI UTAMA GENERATE SIGNAL
# ============================================================

def generate_signal(macro_df, sentiment_df, lookback=60):
    """
    Menghasilkan sinyal berdasarkan kombinasi indikator makro dan sentimen
    """
    
    print("\n" + "="*60)
    print("PROSES GENERATE SIGNAL")
    print("="*60)
    
    # === 1. FILTER MAKRO PROFESIONAL ===
    print("\n" + "="*60)
    print("MACRO FILTERS PROFESIONAL")
    print("="*60)
    
    filter_macro = MacroFilter(macro_df)
    macro_result = filter_macro.run_all_filters()
    
    # Ambil composite score dari filter makro
    macro_composite_score = macro_result['composite_score']
    macro_signal = macro_result['signal']
    macro_confidence = macro_result['confidence']
    macro_details = macro_result['details']
    
    # Simpan hasil filter makro ke file
    macro_summary = filter_macro.get_summary()
    os.makedirs('data', exist_ok=True)
    with open('data/macro_filters_summary.json', 'w') as f:
        json.dump(macro_summary, f, indent=2, default=str)
    print("\n[OK] Filter makro disimpan: data/macro_filters_summary.json")
    
    # === 2. AMBIL DATA TERAKHIR ===
    latest = macro_df.iloc[-1:].copy()
    print(f"\n[DEBUG] Data terakhir index: {latest.index[0]}")
    
    # === 3. AMBIL SEMUA NILAI DENGAN AMAN ===
    gold_price = safe_get_value(latest, 'xauusd')
    fed_rate = safe_get_value(latest, 'fed_funds_rate')
    cpi = safe_get_value(latest, 'cpi')
    dxy = safe_get_value(latest, 'dxy')
    treasury_10y = safe_get_value(latest, 'treasury_10y')
    unemployment = safe_get_value(latest, 'unemployment')
    
    print(f"\n[DEBUG] Nilai terakhir:")
    print(f"   - gold_price: {gold_price}")
    print(f"   - fed_rate: {fed_rate}")
    print(f"   - cpi: {cpi}")
    print(f"   - dxy: {dxy}")
    print(f"   - treasury_10y: {treasury_10y}")
    print(f"   - unemployment: {unemployment}")
    
    # === 4. HITUNG ROLLING AVERAGE ===
    macro_window = macro_df.tail(lookback).copy()
    
    # Rata-rata Fed Funds Rate
    fed_rate_ma = None
    if 'fed_funds_rate' in macro_window:
        fed_series = safe_get_series(macro_window, 'fed_funds_rate')
        if not fed_series.empty:
            fed_rate_ma = fed_series.mean()
    
    # Perubahan CPI (persentase)
    cpi_change = 0.0
    if 'cpi' in macro_window:
        cpi_series = safe_get_series(macro_window, 'cpi')
        cpi_change = safe_pct_change(cpi_series)
    
    # Perubahan DXY (persentase)
    dxy_change = 0.0
    if 'dxy' in macro_window:
        dxy_series = safe_get_series(macro_window, 'dxy')
        dxy_change = safe_pct_change(dxy_series)
    
    # Perubahan Treasury 10Y (persentase)
    treasury_change = 0.0
    if 'treasury_10y' in macro_window:
        treasury_series = safe_get_series(macro_window, 'treasury_10y')
        treasury_change = safe_pct_change(treasury_series)
    
    print(f"\n[DEBUG] Perhitungan rolling ({lookback} hari):")
    print(f"   - fed_rate_ma: {fed_rate_ma}")
    print(f"   - cpi_change: {cpi_change:.6f} ({cpi_change*100:.4f}%)")
    print(f"   - dxy_change: {dxy_change:.6f} ({dxy_change*100:.4f}%)")
    print(f"   - treasury_change: {treasury_change:.6f} ({treasury_change*100:.4f}%)")
    
    # === 5. SENTIMEN BERITA ===
    sentiment_score = 0.0
    if sentiment_df is not None and not sentiment_df.empty:
        try:
            recent_sentiment = sentiment_df.tail(3)['avg_score'].dropna()
            if not recent_sentiment.empty:
                sentiment_score = recent_sentiment.mean()
                sentiment_score = max(-1.0, min(1.0, sentiment_score))
        except Exception as e:
            print(f"[WARNING] Error sentimen: {e}")
            sentiment_score = 0.0
    
    print(f"\n[DEBUG] Sentimen:")
    print(f"   - sentiment_score: {sentiment_score:.4f}")
    
    # === 6. LOGIKA SINYAL ===
    total_score = 0
    components_detail = []
    
    # Faktor 1: Suku Bunga (Fed Funds Rate)
    if fed_rate is not None and fed_rate_ma is not None:
        if fed_rate < fed_rate_ma * 0.98:
            total_score += 2
            components_detail.append("Fed Rate: Strong Bullish (turun)")
            print(f"[INFO] Fed Rate: Strong Bullish ({fed_rate:.2f} < {fed_rate_ma:.2f})")
        elif fed_rate < fed_rate_ma:
            total_score += 1
            components_detail.append("Fed Rate: Bullish")
            print(f"[INFO] Fed Rate: Bullish ({fed_rate:.2f} < {fed_rate_ma:.2f})")
        elif fed_rate > fed_rate_ma * 1.02:
            total_score -= 2
            components_detail.append("Fed Rate: Strong Bearish (naik)")
            print(f"[INFO] Fed Rate: Strong Bearish ({fed_rate:.2f} > {fed_rate_ma:.2f})")
        elif fed_rate > fed_rate_ma:
            total_score -= 1
            components_detail.append("Fed Rate: Bearish")
            print(f"[INFO] Fed Rate: Bearish ({fed_rate:.2f} > {fed_rate_ma:.2f})")
        else:
            components_detail.append("Fed Rate: Netral")
            print(f"[INFO] Fed Rate: Netral ({fed_rate:.2f} = {fed_rate_ma:.2f})")
    else:
        print(f"[INFO] Fed Rate: Data tidak tersedia")
    
    # Faktor 2: Inflasi (CPI)
    if cpi_change > 0.005:
        total_score += 1
        components_detail.append(f"CPI: Bullish (naik {cpi_change*100:.2f}%)")
        print(f"[INFO] CPI: Bullish (naik {cpi_change*100:.2f}%)")
    elif cpi_change < -0.005:
        total_score -= 1
        components_detail.append(f"CPI: Bearish (turun {cpi_change*100:.2f}%)")
        print(f"[INFO] CPI: Bearish (turun {cpi_change*100:.2f}%)")
    else:
        components_detail.append(f"CPI: Netral ({cpi_change*100:.2f}%)")
        print(f"[INFO] CPI: Netral ({cpi_change*100:.2f}%)")
    
    # Faktor 3: Dolar Index (DXY)
    if dxy_change < -0.003:
        total_score += 1
        components_detail.append(f"DXY: Bullish (melemah {dxy_change*100:.2f}%)")
        print(f"[INFO] DXY: Bullish (melemah {dxy_change*100:.2f}%)")
    elif dxy_change > 0.003:
        total_score -= 1
        components_detail.append(f"DXY: Bearish (menguat {dxy_change*100:.2f}%)")
        print(f"[INFO] DXY: Bearish (menguat {dxy_change*100:.2f}%)")
    else:
        components_detail.append(f"DXY: Netral ({dxy_change*100:.2f}%)")
        print(f"[INFO] DXY: Netral ({dxy_change*100:.2f}%)")
    
    # Faktor 4: Sentimen Berita
    if sentiment_score > 0.3:
        total_score += 1
        components_detail.append(f"Sentimen: Bullish ({sentiment_score:.2f})")
        print(f"[INFO] Sentimen: Bullish ({sentiment_score:.2f})")
    elif sentiment_score < -0.3:
        total_score -= 1
        components_detail.append(f"Sentimen: Bearish ({sentiment_score:.2f})")
        print(f"[INFO] Sentimen: Bearish ({sentiment_score:.2f})")
    else:
        components_detail.append(f"Sentimen: Netral ({sentiment_score:.2f})")
        print(f"[INFO] Sentimen: Netral ({sentiment_score:.2f})")
    
    # === 7. KESIMPULAN ===
    print(f"\n[INFO] Total Score: {total_score}")
    
    if total_score >= 3:
        signal = "STRONG BUY"
        confidence = min(100, abs(total_score) / 4 * 100)
    elif total_score >= 1:
        signal = "BUY"
        confidence = min(100, abs(total_score) / 4 * 100)
    elif total_score <= -3:
        signal = "STRONG SELL"
        confidence = min(100, abs(total_score) / 4 * 100)
    elif total_score <= -1:
        signal = "SELL"
        confidence = min(100, abs(total_score) / 4 * 100)
    else:
        signal = "NEUTRAL"
        confidence = 0
    
    # === 8. HASIL AKHIR ===
    result = {
        'signal': signal,
        'confidence': round(confidence, 2),
        'total_score': total_score,
        'components': {
            'fed_rate': round(fed_rate, 2) if fed_rate else None,
            'fed_rate_ma': round(fed_rate_ma, 2) if fed_rate_ma else None,
            'cpi': round(cpi, 2) if cpi else None,
            'cpi_change': round(cpi_change * 100, 2) if cpi_change else None,
            'dxy': round(dxy, 2) if dxy else None,
            'dxy_change': round(dxy_change * 100, 2) if dxy_change else None,
            'treasury_10y': round(treasury_10y, 2) if treasury_10y else None,
            'treasury_change': round(treasury_change * 100, 2) if treasury_change else None,
            'unemployment': round(unemployment, 2) if unemployment else None,
            'sentiment_score': round(sentiment_score, 2),
        },
        'components_detail': components_detail,
        'timestamp': datetime.now().isoformat(),
        'gold_price': round(gold_price, 2) if gold_price else None,
        # ===== INI YANG BARU: TAMBAHKAN HASIL FILTER MAKRO =====
        'macro_filters': macro_summary
    }
    
    return result

# ============================================================
# FUNGSI MAIN
# ============================================================

def main():
    print("\n" + "="*60)
    print("GENERATE SIGNAL XAUUSD")
    print("="*60)
    print("[INFO] Menghasilkan sinyal trading...")
    
    # Load data
    macro_df, sentiment_df = load_data()
    
    if macro_df is None or macro_df.empty:
        print("[WARNING] Data makro tidak ditemukan. Jalankan fetch_macro_data.py terlebih dahulu.")
        return
    
    # Generate signal
    result = generate_signal(macro_df, sentiment_df)
    
    # Simpan
    os.makedirs('data', exist_ok=True)
    with open('data/signal.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print("\n[OK] Sinyal disimpan: data/signal.json")
    
    # ============================================================
    # CETAK HASIL
    # ============================================================
    print("\n" + "="*60)
    print("SINYAL TRADING XAUUSD")
    print("="*60)
    print(f"Sinyal: {result['signal']}")
    print(f"Confidence: {result['confidence']}%")
    print(f"Total Score: {result['total_score']}")
    print(f"Harga Emas: ${result['gold_price']}")
    print("\nKomponen:")
    for key, value in result['components'].items():
        if value is not None:
            print(f"   - {key}: {value}")
    print("\nDetail Faktor:")
    for item in result['components_detail']:
        print(f"   - {item}")
    
    # Cetak filter makro
    if 'macro_filters' in result:
        print("\n" + "="*60)
        print("FILTER MAKRO PROFESIONAL")
        print("="*60)
        macro = result['macro_filters']
        print(f"Composite Score: {macro['composite']['score']:.3f}")
        print(f"Sinyal: {macro['composite']['signal']}")
        print(f"Confidence: {macro['composite']['confidence']}%")
        print("\nTema:")
        for theme, data in macro['themes'].items():
            print(f"   - {theme}: {data['score']:.3f}")
    
    print("="*60)

if __name__ == "__main__":
    main()