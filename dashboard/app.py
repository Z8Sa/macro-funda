"""
app.py - Streamlit Dashboard
Jalankan dengan: streamlit run dashboard/app.py
Developer: Rafi
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================

st.set_page_config(
    page_title="Macro Dashboard XAUUSD",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS STYLING
# ============================================================

st.markdown("""
    <style>
    .big-font { font-size: 40px !important; font-weight: bold; }
    .signal-buy { color: #00ff00; font-weight: bold; }
    .signal-sell { color: #ff0000; font-weight: bold; }
    .signal-neutral { color: #ffff00; font-weight: bold; }
    .theme-card {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 15px;
        margin: 5px 0;
        border-left: 4px solid #ff6b6b;
    }
    .theme-bullish { border-left-color: #00ff00; }
    .theme-bearish { border-left-color: #ff0000; }
    .theme-neutral { border-left-color: #ffff00; }
    .stMetric {
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 10px;
    }
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #1e1e1e;
    }
    ::-webkit-scrollbar-thumb {
        background: #4a4a4a;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #6a6a6a;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================

st.title("📊 Macro Dashboard - XAUUSD")
st.caption(f"🕒 Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data(ttl=300)
def load_macro_data():
    try:
        df = pd.read_parquet('data/macro_data.parquet')
        return df
    except Exception as e:
        st.error(f"Error loading macro data: {e}")
        return None

@st.cache_data(ttl=300)
def load_sentiment():
    try:
        df = pd.read_parquet('data/news_sentiment.parquet')
        return df
    except Exception as e:
        return None

@st.cache_data(ttl=60)
def load_signal():
    try:
        with open('data/signal.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def load_macro_filters():
    """Load hasil filter makro dari signal.json"""
    try:
        signal = load_signal()
        if signal and 'macro_filters' in signal:
            return signal['macro_filters']
        return None
    except Exception as e:
        return None

# ============================================================
# LOAD ALL DATA
# ============================================================

macro_df = load_macro_data()
sentiment_df = load_sentiment()
signal = load_signal()
macro_filters = load_macro_filters()

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ Kontrol")
    
    # ============================================================
    # SINYAL TERKINI
    # ============================================================
    
    if signal:
        st.subheader("🎯 Sinyal Terkini")
        signal_color = {
            'STRONG BUY': '🟢',
            'BUY': '🟢',
            'NEUTRAL': '🟡',
            'SELL': '🔴',
            'STRONG SELL': '🔴'
        }
        signal_text = signal.get('signal', 'NEUTRAL')
        st.markdown(f"### {signal_color.get(signal_text, '⚪')} {signal_text}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Confidence", f"{signal.get('confidence', 0)}%")
        with col2:
            st.metric("Gold Price", f"${signal.get('gold_price', 'N/A')}")
    
    st.divider()
    
    # ============================================================
    # 6 TEMA FILTER MAKRO
    # ============================================================
    
    st.subheader("📊 6 Tema Filter Makro")
    
    if macro_filters:
        # Ambil data themes
        themes_data = macro_filters.get('themes', {})
        
        if themes_data:
            # Tampilkan setiap tema
            for theme_name, theme_data in themes_data.items():
                score = theme_data.get('score', 0)
                
                if score > 0.2:
                    color = "🟢"
                    label = "Bullish"
                    delta_color = "normal"
                elif score < -0.2:
                    color = "🔴"
                    label = "Bearish"
                    delta_color = "inverse"
                else:
                    color = "🟡"
                    label = "Netral"
                    delta_color = "off"
                
                st.metric(
                    label=f"{color} {theme_name}",
                    value=f"{score:.2f}",
                    delta=label,
                    delta_color=delta_color
                )
                
                # Detail expander
                details = theme_data.get('details', [])
                if details:
                    with st.expander(f"📋 Detail {theme_name}"):
                        for detail in details[:4]:
                            st.caption(f"• {detail}")
            
            # Composite Score
            st.divider()
            composite = macro_filters.get('composite', {})
            if composite:
                comp_score = composite.get('score', 0)
                comp_signal = composite.get('signal', 'NEUTRAL')
                comp_conf = composite.get('confidence', 0)
                
                if "BULLISH" in comp_signal:
                    color = "🟢"
                elif "BEARISH" in comp_signal:
                    color = "🔴"
                else:
                    color = "🟡"
                
                st.metric(
                    label=f"{color} Composite Score",
                    value=f"{comp_score:.3f}",
                    delta=f"{comp_signal} ({comp_conf}%)"
                )
        else:
            st.info("⚠️ Data themes tidak ditemukan")
    else:
        st.info("⚠️ Data filter makro belum tersedia")
    
    st.divider()
    
    # ============================================================
    # KOMPONEN ANALISIS
    # ============================================================
    
    st.subheader("📰 Komponen Analisis")
    if signal and 'components' in signal:
        comps = signal['components']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Fed Rate", f"{comps.get('fed_rate', 'N/A')}%")
            st.metric("CPI", f"{comps.get('cpi', 'N/A')}")
            st.metric("CPI Change", f"{comps.get('cpi_change', 'N/A')}%")
        
        with col2:
            st.metric("DXY", f"{comps.get('dxy', 'N/A')}")
            st.metric("DXY Change", f"{comps.get('dxy_change', 'N/A')}%")
            st.metric("Sentiment", f"{comps.get('sentiment_score', 'N/A')}")
        
        st.divider()
        st.caption("📌 Data Tambahan:")
        col3, col4 = st.columns(2)
        with col3:
            st.metric("Treasury 10Y", f"{comps.get('treasury_10y', 'N/A')}%")
        with col4:
            st.metric("Unemployment", f"{comps.get('unemployment', 'N/A')}%")
        
        if 'components_detail' in signal:
            st.divider()
            st.caption("📋 Detail Faktor:")
            for item in signal['components_detail'][:5]:
                st.write(f"• {item}")
    else:
        st.info("⚠️ Sinyal belum tersedia")

# ============================================================
# MAIN CONTENT - SINYAL BESAR
# ============================================================

if signal:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        signal_text = signal.get('signal', 'NEUTRAL')
        confidence = signal.get('confidence', 0)
        gold_price = signal.get('gold_price', 'N/A')
        
        if "BUY" in signal_text:
            color = "#00ff00"
        elif "SELL" in signal_text:
            color = "#ff0000"
        else:
            color = "#ffff00"
        
        st.markdown(f"""
        <div style='text-align: center; padding: 20px; background-color: #1e1e1e; border-radius: 15px;'>
            <h1 style='color: {color}; font-size: 48px;'>{signal_text}</h1>
            <p style='font-size: 20px;'>Confidence: {confidence}%</p>
            <p style='font-size: 24px;'>💰 ${gold_price}</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
else:
    st.warning("⚠️ Sinyal belum tersedia. Jalankan scripts/generate_signals.py terlebih dahulu.")

# ============================================================
# METRIK CEPAT (3 Kolom)
# ============================================================

if signal and 'components' in signal:
    comps = signal['components']
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏦 Fed Rate", f"{comps.get('fed_rate', 'N/A')}%")
    with col2:
        st.metric("📈 CPI", f"{comps.get('cpi', 'N/A')}")
    with col3:
        st.metric("💵 DXY", f"{comps.get('dxy', 'N/A')}")
    with col4:
        st.metric("📊 Sentimen", f"{comps.get('sentiment_score', 'N/A')}")

# ============================================================
# GRAFIK 6 TEMA FILTER MAKRO
# ============================================================

st.subheader("📊 Filter Makro")

if macro_filters:
    themes_data = macro_filters.get('themes', {})
    
    if themes_data:
        themes = []
        scores = []
        colors = []
        details_list = []
        
        for theme_name, theme_data in themes_data.items():
            score = theme_data.get('score', 0)
            themes.append(theme_name)
            scores.append(score)
            details_list.append(theme_data.get('details', []))
            
            if score > 0.2:
                colors.append('#00ff00')
            elif score < -0.2:
                colors.append('#ff0000')
            else:
                colors.append('#ffff00')
        
        if themes:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=themes,
                y=scores,
                marker_color=colors,
                text=[f"{s:.2f}" for s in scores],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Score: %{y:.2f}<extra></extra>'
            ))
            
            # Garis bantu
            fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
            fig.add_hline(y=0.2, line_dash="dot", line_color="green", opacity=0.3)
            fig.add_hline(y=-0.2, line_dash="dot", line_color="red", opacity=0.3)
            
            fig.update_layout(
                template='plotly_dark',
                title="Skor Masing-masing Tema",
                yaxis_title="Score",
                height=400,
                showlegend=False,
                hovermode='x'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Composite Score
            composite = macro_filters.get('composite', {})
            if composite:
                comp_score = composite.get('score', 0)
                comp_signal = composite.get('signal', 'NEUTRAL')
                comp_conf = composite.get('confidence', 0)
                
                st.metric(
                    label="🏆 Composite Score",
                    value=f"{comp_score:.3f}",
                    delta=f"{comp_signal} ({comp_conf}%)"
                )
    else:
        st.info("📊 Data themes tidak ditemukan dalam macro_filters")
else:
    st.info("📊 Data filter makro belum tersedia. Jalankan scripts/run_all.py terlebih dahulu.")

# ============================================================
# GRAFIK TREN DATA MAKRO
# ============================================================

st.subheader("📈 Tren Data Makro")

if macro_df is not None and not macro_df.empty:
    # Pilihan kolom
    exclude_cols = [
        'xauusd_change_1d', 'xauusd_change_5d', 'xauusd_change_20d',
        'dxy_change_1d', 'dxy_change_5d', 'dxy_change_20d',
        'treasury_10y_change_1d', 'treasury_10y_change_5d', 'treasury_10y_change_20d',
        'cpi_change_1d', 'cpi_change_5d', 'cpi_change_20d'
    ]
    available_cols = [col for col in macro_df.columns if col not in exclude_cols]
    
    default_cols = []
    for col in ['xauusd', 'dxy', 'fed_funds_rate']:
        if col in available_cols:
            default_cols.append(col)
    
    selected_cols = st.multiselect(
        "📌 Pilih data yang ingin ditampilkan:", 
        available_cols, 
        default=default_cols
    )
    
    if selected_cols:
        # Buat subplot
        fig = make_subplots(
            rows=len(selected_cols), 
            cols=1, 
            shared_xaxes=True, 
            subplot_titles=selected_cols, 
            vertical_spacing=0.05
        )
        
        colors_line = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9a825', '#ab47bc', '#66bb6a']
        
        for i, col in enumerate(selected_cols, 1):
            if col in macro_df.columns:
                data = macro_df[col].dropna()
                if len(data) > 500:
                    data = data.tail(500)
                
                fig.add_trace(
                    go.Scatter(
                        x=data.index, 
                        y=data, 
                        name=col, 
                        mode='lines', 
                        line=dict(width=2, color=colors_line[(i-1) % len(colors_line)]),
                        hovertemplate='<b>%{x}</b><br>%{y:.2f}<extra></extra>'
                    ),
                    row=i, col=1
                )
        
        fig.update_layout(
            height=300 * len(selected_cols), 
            showlegend=False, 
            template='plotly_dark',
            hovermode='x unified'
        )
        fig.update_xaxes(rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# SENTIMEN BERITA
# ============================================================

st.subheader("📰 Sentimen Berita")

if sentiment_df is not None and not sentiment_df.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=sentiment_df['date'].tail(10), 
            y=sentiment_df['avg_score'].tail(10), 
            name='Skor Sentimen', 
            marker_color='orange',
            hovertemplate='<b>%{x}</b><br>Score: %{y:.2f}<extra></extra>'
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
        fig.add_hline(y=0.3, line_dash="dot", line_color="green", opacity=0.3)
        fig.add_hline(y=-0.3, line_dash="dot", line_color="red", opacity=0.3)
        fig.update_layout(
            template='plotly_dark', 
            title="Rata-rata Skor Sentimen", 
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=sentiment_df['date'].tail(10), 
            y=sentiment_df['article_count'].tail(10), 
            name='Jumlah Artikel', 
            marker_color='blue',
            hovertemplate='<b>%{x}</b><br>Jumlah: %{y}<extra></extra>'
        ))
        fig.update_layout(
            template='plotly_dark', 
            title="Jumlah Artikel Relevan", 
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabel detail
    with st.expander("📋 Detail Sentimen Berita"):
        st.dataframe(
            sentiment_df.tail(10).sort_values('date', ascending=False), 
            use_container_width=True,
            height=300
        )
else:
    st.info("📰 Data sentimen belum tersedia. Jalankan filter_news.py terlebih dahulu.")

# ============================================================
# RAW DATA
# ============================================================

with st.expander("📋 Data Mentah Makro"):
    if macro_df is not None:
        st.dataframe(macro_df.tail(20), use_container_width=True, height=400)

with st.expander("📋 Data Filter Makro (JSON)"):
    if macro_filters:
        st.json(macro_filters)

with st.expander("📋 Data Signal (JSON)"):
    if signal:
        st.json(signal)

# ============================================================
# SCRIPT LOG
# ============================================================

with st.expander("🔄 Cara Menjalankan"):
    st.code("""
# 1. Jalankan secara berurutan
python scripts/fetch_macro_data.py
python scripts/filter_news.py
python scripts/generate_signals.py

# 2. Jalankan dashboard
streamlit run dashboard/app.py

# 3. (Opsional) Satu perintah semua
python scripts/run_all.py && streamlit run dashboard/app.py
""", language='bash')

# ============================================================
# TOMBOL REFRESH
# ============================================================

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ============================================================
# FOOTER
# ============================================================

st.divider()
col1, col2 = st.columns([2, 1])
with col1:
    st.caption("🚀 Dashboard ini menggunakan data dari FRED, Yahoo Finance, Twelve Data, dan NewsAPI")
with col2:
    st.caption(f"👨‍💻 Developer: Rafi | {datetime.now().strftime('%Y')}")

# ============================================================
# END OF FILE
# ============================================================
