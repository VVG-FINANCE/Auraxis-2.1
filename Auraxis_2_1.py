def fetch_yahoo_data(symbol, period="7d", interval="1m"):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df.empty:
            return pd.DataFrame()
        
        df.reset_index(inplace=True)
        
        # Tradução de colunas para garantir que o KeyError suma
        # O yfinance às vezes muda o nome de 'Datetime' para 'Date'
        if 'Date' in df.columns and 'Datetime' not in df.columns:
            df.rename(columns={'Date': 'Datetime'}, inplace=True)
            
        # Filtra apenas o necessário se existir
        cols = ['Datetime', 'Open', 'High', 'Low', 'Close']
        df = df[[c for c in cols if c in df.columns]]
        return df
    except Exception:
        return pd.DataFrame()
