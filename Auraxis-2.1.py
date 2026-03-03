import streamlit as st
import time
from datetime import datetime
from engine import get_hifi_data, neural_engine_v12
from interface import apply_terminal_theme, draw_auraxis_hud, render_strategy_module

st.set_page_config(page_title="AURAXIS V12 APEX", layout="wide")
apply_terminal_theme()

# Inicialização do Diário de Bordo em Memória (Streamlit Session State)
if 'diario' not in st.session_state:
    st.session_state.diario = []

placeholder = st.empty()

while True:
    with placeholder.container():
        df, pips = get_hifi_data()
        
        if not df.empty:
            p_atual = float(df['close'].iloc[-1])
            
            # 1. Auraxis lê a tendência de Position (A Maré Institucional)
            pos_sig = neural_engine_v12(df, "POSITION", 0)
            trend_dir = 0
            if pos_sig:
                trend_dir = 1 if pos_sig['tipo'] == "COMPRA" else -1
            
            # 2. Desenha HUD Principal
            draw_auraxis_hud(p_atual, pips, "OPERATIONAL")
            
            # 3. Grade Fractal de Execução
            c1, c2, c3, c4 = st.columns(4)
            
            modes = [("SCALPER", c1), ("DAY TRADE", c2), ("SWING", c3), ("POSITION", c4)]
            
            for m_name, col in modes:
                with col:
                    # O sistema processa internamente a coerência
                    sig_name = m_name.split()[0]
                    sig = neural_engine_v12(df, sig_name, trend_dir)
                    
                    # Lógica de "Sumir" ao romper: se o preço sai da zona, limpa o sinal
                    if sig and not (sig['z_inf'] <= p_atual <= sig['z_sup']):
                        sig = None
                    
                    # Se um sinal forte surge, o Auraxis 'anota' no diário (Memória)
                    if sig and sig['confianca'] > 85:
                        log = f"{datetime.now().strftime('%H:%M:%S')} | {m_name} | {sig['tipo']} @ {p_atual:.5f}"
                        if log not in st.session_state.diario:
                            st.session_state.diario.insert(0, log)
                    
                    render_strategy_module(m_name, sig)
            
            # 4. Painel de Diário de Bordo (Memória Evolutiva)
            with st.expander("📓 DIÁRIO DE BORDO (LOG DE SINAIS INSTITUCIONAIS)"):
                for entry in st.session_state.diario[:10]:
                    st.write(f"`{entry}`")
                    
            st.caption(f"Reflexo Neural Auraxis // Ciclo de 5s // Latência de Amostragem: Zero")
        else:
            st.error("ERRO_DE_FLUXO: Reconectando aos Satélites Financeiros...")
            
    time.sleep(5)
