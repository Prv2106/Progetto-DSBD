import pymysql
from datetime import datetime
import time
import yfinance as yf
import pytz

tz = pytz.timezone('Europe/Rome')  


# Configurazione per il database
db_config = {
    "host": "mysql_container",
    "user": "alberto_giuseppe",
    "password": "progetto",
    "database": "DSBD_progetto"
}

# QUERIEs
insert_query = """
    INSERT INTO Data (timestamp, id, ticker, valore_euro)
    VALUES (%s, %s, %s, %s);
"""
delete_old_query = """
    DELETE D 
    FROM Data D
    JOIN (
        SELECT id, ticker, MIN(timestamp) AS oldest_timestamp
        FROM Data
        GROUP BY id, ticker
    ) AS subquery ON D.id = subquery.id AND D.ticker = subquery.ticker AND D.timestamp = subquery.oldest_timestamp
    WHERE D.id = %s AND D.ticker = %s;
"""

def fetch_from_user_db():
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, ticker FROM Users;")            
            result = cursor.fetchall()

            if not result:
                return [], []

            # otteniamo 2 liste separate a partire da una lista di tuple
            ids, tickers = zip(*result)
            return ids, tickers
    finally:
        conn.close()

def fetch_yfinance_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    
    if data.empty:
        raise ValueError(f"No data found for ticker {ticker}")
    
    closing_price_usd = data['Close'].iloc[0]

    # cambio USD-EUR (puoi considerare di aggiornarlo dinamicamente)
    usd_to_eur_rate = 0.9  # valore fisso; considera l'aggiornamento dinamico se necessario
    closing_price_eur = closing_price_usd * usd_to_eur_rate
    return closing_price_eur

def data_collector():
    print("Connessione..")
    time.sleep(5)
    # Connessione al database
    conn = pymysql.connect(**db_config)
    ids, tickers = fetch_from_user_db()
    print("Utenti recuperati")
    if not ids or not tickers:
        print("Nessun dato trovato nella tabella Users.")
        return

    try:
        with conn.cursor() as cursor:
            for id, ticker in zip(ids, tickers):
                try:
                    price_in_eur = fetch_yfinance_data(ticker)
                except ValueError as e:
                    print(e)
                    continue

                timestamp = datetime.now(tz)  # Ottiene il timestamp corrente

                # Inserimento nel database
                cursor.execute(insert_query, (timestamp, id, ticker, price_in_eur))
                
                # Contiamo le occorrenze presenti per la coppia (id, ticker)
                cursor.execute("SELECT COUNT(*) FROM Data WHERE id = %s AND ticker = %s", (id, ticker))
                count = cursor.fetchone()[0]
                
                if count > 30:  # Se ci sono più di 30 occorrenze, eliminiamo la più vecchia
                    cursor.execute(delete_old_query, (id, ticker))
            
            # Conferma delle modifiche
            conn.commit()

    finally:
        conn.close()
        print(f"Operazione conclusa con successo alle ore: {datetime.now(tz)}")

# Esegui il DataCollector 
if __name__ == "__main__": 
    data_collector()
