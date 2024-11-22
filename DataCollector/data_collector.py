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

# Query che per ogni ticker elimina quello più vecchio
delete_old_query = """
    DELETE FROM Data
    WHERE (ticker, timestamp) IN (
    SELECT * FROM (
        SELECT ticker, MIN(timestamp) AS oldest_timestamp
        FROM Data
        WHERE ticker = %s
        GROUP BY ticker
    ) AS subquery
);

"""


circuit_breaker = CircuitBreaker(f_threshold = 4, r_timeout= 30)
maximum_occurrences = 10 # numero di entry nella tabella Data per ciascun ticker





def fetch_yfinance_data(ticker):
    stock = yf.Ticker(ticker)

    # Otteniamo i dati storici dell'oggetto ticker per 1 giorno
    data = stock.history(period="1d")
    
    if data.empty:
        raise ValueError(f"Non sono stati trovati valori per il ticker: {ticker}")
    
    """
    Viene estratto il valore del prezzo di chiusura (Close) del primo (e unico) giorno nel DataFrame data. 
    La funzione .iloc[0] restituisce il primo valore nella colonna "Close", che è il prezzo di chiusura per il giorno richiesto.
    """
    closing_price_usd = data['Close'].iloc[0]

    # cambio USD-EUR 
    usd_to_eur_rate = 0.9  
    closing_price_eur = closing_price_usd * usd_to_eur_rate
    return closing_price_eur

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
        print(f"Errore durante il recupero dei ticker, codice di errore: {e}")
        return []



def data_collector():
    print("data_collector: start...")

    # Connessione al database (una sola volta)
    print("data_collector: Tentativo di connessione al database...")
    try:
        # Connessione al database tramite context manager (con la connessione che verrà chiusa automaticamente)
        with pymysql.connect(**db_config) as conn:  # Uso del context manager 'with' per gestire la connessione
            print("data_collector: Connessione al database riuscita")

            while True:
                try:
                    # Otteniamo i ticker dalla tabella Users
                    tickers = fetch_ticker_from_db(conn)
                    print(f"data_collector.py: Lista dei Ticker recuperati: {tickers}")

                    if not tickers:
                        print("data_collector.py: Nessun ticker trovato nella tabella Users")
                        continue

                    with conn.cursor() as cursor:
                        for ticker in tickers:
                            try:
                                # Richiede i dati al Circuit Breaker
                                price_in_eur = circuit_breaker.call(fetch_yfinance_data, ticker)
                            
                            except CircuitBreakerOpenException as e:
                                print(f"{e}")  # Eccezione sollevata quando il Circuit Breaker è nello stato "OPEN"
                                continue  # Continuiamo con il prossimo ticker
                            except Exception as e:
                                print(f"{e}")  # Altri tipi di eccezione (es. server fallisce)
                                continue  # Continuiamo con il prossimo ticker

                            # Otteniamo il timestamp corrente
                            timestamp = datetime.now(tz)

                            try:
                                # Inseriamo i dati nel database
                                cursor.execute(insert_query, (timestamp, ticker, price_in_eur))

                                # Contiamo le occorrenze presenti per un dato ticker
                                cursor.execute("SELECT COUNT(*) FROM Data WHERE ticker = %s", (ticker,))
                                count = cursor.fetchone()[0]

                                # Se ci sono più di maximum_occurrences, eliminiamo la più vecchia
                                if count > maximum_occurrences:
                                    cursor.execute(delete_old_query, (ticker,))
                                
                                print(f"data_collector: Ticker '{ticker}' aggiornato con successo, prezzo in uscita -> {price_in_eur:.2f} ({datetime.now(tz)})")

                            except pymysql.MySQLError as e:
                                print(f"data_collector: Errore nelle query al database... Codice di errore: {e}")
                                continue  # Continuiamo con il prossimo ticker

                        # Confermiamo tutte le modifiche nel database
                        conn.commit()

                    # Aggiungiamo un ritardo di 5 secondi tra ogni ciclo
                    time.sleep(5)

                except Exception as e:
                    print(f"data_collector: Errore {e}")

    except pymysql.MySQLError as e:
        print(f"Tentativo di connessione al database fallito, codice di errore: {e}")
        return




if __name__ == "__main__": 
    data_collector()
