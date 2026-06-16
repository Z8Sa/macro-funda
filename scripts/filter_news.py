"""
filter_news.py
Menyaring berita dari NewsAPI dan menghitung skor sentimen untuk XAUUSD
"""

import os
import json
import pandas as pd
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re
from collections import Counter

load_dotenv()
NEWS_API_KEY = os.getenv('NEWS_API_KEY')

# ============ DAFTAR KATA KUNCI ============
BULLISH_KEYWORDS = [
    'perang', 'konflik', 'ketegangan', 'geopolitik', 'krisis',
    'bank sentral beli emas', 'cadangan emas', 'inflasi', 
    'utang pemerintah', 'defisit', 'pemotongan suku bunga',
    'dovish', 'resesi', 'pasar bear', 'kejatuhan saham',
    'devaluasi', 'ketidakpastian', 'safe haven', 'lindung nilai'
]

BEARISH_KEYWORDS = [
    'kenaikan suku bunga', 'hawkish', 'the fed', 'federal reserve',
    'penguatan dolar', 'dxy', 'data as kuat', 'nonfarm payroll',
    'cpi', 'inflasi turun', 'pemulihan ekonomi', 'optimisme',
    'pasar bull', 'risk on', 'taper', 'quantitative tightening',
    'yield naik', 'treasury yield'
]

# Sumber yang diabaikan (sering clickbait)
IGNORED_SOURCES = [
    'dailymail.co.uk', 'thesun.co.uk', 'mirror.co.uk',
    'seekingalpha.com', 'zerohedge.com'
]

# Sumber dengan bobot lebih tinggi
TRUSTED_SOURCES = {
    'reuters.com': 1.5,
    'bloomberg.com': 1.5,
    'ft.com': 1.5,
    'wsj.com': 1.5,
    'cnbc.com': 1.2,
    'forexfactory.com': 1.2,
    'fxstreet.com': 1.2,
}

def get_news_from_api(days_back=3):
    """Ambil berita terbaru dari NewsAPI"""
    from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    # Query spesifik untuk emas
    queries = [
        'gold OR emas',
        'Federal Reserve OR The Fed',
        'dollar OR dolar',
        'inflation OR inflasi',
        'geopolitical OR geopolitik'
    ]
    
    all_articles = []
    
    for q in queries:
        url = 'https://newsapi.org/v2/everything'
        params = {
            'q': q,
            'from': from_date,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 50,
            'apiKey': NEWS_API_KEY
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if data.get('status') == 'ok':
                for article in data.get('articles', []):
                    source = article.get('source', {}).get('name', '').lower()
                    url_source = article.get('url', '').lower()
                    if any(ignored in url_source for ignored in IGNORED_SOURCES):
                        continue
                    all_articles.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'content': article.get('content', ''),
                        'source': source,
                        'url': article.get('url', ''),
                        'publishedAt': article.get('publishedAt', ''),
                        'query': q
                    })
        except Exception as e:
            print(f"Error query {q}: {e}")
    
    return all_articles

def clean_text(text):
    """Bersihkan teks untuk analisis"""
    if not text:
        return ""
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()

def calculate_news_score(article):
    """Hitung skor sentimen untuk satu artikel"""
    text = clean_text(article['title'] + ' ' + (article['description'] or ''))
    words = text.split()
    
    bullish_count = 0
    bearish_count = 0
    
    for keyword in BULLISH_KEYWORDS:
        if keyword in text:
            bullish_count += 1
    
    for keyword in BEARISH_KEYWORDS:
        if keyword in text:
            bearish_count += 1
    
    source_weight = 1.0
    for trusted, weight in TRUSTED_SOURCES.items():
        if trusted in article['source']:
            source_weight = weight
            break
    
    raw_score = bullish_count - bearish_count
    
    has_gold = 'gold' in text or 'emas' in text
    if has_gold:
        raw_score = raw_score * 1.5
    
    final_score = raw_score * source_weight
    
    return {
        'score': final_score,
        'bullish': bullish_count,
        'bearish': bearish_count,
        'has_gold': has_gold,
        'source_weight': source_weight
    }

def main():
    print("[INFO] Mengambil berita terbaru...")
    articles = get_news_from_api(days_back=3)
    
    if not articles:
        print("[WARNING] Tidak ada berita yang ditemukan.")
        return
    
    print(f"[OK] {len(articles)} artikel ditemukan")
    
    scored_articles = []
    for article in articles:
        score_info = calculate_news_score(article)
        if score_info['score'] != 0:
            article['score'] = score_info['score']
            article['bullish_count'] = score_info['bullish']
            article['bearish_count'] = score_info['bearish']
            article['has_gold'] = score_info['has_gold']
            scored_articles.append(article)
    
    print(f"[INFO] {len(scored_articles)} artikel memiliki skor relevan")
    
    df = pd.DataFrame(scored_articles)
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['publishedAt']).dt.date
        
        daily_sentiment = df.groupby('date').agg({
            'score': ['mean', 'sum', 'count'],
            'bullish_count': 'sum',
            'bearish_count': 'sum'
        }).reset_index()
        
        daily_sentiment.columns = ['date', 'avg_score', 'total_score', 'article_count', 'bullish', 'bearish']
        daily_sentiment['sentiment_label'] = daily_sentiment['avg_score'].apply(
            lambda x: 'BULLISH' if x > 0.5 else ('BEARISH' if x < -0.5 else 'NEUTRAL')
        )
        
        os.makedirs('data', exist_ok=True)
        daily_sentiment.to_parquet('data/news_sentiment.parquet', index=False)
        
        top_articles = df.nlargest(10, 'score')[['title', 'source', 'score', 'url', 'date']]
        top_articles.to_csv('data/top_news.csv', index=False)
        
        print(f"\n[OK] Sentimen berita disimpan di data/news_sentiment.parquet")
        print(f"[INFO] Periode: {daily_sentiment['date'].min()} sampai {daily_sentiment['date'].max()}")
        print(f"[INFO] Rata-rata skor hari ini: {daily_sentiment['avg_score'].iloc[-1]:.2f}")
        print(f"[INFO] Sentimen hari ini: {daily_sentiment['sentiment_label'].iloc[-1]}")
    else:
        print("[WARNING] Tidak ada data sentimen yang dihasilkan")

if __name__ == "__main__":
    main()