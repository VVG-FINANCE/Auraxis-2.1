import streamlit as st

def apply_terminal_theme():
    st.markdown("""
        <style>
        .stApp { background-color: #020408; color: #d1d5db; }
        .auraxis-header { border-left: 4px solid #58a6ff; padding-left: 20px; margin-bottom: 30px; }
        .system-status { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #3fb950; }
        .mode-card { 
            background: #0d1117; border: 1px solid #30363d; border-radius: 8px; 
            padding: 20px; height: 100%; transition: 0.3s;
        }
        .signal-active { border-right: 4px solid #3fb950; background: linear-gradient(90deg, #0d1117 0%, #10151c 100%); }
        .metric-label { font-size: 0.65rem; color: #8b949e; letter-spacing: 1px; }
        .metric-value { font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; color: #ffffff; }
        </style>
    """, unsafe_allow_html=True)

def draw_auraxis_hud(preco, pips, status):
    st.markdown(f"""
        <div class='auraxis-header'>
            <div class='system-status'>● AURAXIS_CORE_v12 // {status} // STREAM_ACTIVE</div>
            <h1 style='font-size: 4.5rem; margin: 0; color:white;'>{preco:.5f}</h1>
            <span style='color:{"#3fb950" if pips >=0 else "#f85149"}; font-weight:bold;'>
                {"▲" if pips>=0 else "▼"} {abs(pips):.1f} PIPS (VAR_DIÁRIA)
            </span>
        </div>
    """, unsafe_allow_html=True)

def render_strategy_module(name, data):
    with st.container():
        if data:
            color = "#3fb950" if data['tipo'] == "COMPRA" else "#f85149"
            st.markdown(f"""
                <div class='mode-card signal-active'>
                    <div style='display:flex; justify-content:space-between;'>
                        <span style='font-size:0.8rem; font-weight:bold;'>{name}</span>
                        <span style='color:{color}; font-size:0.7rem;'>SINAL_DETECTADO</span>
                    </div>
                    <h3 style='color:{color}; margin: 5px 0;'>{data['tipo']}</h3>
                    <div style='margin-bottom:10px; border-bottom: 1px solid #222; padding-bottom:10px;'>
                        <span class='metric-label'>ZONA_LIMITE (ENTRY)</span><br>
                        <code style='color:#58a6ff;'>{data['z_inf']:.5f} — {data['z_sup']:.5f}</code>
                    </div>
                    <div style='display:grid; grid-template-columns: 1fr 1fr; gap:10px;'>
                        <div><span class='metric-label'>TARGET_TP</span><br><b>{data['tp'][0]:.5f}</b></div>
                        <div><span class='metric-label'>RISK_SL</span><br><b>{data['sl'][0]:.5f}</b></div>
                    </div>
                    <div style='margin-top:10px; font-size:0.7rem; color:#8b949e;'>
                        CONFIANÇA_NEURAL: {data['confianca']:.1f}%
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class='mode-card' style='opacity:0.3;'>
                    <span style='font-size:0.8rem;'>{name}</span><br>
                    <span class='metric-label'>VARREDURA_ATIVA...</span>
                </div>
            """, unsafe_allow_html=True)
