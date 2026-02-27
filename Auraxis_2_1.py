# =========================
# Auraxis 2.1 Final Revisado
# Multi-Par + Microtrajectória + Sweep/IPI + Layout Profissional
# =========================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Auraxis 2.1", layout="wide")
st.title("Auraxis 2.1 — Simulator Fusion Layer (Final Revisado)")

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
    df.reset_index(inplace=True)
    df = df[['Datetime','Open','High','Low','Close']]
    return df

def candle_valido(candle):
    return candle['High'] > 0 and candle['Low'] > 0 and candle['Open'] > 0 and candle['Close'] > 0

def compute_confidence(candle):
    body = abs(candle['Close'] - candle['Open'])
    total_range = candle['High'] - candle['Low']
    if total_range == 0:
        return 0.3
    return min(0.85, body/total_range*0.85 + 0.15)

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
    return sl, tp

def simulate_sweep_IPI(df):
    ipi = []
    for i in range(len(df)):
        if i == 0:
            ipi.append(0.5)
        else:
            delta = df['Close'][i] - df['Close'][i-1]
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
        df = df[df.apply(candle_valido, axis=1)]
        df['confidence'] = df.apply(lambda x: compute_confidence(x), axis=1)
        df['regime'] = compute_regime(df)
        df = simulate_sweep_IPI(df)
        
        if len(df) == 0:
            st.warning("Sem dados disponíveis no momento para este par.")
            continue

        ultimo_candle = df.iloc[-1]
        fragmentos = compute_fragmentation(ultimo_candle)
        sl, tp = simulate_SL_TP(ultimo_candle, perfil_trader)

        # -------------------------
        # Gráfico Profissional
        # -------------------------
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df['Datetime'],
            open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name=f"{par} {periodo}"
        ))

        # Overlay Confidence
        colors = ["rgba(0,255,0,0.2)" if c>0.7 else "rgba(255,255,0,0.2)" if c>0.5 else "rgba(255,0,0,0.2)" for c in df['confidence']]
        for j, color in enumerate(colors):
            fig.add_vrect(x0=df['Datetime'][j], x1=df['Datetime'][j], fillcolor=color, opacity=0.2, line_width=0)

        # Overlay fragmentos
        for zone, (low_z, high_z) in fragmentos.items():
            fig.add_hrect(y0=low_z, y1=high_z, fillcolor="blue", opacity=0.1, line_width=0)

        # Overlay Sweep/IPI
        fig.add_trace(go.Scatter(
            x=df['Datetime'], y=df['Close']*df['IPI'], mode='lines', line=dict(color='orange', width=1), name='Sweep/IPI'
        ))

        # SL/TP
        fig.add_hline(y=sl, line=dict(color='red', width=1, dash='dash'), annotation_text="SL", annotation_position="bottom right")
        fig.add_hline(y=tp, line=dict(color='green', width=1, dash='dash'), annotation_text="TP", annotation_position="top right")

        fig.update_layout(title=f"Auraxis 2.1 — {par.replace('=X','')} ({periodo})",
                          xaxis_title="Tempo", yaxis_title="Preço",
                          xaxis_rangeslider_visible=False,
                          template="plotly_dark",
                          legend=dict(orientation="h", y=1.05))
        st.plotly_chart(fig, use_container_width=True)

        # -------------------------
        # Simulador Interativo
        # -------------------------
        st.subheader("Simulador de Operações")
        if simulador_tipo != "Automático":
            col1, col2 = st.columns(2)
            with col1:
                aceito = st.button(f"Aceitar Entrada {par}")
            with col2:
                descarto = st.button(f"Descartar Entrada {par}")
            if aceito:
                st.success(f"Entrada aceita para {par} com SL={sl:.5f} e TP={tp:.5f}")
            elif descarto:
                st.warning("Entrada descartada")

        # -------------------------
        # Histórico e Alavancagem
        # -------------------------
        st.subheader("Histórico Recente (Últimos 7 dias)")
        st.dataframe(df[['Datetime','Open','High','Low','Close','confidence','regime','IPI']].tail(50))
        st.subheader("Informação Orientativa de Alavancagem")
        st.info(f"Perfil '{perfil_trader}': alavancagem sugerida {leverage_guide[perfil_trader]}")
        st.caption("Apenas indicativa. Use seu critério para aplicar em conta real.")

# -------------------------
# Atualização automática (30s)
# -------------------------
st.run()
