import pymysql
import yfinance as yf

# Configurazione per il database degli utenti
db_config = {
    "host": "users_db_container",
    "user": "alberto_giuseppe",
    "password": "dsbd_users",
    "database": "DSBD_users"
}


def fetch_tickers_from_db():
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT ticker FROM Utenti;")            
            result = cursor.fetchall()

            # Estrae solo i ticker come lista di stringhe
            tickers = [row[0] for row in result]
            return tickers
    finally:
        conn.close()

def fetch_yfinance_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    closing_price_usd = data['Close'].iloc[0]

    # cambio USD-EUR
    usd_to_eur_rate = 0.85 
    closing_price_eur = closing_price_usd * usd_to_eur_rate
    return closing_price_eur


def data_collector():
    tickers = fetch_tickers_from_db()
    for ticker in tickers: 
        price_in_eur = fetch_yfinance_data(ticker) 
        print(f"Ticker: {ticker}, Prezzo di chiusura in EUR: {price_in_eur:.2f}") 

# Esegui il DataCollector 
if __name__ == "__main__": 
    data_collector()

