import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sqlite3
import calendar

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="369 ELITE V34", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;600&display=swap');
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .stTabs [data-testid="stVerticalBlock"] > div { animation: fadeIn 0.5s ease-out forwards; }
    .stApp { background: #05070a; color: #e6edf3; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Orbitron'; color: #00ffcc; text-align: center; text-shadow: 0 0 20px rgba(0,255,204,0.4); padding: 10px 0 5px 0; }
    .cal-card { border-radius: 8px; padding: 15px; text-align: center; min-height: 110px; transition: 0.3s; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 10px; }
    .cal-win { background: linear-gradient(135deg, rgba(45, 101, 74, 0.9), rgba(20, 50, 40, 0.9)); border-top: 4px solid #34d399; }
    .cal-loss { background: linear-gradient(135deg, rgba(127, 45, 45, 0.9), rgba(60, 20, 20, 0.9)); border-top: 4px solid #ef4444; }
    .cal-be { background: linear-gradient(135deg, rgba(180, 130, 40, 0.9), rgba(80, 60, 20, 0.9)); border-top: 4px solid #fbbf24; }
    .cal-empty { background: #161b22; opacity: 0.3; }
    div[data-testid="stMetric"] { background: rgba(22, 27, 34, 0.7) !important; border: 1px solid #30363d !important; backdrop-filter: blur(5px); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ---
conn = sqlite3.connect('elite_final_v34.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS trades 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, pair TEXT, 
              outcome TEXT, pnl REAL, rr REAL, balance REAL, mindset TEXT, setup TEXT)''')
conn.commit()

# --- 3. DATA PREP ---
df = pd.read_sql_query("SELECT * FROM trades", conn)
current_balance = 0.0
total_pnl = 0.0

if not df.empty:
    df['date_dt'] = pd.to_datetime(df['date'])
    df = df.sort_values('date_dt')
    df['cum_pnl'] = df['pnl'].cumsum()
    current_balance = df['balance'].iloc[-1] + df['pnl'].sum()
    total_pnl = df['pnl'].sum()
    df['equity_curve'] = df['balance'].iloc[0] + df['cum_pnl']

# --- 4. HEADER & EQUITY (Top Position) ---
st.markdown('<h1 class="main-title">369 TRACKER PRO</h1>', unsafe_allow_html=True)
col_eq1, col_eq2, col_eq3 = st.columns([1, 2, 1])
with col_eq2:
    st.metric(label="CURRENT EQUITY", value=f"${current_balance:,.2f}", delta=f"${total_pnl:,.2f}")

tabs = st.tabs(["🚀 TERMINAL", "📅 CALENDAR LOG", "📊 MONTHLY %", "🧬 ANALYZERS", "📜 JOURNAL"])

# --- TAB 1: TERMINAL ---
with tabs[0]:
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.form("entry_v34", clear_on_submit=True):
            bal_in = st.number_input("Initial Balance ($)", value=1000.0)
            d_in = st.date_input("Date", datetime.now())
            asset = st.text_input("Pair", "XAUUSD").upper()
            res = st.selectbox("Outcome", ["WIN", "LOSS", "BE"])
            p_val = st.number_input("P&L ($)", value=0.0)
            r_val = st.number_input("RR Ratio", value=0.0)
            setup = st.text_input("Setup").upper()
            mind = st.selectbox("Mindset", ["Focused", "Impulsive", "Revenge", "Bored"])
            if st.form_submit_button("LOCK"):
                c.execute("INSERT INTO trades (date, pair, outcome, pnl, rr, balance, mindset, setup) VALUES (?,?,?,?,?,?,?,?)",
                          (str(d_in), asset, res, p_val, r_val, bal_in, mind, setup))
                conn.commit()
                st.rerun()
    with c2:
        if not df.empty:
            # الإصلاح: لا يتم استدعاء update_traces إلا إذا كانت هناك بيانات فعلاً
            fig_eq = px.line(df, x='date_dt', y='equity_curve', title="📈 GROWTH CURVE")
            fig_eq.update_traces(line_color='#00ffcc', fill='tozeroy', fillcolor='rgba(0,255,204,0.1)', markers=True)
            fig_eq.update_layout(template="plotly_dark")
            st.plotly_chart(fig_eq, use_container_width=True)
        else:
            st.info("Log your first trade to see the growth curve! 🚀")

# --- TAB 2: CALENDAR LOG ---
with tabs[1]:
    if not df.empty:
        today = datetime.now()
        cal = calendar.monthcalendar(today.year, today.month)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        cols_h = st.columns(7)
        for i, d_n in enumerate(days): cols_h[i].markdown(f"<p style='text-align:center; color:#8b949e'>{d_n}</p>", unsafe_allow_html=True)
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0: cols[i].markdown('<div class="cal-card cal-empty"></div>', unsafe_allow_html=True)
                else:
                    curr_d = datetime(today.year, today.month, day).date()
                    day_data = df[df['date_dt'].dt.date == curr_d]
                    p_s = day_data['pnl'].sum()
                    cnt = len(day_data)
                    style = "cal-win" if cnt > 0 and p_s > 0 else "cal-loss" if cnt > 0 and p_s < 0 else "cal-be" if cnt > 0 else "cal-empty"
                    pnl_v = f"${p_s:.2f}" if cnt > 0 else ""
                    cols[i].markdown(f'<div class="cal-card {style}"><div class="cal-date">{day}</div><div class="cal-pnl">{pnl_v}</div><div style="font-size:0.7rem">{cnt if cnt>0 else ""} Trades</div></div>', unsafe_allow_html=True)

# --- TAB 4: ANALYZERS ---
with tabs[3]:
    if not df.empty:
        st.subheader("🧬 Performance DNA")
        # Consistency Score
        avg_w = df[df['pnl'] > 0]['pnl'].mean() if not df[df['pnl'] > 0].empty else 1
        avg_l = abs(df[df['pnl'] < 0]['pnl'].mean()) if not df[df['pnl'] < 0].empty else 1
        wr = len(df[df['outcome']=='WIN']) / len(df)
        score = min((avg_w / avg_l) * wr * 10, 10.0)
        
        st.metric("Consistency Score", f"{score:.1f} / 10")
        st.progress(score/10)
        
        ca, cb = st.columns(2)
        with ca: st.plotly_chart(px.scatter(df, x='rr', y='pnl', color='outcome', title="Risk Management", template="plotly_dark"), use_container_width=True)
        with cb: st.plotly_chart(px.bar(df.groupby('mindset')['pnl'].sum().reset_index(), x='mindset', y='pnl', title="Psychology Tracker", template="plotly_dark"), use_container_width=True)
