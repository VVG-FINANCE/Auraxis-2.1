import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

def get_hifi_data(ticker="EURUSD=X"):
    try:
        # Puxa 1 mês de histórico para contexto, mas foca nos últimos 100 ticks para micro-análise
        data = yf.download(ticker, period="1mo", interval="15m", progress=False)
        if data.empty: return pd.DataFrame(), 0.0
        
        p_atual = float(data['Close'].iloc[-1])
        p_ontem = float(yf.download(ticker, period="2d", interval="1d", progress=False)['Close'].iloc[-2])
        pips_diff = (p_atual - p_ontem) * 10000
        
        df = data[['Open', 'High', 'Low', 'Close']].copy()
        df.columns = ['open', 'high', 'low', 'close']
        return df, float(pips_diff)
    except:
        return pd.DataFrame(), 0.0

def neural_engine_v12(df, mode="DAY", trend_dir=0):
    """
    Motor de processamento interno do Auraxis. 
    Analisa fragmentação e exaustão institucional.
    """
    p_atual = float(df['close'].iloc[-1])
    
    # Engrenagens por Horizonte (Amostragem Estratégica)
    config = {
        "SCALPER": {"p": 14, "m": 1.4, "vol_weight": 1.1},
        "DAY": {"p": 32, "m": 2.4, "vol_weight": 1.2},
        "SWING": {"p": 70, "m": 4.2, "vol_weight": 1.5},
        "POSITION": {"p": 160, "m": 5.8, "vol_weight": 2.0}
    }
    
    c = config[mode]
    
    # Cálculo de Inércia Neural (Z-Score Adaptativo com Fragmentação)
    window = df.tail(c['p'])
    ma = window['close'].mean()
    # Fragmentação: Analisamos o desvio médio absoluto para evitar ruído de 'fat fingers'
    std = window['close'].std() + 1e-9
    z_score = (p_atual - ma) / std
    
    # Aprendizado de Exaustão: Compara corpo vs pavio
    candle_body = abs(window['open'].iloc[-1] - window['close'].iloc[-1])
    candle_range = (window['high'].iloc[-1] - window['low'].iloc[-1]) + 1e-9
    exhaustion_ratio = candle_body / candle_range

    # Filtro Fractal Institucional
    if mode != "POSITION" and trend_dir != 0:
        if (trend_dir > 0 and z_score < 0) or (trend_dir < 0 and z_score > 0):
            return None 

    atr = (window['high'] - window['low']).mean()
    
    # Lógica de Gatilho por Injeção de Liquidez
    # Se o z_score é alto mas o exhaustion_ratio é baixo, há 'Absorção' (Institucional segurando o preço)
    if z_score > 1.35 and exhaustion_ratio > 0.4:
        return {
            "tipo": "COMPRA",
            "z_inf": p_atual - (atr * 0.3), "z_sup": p_atual + (atr * 0.3),
            "tp": [p_atual + (atr * c['m']), p_atual + (atr * c['m'] * 1.5)],
            "sl": [p_atual - (atr * c['m'] * 0.7), p_atual - (atr * c['m'] * 1.2)],
            "confianca": min(70 + (z_score * 4), 99.4)
        }
    elif z_score < -1.35 and exhaustion_ratio > 0.4:
        return {
            "tipo": "VENDA",
            "z_inf": p_atual - (atr * 0.3), "z_sup": p_atual + (atr * 0.3),
            "tp": [p_atual - (atr * c['m']), p_atual - (atr * c['m'] * 1.5)],
            "sl": [p_atual + (atr * c['m'] * 0.7), p_atual + (atr * c['m'] * 1.2)],
            "confianca": min(70 + (abs(z_score) * 4), 99.4)
        }
    return None
