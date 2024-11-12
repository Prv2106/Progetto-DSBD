import pymysql
from datetime import datetime
import time
import yfinance as yf

# Configurazione per il database degli utenti
db_1_config = {
    "host": "users_db_container",
    "user": "alberto_giuseppe",
    "password": "dsbd_users",
    "database": "DSBD_users"
}

# Configurazione per il database dei dati da collezionare
db_2_config = {
    "host": "data_db_container",
    "user": "alberto_giuseppe",
    "password": "dsbd_data",
    "database": "DSBD_data"
}

# QUERIEs
insert_query = """
    INSERT INTO Data (timestamp, id, ticker, valore_euro)
    VALUES (%s, %s, %s, %s);
"""
delete_old_query = """
    DELETE FROM Data
    WHERE (id, ticker) = (%s, %s)
    AND timestamp = (
        SELECT timestamp FROM (
            SELECT timestamp 
            FROM Data 
            WHERE id = %s AND ticker = %s 
            ORDER BY timestamp ASC 
            LIMIT 1
        )
    );
"""



def fetch_from_user_db():
    conn = pymysql.connect(**db_1_config)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id,ticker FROM Users;")            
            result = cursor.fetchall()

            # otteniamo 2 liste separate a partire da una lista di tuple
            ids, tickers = zip(*result) 
            # l'asterisco espande la lista in singole tuple, 'zip' poi le separa

            return ids, tickers
    finally:
        conn.close()

def fetch_yfinance_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    closing_price_usd = data['Close'].iloc[0]

    # cambio USD-EUR
    usd_to_eur_rate = 0.9
    closing_price_eur = closing_price_usd * usd_to_eur_rate
    return closing_price_eur


def data_collector():
    time.sleep(3)
    # Connessione al secondo database
    conn = pymysql.connect(**db_2_config)
    ids, tickers = fetch_from_user_db()
    try:
        with conn.cursor() as cursor:
            for id, ticker in zip(ids, tickers):
                price_in_eur = fetch_yfinance_data(ticker)
                timestamp = datetime.now()  # Ottiene il timestamp corrente

                # adesso interagiamo cosl database...
                cursor.execute(insert_query, (timestamp, id, ticker, price_in_eur))
                # dopo, contiamo le occorrenze presenti per la coppia (id, ticker)
                cursor.execute("SELECT COUNT(*) FROM Data WHERE id = %s AND ticker = %s", (id, ticker))
                count = cursor.fetchone()[0]
                if count > 30: # se questo supera 30 occorrenze, gli eliminiamo la più vecchia
                    cursor.execute(delete_old_query, (id, ticker, id, ticker))
            
            # Conferma delle modifiche
            conn.commit()

    finally:
        conn.close()

# Esegui il DataCollector 
if __name__ == "__main__": 
    data_collector()
