import pymysql
from datetime import datetime
import time
import yfinance as yf
import pytz
from circuit_breaker import CircuitBreakerOpenException, CircuitBreaker

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
    INSERT INTO Data (timestamp, ticker, valore_euro)
    VALUES (%s, %s, %s);
"""

# Query che per ogni id e ticker restituisce quello più vecchio
delete_old_query = """
    DELETE D 
    FROM Data D
    JOIN (
        SELECT ticker, MIN(timestamp) AS oldest_timestamp
        FROM Data
        GROUP BY ticker
    ) AS subquery ON D.ticker = subquery.ticker AND D.timestamp = subquery.oldest_timestamp
    WHERE D.ticker = %s;
"""


circuit_breaker = CircuitBreaker(f_threshold = 4, r_timeout= 30)
maximum_occurrences = 10

def fetch_ticker_from_db(conn):
    # Usa la connessione passata come parametro
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT ticker FROM Users;")            
            result = cursor.fetchall() 

            if not result:  # condizione di lista vuota
                return []

            # otteniamo una lista a partire dalla lista di tuple
            # result è una lista di tuple per esempio: [('AAPL',), ('GOOG',), ('TSLA',)]
            tickers = [row[0] for row in result]
            return tickers
        
    except Exception as e:
        print(f"Errore durante il recupero degli utenti: {e}")
        return []


def fetch_yfinance_data(ticker):
    stock = yf.Ticker(ticker)

    # Otteniamo i dati storici dell'oggetto ticker per 1 giorno
    data = stock.history(period="1d")
    
    if data.empty:
        raise ValueError(f"No data found for ticker {ticker}")
    
    """
    Viene estratto il valore del prezzo di chiusura (Close) del primo (e unico) giorno nel DataFrame data. 
    La funzione .iloc[0] restituisce il primo valore nella colonna "Close", che è il prezzo di chiusura per il giorno richiesto.
    """
    closing_price_usd = data['Close'].iloc[0]

    # cambio USD-EUR 
    usd_to_eur_rate = 0.9  
    closing_price_eur = closing_price_usd * usd_to_eur_rate
    return closing_price_eur

def data_collector():
    time.sleep(5)
    # Connessione al database (una sola volta)
    conn = pymysql.connect(**db_config)
    try:
        # Otteniamo i ticker dalla tabella Users
        tickers = fetch_ticker_from_db(conn)  # Passiamo la connessione
        print("\n############################################################")
        print(f"data_collector.py: Lista dei Ticker recuperati: {tickers}")
        print("############################################################\n")
        if not tickers:
            print("data_collector.py: Nessun dato trovato nella tabella Users.")
            return

       
        with conn.cursor() as cursor: # crea un oggetto cursore (che è utilizzato per eseguire le query nel database)
            # Cicliamo per ogni coppia (id, ticker)
            for ticker in tickers:
                try:
                    # Richiede i dati al Circuit Breaker
                    price_in_eur = circuit_breaker.call(fetch_yfinance_data, ticker)
                except CircuitBreakerOpenException as e:
                    print(f"{e}")  # Eccezione sollevata quando il Circuit Breaker è nello stato "OPEN"
                    continue  # Continuiamo con il prossimo ticker

                # Otteniamo il timestamp corrente
                timestamp = datetime.now(tz)

                # Inseriamo i dati nel database
                cursor.execute(insert_query, (timestamp,ticker, price_in_eur))

                # Contiamo le occorrenze presenti per un dato ticker
                cursor.execute("SELECT COUNT(*) FROM Data WHERE ticker = %s", (ticker))
                count = cursor.fetchone()[0]

                # Se ci sono più di maximum_occurrences, eliminiamo la più vecchia
                if count > maximum_occurrences:
                    cursor.execute(delete_old_query, (ticker))
                
                print(f"\ndata_collector.py: Ticker '{ticker}' aggiornato con successo, prezzo in uscita -> {price_in_eur:.2f} ({datetime.now(tz)})\n")

            # Confermiamo tutte le modifiche nel database
            conn.commit()

    finally:
        # Chiudiamo la connessione al database
        conn.close()


if __name__ == "__main__": 
    data_collector()
