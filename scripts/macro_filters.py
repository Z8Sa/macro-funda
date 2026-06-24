"""
macro_filters.py

Tema Ekonomi:
1. Siklus Bisnis
2. Kebijakan Moneter
3. Nilai Tukar & Perdagangan
4. Sentimen Risiko
5. Kondisi Pasar Tenaga Kerja
6. Kredit & Likuiditas

PERIODE YANG DIGUNAKAN:
- Data Harian (XAUUSD, DXY, Treasury): 5D, 20D
- Data Bulanan (CPI, Unemployment): MoM (21 hari), YoY (252 hari)
- Data Mingguan/Bulanan (M2): YoY (252 hari)
- Sahm Rule: 3 bulan (63 hari)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


# ============================================================
# KELAS UTAMA: MacroFilter
# ============================================================

class MacroFilter:
    """
    Filter makro fundamental profesional untuk trading XAUUSD
    """
    
    def __init__(self, macro_df):
        """
        Inisialisasi dengan data makro DataFrame
        
        Parameters:
        - macro_df: DataFrame dari fetch_macro_data.py
        """
        self.df = macro_df.copy()
        self.scores = {}
        self.details = {}
        
    # ============================================================
    # 1. SIKLUS BISNIS
    # ============================================================
    
    def calculate_business_cycle(self):
        """
        Mengukur kekuatan ekonomi riil
        
        Indikator:
        - Gold 5D change (safe haven)
        - Unemployment 3M change (Sahm Rule)
        - Treasury 10Y 20D change (ekonomi)
        
        Logika: Gold naik = risk-off, Unemployment naik = resesi, Yield naik = ekonomi kuat
        """
        print("\n[FILTER] 1. Siklus Bisnis")
        
        score = 0
        details = []
        
        # === A. Gold Change (5 hari - VALID, data harian) ===
        if 'xauusd' in self.df.columns and len(self.df) > 5:
            gold_change = self.df['xauusd'].pct_change(periods=5).iloc[-1]
            if not pd.isna(gold_change):
                if gold_change < -0.01:  # Emas turun >1% dalam 5 hari
                    score += 1
                    details.append(f"Gold turun {gold_change:.2%} -> Risk-On (Bullish)")
                elif gold_change > 0.01:  # Emas naik >1% dalam 5 hari
                    score -= 1
                    details.append(f"Gold naik {gold_change:.2%} -> Safe haven (Bearish)")
                else:
                    details.append(f"Gold netral ({gold_change:.2%})")
                print(f"   Gold 5D: {gold_change:.2%}")
        
        # === B. Unemployment 3M Change (SAHM RULE - 63 hari) ===
        if 'unemployment' in self.df.columns and len(self.df) > 63:
            unemp_current = self.df['unemployment'].iloc[-1]
            unemp_3m_ago = self.df['unemployment'].iloc[-63] if len(self.df) >= 63 else unemp_current
            sahm_rule = unemp_current - unemp_3m_ago
            
            if not pd.isna(sahm_rule):
                if sahm_rule > 0.5:
                    score -= 2
                    details.append(f"Sahm Rule: +{sahm_rule:.1f}% -> Resesi (Bearish)")
                elif sahm_rule > 0.3:
                    score -= 1
                    details.append(f"Unemployment naik {sahm_rule:.1f}% dalam 3 bulan")
                elif sahm_rule < -0.2:
                    score += 1
                    details.append(f"Unemployment turun {sahm_rule:.1f}% dalam 3 bulan -> Ekonomi kuat")
                else:
                    details.append(f"Unemployment stabil ({unemp_current:.1f}%)")
                print(f"   Sahm Rule: {sahm_rule:.1f}%")
        
        # === C. Treasury 10Y 20D Change (VALID, data harian) ===
        if 'treasury_10y' in self.df.columns and len(self.df) > 20:
            yield_change = self.df['treasury_10y'].pct_change(periods=20).iloc[-1]
            if not pd.isna(yield_change):
                if yield_change > 0.02:
                    score += 1
                    details.append(f"Yield naik {yield_change:.2%} -> Ekonomi kuat (Bullish)")
                elif yield_change < -0.02:
                    score -= 1
                    details.append(f"Yield turun {yield_change:.2%} -> Ekonomi lemah (Bearish)")
                else:
                    details.append(f"Yield netral ({yield_change:.2%})")
                print(f"   Treasury 10Y 20D: {yield_change:.2%}")
        
        # Normalisasi score ke -1 s.d 1
        if score > 0:
            final_score = min(1.0, score / 3)
        elif score < 0:
            final_score = max(-1.0, score / 3)
        else:
            final_score = 0.0
        
        self.scores['business_cycle'] = final_score
        self.details['business_cycle'] = {
            'score': final_score,
            'raw_score': score,
            'details': details
        }
        
        print(f"   Final Score: {final_score:.2f}")
        return final_score
    
    # ============================================================
    # 2. KEBIJAKAN MONETER
    # ============================================================
    
    def calculate_monetary_policy(self):
        """
        Menangkap arah kebijakan bank sentral
        
        Indikator:
        - Fed Rate YoY (perubahan tahunan)
        - Treasury 10Y vs MA20 (tren)
        
        Logika: Fed Rate turun = dovish, Treasury turun = dovish
        """
        print("\n[FILTER] 2. Kebijakan Moneter")
        
        score = 0
        details = []
        
        # === A. Fed Rate YoY (252 hari) ===
        if 'fed_funds_rate' in self.df.columns and len(self.df) > 252:
            fed_current = self.df['fed_funds_rate'].iloc[-1]
            fed_1y_ago = self.df['fed_funds_rate'].iloc[-252] if len(self.df) >= 252 else fed_current
            fed_yoy = fed_current - fed_1y_ago
            
            if not pd.isna(fed_yoy):
                if fed_yoy < -0.5:
                    score += 2
                    details.append(f"Fed Rate turun {fed_yoy:.2f}% YoY -> Dovish (Bullish)")
                elif fed_yoy < -0.25:
                    score += 1
                    details.append(f"Fed Rate turun {fed_yoy:.2f}% YoY")
                elif fed_yoy > 0.5:
                    score -= 2
                    details.append(f"Fed Rate naik {fed_yoy:.2f}% YoY -> Hawkish (Bearish)")
                elif fed_yoy > 0.25:
                    score -= 1
                    details.append(f"Fed Rate naik {fed_yoy:.2f}% YoY")
                else:
                    details.append(f"Fed Rate netral YoY ({fed_yoy:.2f}%)")
                print(f"   Fed Rate YoY: {fed_yoy:.2f}%")
        
        # === B. Treasury 10Y vs MA20 (VALID, data harian) ===
        if 'treasury_10y' in self.df.columns and len(self.df) > 20:
            yield_current = self.df['treasury_10y'].iloc[-1]
            yield_20d_ma = self.df['treasury_10y'].tail(20).mean()
            
            if not pd.isna(yield_current) and not pd.isna(yield_20d_ma):
                if yield_current < yield_20d_ma * 0.97:
                    score += 1
                    details.append("Treasury yield turun -> Dovish (Bullish)")
                elif yield_current > yield_20d_ma * 1.03:
                    score -= 1
                    details.append("Treasury yield naik -> Hawkish (Bearish)")
                else:
                    details.append("Treasury yield netral")
                print(f"   Treasury 10Y: {yield_current:.2f}% (MA20: {yield_20d_ma:.2f}%)")
        
        # Normalisasi
        if score > 0:
            final_score = min(1.0, score / 3)
        elif score < 0:
            final_score = max(-1.0, score / 3)
        else:
            final_score = 0.0
        
        self.scores['monetary_policy'] = final_score
        self.details['monetary_policy'] = {
            'score': final_score,
            'raw_score': score,
            'details': details
        }
        
        print(f"   Final Score: {final_score:.2f}")
        return final_score
    
    # ============================================================
    # 3. NILAI TUKAR & PERDAGANGAN
    # ============================================================
    
    def calculate_trade_currency(self):
        """
        Menangkap nilai tukar dan perdagangan
        
        Indikator:
        - DXY 20D change (tren dolar)
        
        Logika: Dolar melemah = bullish untuk emas
        """
        print("\n[FILTER] 3. Nilai Tukar & Perdagangan")
        
        score = 0
        details = []
        
        # === A. DXY 20D Change (VALID, data harian) ===
        if 'dxy' in self.df.columns and len(self.df) > 20:
            dxy_current = self.df['dxy'].iloc[-1]
            dxy_20d_ma = self.df['dxy'].tail(20).mean()
            
            if not pd.isna(dxy_current) and not pd.isna(dxy_20d_ma) and dxy_20d_ma != 0:
                dxy_change = (dxy_current - dxy_20d_ma) / dxy_20d_ma
                
                if dxy_change < -0.01:
                    score += 1
                    details.append(f"DXY turun {dxy_change:.2%} -> Dolar melemah (Bullish)")
                elif dxy_change > 0.01:
                    score -= 1
                    details.append(f"DXY naik {dxy_change:.2%} -> Dolar menguat (Bearish)")
                else:
                    details.append(f"DXY netral ({dxy_change:.2%})")
                print(f"   DXY 20D Change: {dxy_change:.2%}")
        
        # Normalisasi
        if score > 0:
            final_score = min(1.0, score)
        elif score < 0:
            final_score = max(-1.0, score)
        else:
            final_score = 0.0
        
        self.scores['trade_currency'] = final_score
        self.details['trade_currency'] = {
            'score': final_score,
            'raw_score': score,
            'details': details
        }
        
        print(f"   Final Score: {final_score:.2f}")
        return final_score
    
    # ============================================================
    # 4. SENTIMEN RISIKO
    # ============================================================
    
    def calculate_risk_sentiment(self):
        """
        Mencerminkan selera risiko pasar
        
        Indikator:
        - Treasury Volatility Ratio (volatilitas)
        - Credit Spread Z-Score (spread kredit)
        
        Logika: Volatilitas tinggi = risk-off, Spread lebar = risk-off
        """
        print("\n[FILTER] 4. Sentimen Risiko")
        
        score = 0
        details = []
        
        # === A. Treasury Volatility Ratio (VALID, data harian) ===
        if 'treasury_10y' in self.df.columns and len(self.df) > 60:
            treasury_vol = self.df['treasury_10y'].tail(20).std()
            treasury_vol_mean = self.df['treasury_10y'].tail(60).std()
            
            if not pd.isna(treasury_vol) and not pd.isna(treasury_vol_mean) and treasury_vol_mean != 0:
                vol_ratio = treasury_vol / treasury_vol_mean
                
                if vol_ratio > 1.3:
                    score -= 1
                    details.append(f"Volatilitas tinggi (ratio={vol_ratio:.2f}) -> Risk-Off (Bearish)")
                elif vol_ratio < 0.7:
                    score += 1
                    details.append(f"Volatilitas rendah (ratio={vol_ratio:.2f}) -> Risk-On (Bullish)")
                else:
                    details.append(f"Volatilitas netral (ratio={vol_ratio:.2f})")
                print(f"   Treasury Vol Ratio: {vol_ratio:.2f}")
        
        # === B. Credit Spread Z-Score (VALID, data harian) ===
        if 'treasury_10y' in self.df.columns and 'fed_funds_rate' in self.df.columns:
            spread = self.df['treasury_10y'].iloc[-1] - self.df['fed_funds_rate'].iloc[-1]
            spread_mean = (self.df['treasury_10y'] - self.df['fed_funds_rate']).tail(60).mean()
            spread_std = (self.df['treasury_10y'] - self.df['fed_funds_rate']).tail(60).std()
            
            if not pd.isna(spread) and not pd.isna(spread_mean) and spread_std != 0:
                z_score = (spread - spread_mean) / spread_std
                
                if z_score > 1.5:
                    score -= 2
                    details.append(f"Spread sangat lebar (Z={z_score:.1f}) -> Stres (Bearish)")
                elif z_score > 0.5:
                    score -= 1
                    details.append(f"Spread melebar (Z={z_score:.1f}) -> Risk-Off (Bearish)")
                elif z_score < -0.5:
                    score += 1
                    details.append(f"Spread menyempit (Z={z_score:.1f}) -> Risk-On (Bullish)")
                else:
                    details.append(f"Spread netral (Z={z_score:.1f})")
                print(f"   Spread Z-Score: {z_score:.1f}")
        
        # Normalisasi
        if score > 0:
            final_score = min(1.0, score / 2)
        elif score < 0:
            final_score = max(-1.0, score / 2)
        else:
            final_score = 0.0
        
        self.scores['risk_sentiment'] = final_score
        self.details['risk_sentiment'] = {
            'score': final_score,
            'raw_score': score,
            'details': details
        }
        
        print(f"   Final Score: {final_score:.2f}")
        return final_score
    
    # ============================================================
    # 5. KONDISI PASAR TENAGA KERJA
    # ============================================================
    
    def calculate_labor_market(self):
        """
        Indikator utama kesehatan ekonomi
        
        Indikator:
        - Sahm Rule (3 bulan)
        
        Logika: Pengangguran naik >0.5% dalam 3 bulan = resesi
        """
        print("\n[FILTER] 5. Kondisi Pasar Tenaga Kerja")
        
        score = 0
        details = []
        
        # === A. SAHM RULE (3 bulan = 63 hari) ===
        if 'unemployment' in self.df.columns and len(self.df) > 63:
            unemp_current = self.df['unemployment'].iloc[-1]
            unemp_3m_ago = self.df['unemployment'].iloc[-63] if len(self.df) >= 63 else unemp_current
            sahm_rule = unemp_current - unemp_3m_ago
            
            if not pd.isna(sahm_rule):
                if sahm_rule > 0.5:
                    score -= 2
                    details.append(f"Sahm Rule: +{sahm_rule:.1f}% -> Resesi (Bearish)")
                elif sahm_rule > 0.3:
                    score -= 1
                    details.append(f"Unemployment naik {sahm_rule:.1f}% dalam 3 bulan")
                elif sahm_rule < -0.2:
                    score += 1
                    details.append(f"Unemployment turun {sahm_rule:.1f}% dalam 3 bulan -> Ekonomi kuat (Bullish)")
                else:
                    details.append(f"Unemployment stabil ({unemp_current:.1f}%)")
                print(f"   Sahm Rule: {sahm_rule:.1f}%")
        
        # Normalisasi
        if score > 0:
            final_score = min(1.0, score / 2)
        elif score < 0:
            final_score = max(-1.0, score / 2)
        else:
            final_score = 0.0
        
        self.scores['labor_market'] = final_score
        self.details['labor_market'] = {
            'score': final_score,
            'raw_score': score,
            'details': details
        }
        
        print(f"   Final Score: {final_score:.2f}")
        return final_score
    
    # ============================================================
    # 6. KREDIT & LIKUIDITAS
    # ============================================================
    
    def calculate_credit_liquidity(self):
        """
        Menangkap stres di pasar keuangan
        
        Indikator:
        - Credit Spread Z-Score
        - M2 YoY (pertumbuhan uang beredar tahunan)
        
        Logika: Spread lebar = stres, M2 turun = likuiditas menurun
        """
        print("\n[FILTER] 6. Kredit & Likuiditas")
        
        score = 0
        details = []
        
        # === A. Credit Spread Z-Score ===
        if 'treasury_10y' in self.df.columns and 'fed_funds_rate' in self.df.columns:
            spread = self.df['treasury_10y'].iloc[-1] - self.df['fed_funds_rate'].iloc[-1]
            spread_mean = (self.df['treasury_10y'] - self.df['fed_funds_rate']).tail(60).mean()
            spread_std = (self.df['treasury_10y'] - self.df['fed_funds_rate']).tail(60).std()
            
            if not pd.isna(spread) and not pd.isna(spread_mean) and spread_std != 0:
                z_score = (spread - spread_mean) / spread_std
                
                if z_score > 1.5:
                    score -= 2
                    details.append(f"Spread sangat lebar (Z={z_score:.1f}) -> Stres (Bearish)")
                elif z_score > 0.5:
                    score -= 1
                    details.append(f"Spread melebar (Z={z_score:.1f}) -> Risk-Off (Bearish)")
                elif z_score < -0.5:
                    score += 1
                    details.append(f"Spread menyempit (Z={z_score:.1f}) -> Likuiditas baik (Bullish)")
                else:
                    details.append(f"Spread netral ({spread:.2f}%)")
                print(f"   Spread Z-Score: {z_score:.1f}")
        
        # === B. M2 YoY (252 hari) ===
        if 'money_supply' in self.df.columns and len(self.df) > 252:
            m2_current = self.df['money_supply'].iloc[-1]
            m2_1y_ago = self.df['money_supply'].iloc[-252] if len(self.df) >= 252 else m2_current
            m2_yoy = (m2_current - m2_1y_ago) / m2_1y_ago if m2_1y_ago != 0 else 0
            
            if not pd.isna(m2_yoy):
                if m2_yoy > 0.05:
                    score += 1
                    details.append(f"M2 YoY: {m2_yoy:.2%} -> Likuiditas meningkat (Bullish)")
                elif m2_yoy < -0.02:
                    score -= 1
                    details.append(f"M2 YoY: {m2_yoy:.2%} -> Likuiditas menurun (Bearish)")
                else:
                    details.append(f"M2 YoY netral ({m2_yoy:.2%})")
                print(f"   M2 YoY: {m2_yoy:.2%}")
        
        # Normalisasi
        if score > 0:
            final_score = min(1.0, score / 2)
        elif score < 0:
            final_score = max(-1.0, score / 2)
        else:
            final_score = 0.0
        
        self.scores['credit_liquidity'] = final_score
        self.details['credit_liquidity'] = {
            'score': final_score,
            'raw_score': score,
            'details': details
        }
        
        print(f"   Final Score: {final_score:.2f}")
        return final_score
    
    # ============================================================
    # 7. RUN ALL FILTERS & GET COMPOSITE SCORE
    # ============================================================
    
    def run_all_filters(self):
        """
        Menjalankan semua filter makro dan menghasilkan sinyal komposit
        """
        print("\n" + "="*60)
        print("MACRO FILTERS PROFESIONAL")
        print("="*60)
        
        # Jalankan semua filter
        self.calculate_business_cycle()
        self.calculate_monetary_policy()
        self.calculate_trade_currency()
        self.calculate_risk_sentiment()
        self.calculate_labor_market()
        self.calculate_credit_liquidity()
        
        # === Sinyal Komposit ===
        weights = {
            'business_cycle': 0.20,
            'monetary_policy': 0.25,
            'trade_currency': 0.20,
            'risk_sentiment': 0.15,
            'labor_market': 0.10,
            'credit_liquidity': 0.10
        }
        
        # Hitung weighted average
        composite_score = sum(self.scores.get(key, 0) * weights[key] for key in weights.keys())
        
        # Tentukan sinyal
        if composite_score >= 0.5:
            signal = "STRONG BULLISH"
            confidence = min(100, abs(composite_score) * 100)
        elif composite_score >= 0.2:
            signal = "BULLISH"
            confidence = abs(composite_score) * 100
        elif composite_score <= -0.5:
            signal = "STRONG BEARISH"
            confidence = min(100, abs(composite_score) * 100)
        elif composite_score <= -0.2:
            signal = "BEARISH"
            confidence = abs(composite_score) * 100
        else:
            signal = "NEUTRAL"
            confidence = 0
        
        self.composite_score = composite_score
        self.composite_signal = signal
        self.composite_confidence = round(confidence, 2)
        
        self.details['composite'] = {
            'score': composite_score,
            'signal': signal,
            'confidence': confidence,
            'weights': weights
        }
        
        print("\n" + "="*60)
        print("HASIL KOMPOSIT")
        print("="*60)
        print(f"Composite Score: {composite_score:.3f}")
        print(f"Sinyal: {signal}")
        print(f"Confidence: {confidence:.1f}%")
        print("="*60)
        
        return {
            'composite_score': composite_score,
            'signal': signal,
            'confidence': confidence,
            'details': self.details
        }
    
    # ============================================================
    # 8. GET SUMMARY
    # ============================================================
    
    def get_summary(self):
        """
        Mendapatkan ringkasan semua filter dalam format dictionary
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'composite': {
                'score': self.composite_score,
                'signal': self.composite_signal,
                'confidence': self.composite_confidence
            },
            'themes': {}
        }
        
        theme_names = {
            'business_cycle': 'Siklus Bisnis',
            'monetary_policy': 'Kebijakan Moneter',
            'trade_currency': 'Nilai Tukar & Perdagangan',
            'risk_sentiment': 'Sentimen Risiko',
            'labor_market': 'Pasar Tenaga Kerja',
            'credit_liquidity': 'Kredit & Likuiditas'
        }
        
        for key, name in theme_names.items():
            if key in self.scores:
                summary['themes'][name] = {
                    'score': self.scores[key],
                    'details': self.details.get(key, {}).get('details', [])
                }
        
        return summary


# ============================================================
# FUNGSI UTAMA (untuk testing)
# ============================================================

def main():
    """
    Testing fungsi MacroFilter
    """
    print("Loading data...")
    
    try:
        macro_df = pd.read_parquet('data/macro_data.parquet')
        print(f"Data loaded: {len(macro_df)} rows")
    except Exception as e:
        print(f"Error loading data: {e}")
        return
    
    filter_macro = MacroFilter(macro_df)
    result = filter_macro.run_all_filters()
    summary = filter_macro.get_summary()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Composite Signal: {summary['composite']['signal']}")
    print(f"Confidence: {summary['composite']['confidence']}%")
    print("\nTheme Scores:")
    for theme, data in summary['themes'].items():
        print(f"   - {theme}: {data['score']:.3f}")
        for detail in data['details'][:2]:
            print(f"      {detail}")
    
    return summary


if __name__ == "__main__":
    main()
