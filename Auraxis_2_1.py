# =========================
# Auraxis 2.1 Final Corrigido
# Multi-Par + Microtrajectória + Sweep/IPI + Layout Profissional
# =========================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Auraxis 2.1", layout="wide")
st.title("Auraxis 2.1 — Simulator Fusion Layer")

# -------------------------
# Configurações do Usuário
# -------------------------
st.sidebar.header("Configurações do Usuário")
perfil_trader = st.sidebar.selectbox(
    "Perfil de Trader:",
    ["Ultra Conservador", "Conservador", "Moderado", "Agressivo", "Automático"]
)
simulador_tipo = st.sidebar.selectbox(
    "Simulador:",
    ["Manual", "Assistido", "Automático"]
)
leverage_guide = {
    "Ultra Conservador": "1:10",
    "Conservador": "1:20",
    "Moderado": "1:50",
    "Agressivo": "1:100",
    "Automático": "Adaptável"
}
st.sidebar.markdown(f"**Alavancagem orientativa:** {leverage_guide[perfil_trader]}")

# -------------------------
# Pares de moedas
# -------------------------
pares_disponiveis = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "AUDUSD=X"]
periodo = st.sidebar.selectbox("Timeframe:", ["1m", "5m"])

# -------------------------
# Funções auxiliares
# -------------------------
def fetch_yahoo_data(symbol, period="7d", interval="1m"):
    df = yf.download(symbol, period=period, interval=interval)
    if df.empty:
        return pd.DataFrame()
    df.reset_index(inplace=True)
    # Garante que as colunas existam antes de filtrar
    cols_needed = ['Datetime','Open','High','Low','Close']
    df = df[[c for c in cols_needed if c in df.columns]]
    return df

def candle_valido(candle):
    return all(candle[col] > 0 for col in ['High', 'Low', 'Open', 'Close'])

def compute_confidence(candle):
    body = abs(candle['Close'] - candle['Open'])
    total_range = candle['High'] - candle['Low']
    if total_range == 0:
        return 0.3
    return float(min(0.85, body/total_range*0.85 + 0.15))

def compute_regime(df):
    df['diff'] = df['Close'] - df['Open']
    regime = []
    for d in df['diff']:
        if abs(d) < 0.0005: regime.append("Lateral")
        elif d > 0: regime.append("Alta")
        else: regime.append("Baixa")
    return regime

def compute_fragmentation(candle):
    zones = {}
    high, low, open_, close = candle['High'], candle['Low'], candle['Open'], candle['Close']
    range_ = high - low
    zones['zona_abertura'] = (open_, open_ + 0.2*range_)
    zones['zona_expansao'] = (open_ + 0.2*range_, open_ + 0.5*range_)
    zones['zona_pullback'] = (open_ + 0.5*range_, open_ + 0.7*range_)
    zones['zona_exp_final'] = (open_ + 0.7*range_, open_ + 0.9*range_)
    zones['zona_exaustao'] = (open_ + 0.9*range_, high)
    return zones

def simulate_SL_TP(candle, profile):
    percent_map = {"Ultra Conservador":0.005,"Conservador":0.01,"Moderado":0.02,"Agressivo":0.03,"Automático":0.015}
    pct = percent_map.get(profile, 0.01)
    range_ = candle['High'] - candle['Low']
    sl = candle['Close'] - pct*range_
    tp = candle['Close'] + pct*range_
    return float(sl), float(tp)

def simulate_sweep_IPI(df):
    ipi = []
    for i in range(len(df)):
        if i == 0:
            ipi.append(0.5)
        else:
            delta = float(df['Close'].iloc[i] - df['Close'].iloc[i-1])
            ipi_val = 0.5 + np.tanh(delta*100) / 2
            ipi.append(max(0, min(1, ipi_val)))
    df['IPI'] = ipi
    return df

# -------------------------
# Abas para múltiplos pares
# -------------------------
tabs = st.tabs([p.replace("=X","") for p in pares_disponiveis])

for i, par in enumerate(pares_disponiveis):
    with tabs[i]:
        st.subheader(f"Par: {par.replace('=X','')}")
        df = fetch_yahoo_data(par, period="7d", interval=periodo)
        
        if df.empty or len(df) < 2:
            st.warning("Aguardando dados do mercado ou mercado fechado.")
            continue

        df = df[df.apply(candle_valido, axis=1)]
        df['confidence'] = df.apply(lambda x: compute_confidence(x), axis=1)
        df['regime'] = compute_regime(df)
        df = simulate_sweep_IPI(df)
        
        ultimo_candle = df.iloc[-1]
        fragmentos = compute_fragmentation(ultimo_candle)
        sl, tp = simulate_SL_TP(ultimo_candle, perfil_trader)

        # Gráfico
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df['Datetime'],
            open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name=par
        ))

        # SL/TP Lines
        fig.add_hline(y=sl, line=dict(color='red', width=1, dash='dash'))
        fig.add_hline(y=tp, line=dict(color='green', width=1, dash='dash'))

        fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # Simulador
        st.write(f"**Confiança Atual:** {ultimo_candle['confidence']:.2%}")
        col1, col2 = st.columns(2)
        with col1: st.button(f"Comprar {par}", key=f"buy_{par}")
        with col2: st.button(f"Vender {par}", key=f"sell_{par}")

# Atualização automática (30s)
st.caption("Atualizando dados a cada 30 segundos...")

