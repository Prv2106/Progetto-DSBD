import pymysql
from datetime import datetime
import time
import yfinance as yf
import pytz
from circuit_breaker import CircuitBreakerOpenException, CircuitBreaker
import logging
import query_service
import command_service
import db_config
import json
from confluent_kafka import Producer
from create_topic import bootstrap_servers
import metrics


tz = pytz.timezone('Europe/Rome') 

# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# creiamo un'istanza del Circuit Breaker
circuit_breaker = CircuitBreaker(f_threshold = 3, r_timeout= 20)
maximum_occurrences = 200 # numero max di entry nella tabella Data per ciascun ticker
last_tickers = [] # lista dei ticker recuperati all'iterazione precedente


# configurazione produttore
producer_config = {
    'bootstrap.servers': ','.join(bootstrap_servers), 
    'acks': 'all', 
    'linger.ms': 0, # tempo max (ms) che aspetta prima di inviare i messaggi accumulati nel buffer. Se 0, vengono inviati immediatamente.
    'compression.type': 'gzip',
    'max.in.flight.requests.per.connection': 1,  
    'retries': 3 ,
}  

out_topic = 'to-alert-system'  


# Funzione per recuperare l'ultimo valore del ticker da Yahoo! Finance
def fetch_yfinance_data(ticker):
    try:    
        stock = yf.Ticker(ticker)

        # Otteniamo i dati storici dell'oggetto ticker per 1 giorno
        data = stock.history(period="1d")
        
        """
        dato che non abbiamo gestito la validazione del ticker passato dall'utente, abbiamo scelto di 
        considerare una risposta vuota (dovuta ad esempio dall'inserimento di un ticker non valido) come un soft error, 
        in modo da non causare l'apertura del circuito in questo tipo di situazione       
        """
        if data.empty: 
            return 0 
       
        """
        Viene estratto il valore del prezzo di chiusura (Close) del primo (e unico) giorno nel DataFrame data. 
        La funzione .iloc[0] restituisce il primo valore nella colonna "Close", che è il prezzo di chiusura per il giorno richiesto.
        """
        closing_price_usd = data['Close'].iloc[0]
            
        # Cambio USD-EUR
        usd_to_eur_rate = 0.9
        closing_price_eur = closing_price_usd * usd_to_eur_rate

        # --> aggiorniamo la metrica relativa al numero di richieste verso yahoo finance
        metrics.request_to_yf.labels(uservice="data-collector", hostname=metrics.HOSTNAME).inc()
            
        return closing_price_eur
            
    except Exception as e:
        # Gestione di errori generici (es. problemi di rete, API non raggiungibile)
        logger.error(f"Errore critico durante l'elaborazione del ticker {ticker}: {e}")
        raise Exception(f"Errore, codice di errore: {e}") 


# funzione che si occupa di recuperare la lista dei ticker dalla tabella Users del database
def fetch_ticker_from_db(conn):
    try:
        service = query_service.QueryService()
        result = service.handle_get_distinct_users_ticker(query_service.GetDistinctUsersTickerQuery(conn))
        if not result:  # condizione di lista vuota
            return []
        return result     
        
    except Exception as e:
        logger.error(f"data_collector: Errore durante il recupero dei ticker dal db, codice di errore: {e}")
        return []

def delivery_report(err, msg, start_time):
    end_time = time.perf_counter()  # Tempo finale
    if err is not None:
        logger.error(f"delivery_report: Errore nella consegna del messaggio: {err}")
    else:
        latency = end_time - start_time  # Calcola latenza in secondi
        # --> settiamo la metrica
        metrics.production_latency.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).set(latency)
        logger.info(f"delivery_report: Messaggio consegnato con successo al topic {msg.topic()} "
                    f"nella partizione {msg.partition()} con latenza {latency:.3f}s")


def data_collector():
    global last_tickers
    global start_time
    request_count = 0 # contatore per gestire la velocità delle richieste
    
    while True:
        
        if request_count > 300:
            time.sleep(3600) # aggiorna ogni ora
        elif request_count <1: # All'avvio esegue subito un ciclo
            pass
        else:
            time.sleep(120) # aggiorna ogni 2 min
        logger.info(f">>>>>>>>>>>>>>>>>>>>>>>>> Ciclo {request_count + 1}:")
        
        request_count += 1
        
        try:
            logger.info("data_collector: Tentativo di connessione al database...")
            # Apriamo una nuova connessione ad ogni ciclo
            with pymysql.connect(**db_config.db_config) as conn: 
                logger.info("data_collector: Connessione al database riuscita")

                # Otteniamo i ticker dalla tabella Users
                tickers = fetch_ticker_from_db(conn)
                logger.info(f"data_collector: Lista dei Ticker recuperati: {tickers}")

                if not tickers:  # lista vuota
                    logger.info("data_collector: Nessun ticker trovato nella tabella Users")
                    last_tickers.clear()
                    continue # riproviamo

                ############### Eliminazione dei ticker inutilizzati 
                for ticker in last_tickers:  # Confronta i ticker precedenti con quelli attuali
                    if ticker not in tickers:  # Ticker obsoleti
                        try:
                            service = command_service.CommandService()
                            service.handle_delete_tickers(command_service.DeleteTickerCommand(ticker,conn))
                            logger.info(f"data_collector: Ticker '{ticker}' rimosso dal database.")
                        except pymysql.MySQLError as e:
                            logger.error(f"data_collector: Errore durante l'eliminazione del ticker '{ticker}': {e}")
                            continue
            
                # Aggiorna last_tickers con la lista attuale
                last_tickers = tickers[:]

                # --> settiamo la metrica
                metrics.monitored_tickers.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).set(len(last_tickers))


                ############### Inserimento degli ultimi valori per i ticker
                for ticker in tickers:
                    try:
                        # Richiede i dati al Circuit Breaker
                        price_in_eur = circuit_breaker.call(fetch_yfinance_data, ticker)
                    
                    except CircuitBreakerOpenException as e:
                        # Eccezione sollevata quando il Circuit Breaker è nello stato "OPEN"
                        logger.error(f"{e}")
                        continue  # Continuiamo con il prossimo ticker
                    except Exception as e:
                        # Altri tipi di eccezione (es. server fallisce)
                        logger.error(f"{e}")
                        continue  # Continuiamo con il prossimo ticker

                    # Otteniamo il timestamp corrente
                    timestamp = datetime.now(tz)

                    try:
                        # Inseriamo i dati nel database
                        service = command_service.CommandService()
                        service.handle_insert_tickers(command_service.InsertTickerCommand(timestamp,ticker,price_in_eur,conn))

                        # Contiamo le occorrenze presenti per un dato ticker
                        service = query_service.QueryService()
                        count = service.handle_get_entry_count_by_ticker(query_service.GetEntryCountByTickerQuery(ticker,conn))
                    
                        # Se ci sono più di maximum_occurrences, eliminiamo la più vecchia
                        if count > maximum_occurrences:
                            service = command_service.QueryService()
                            service.handle_delete_old_entries_by_ticker(command_service.DeleteOldEntryByTickerCommand(ticker,conn))
                        
                        logger.info(f"data_collector: Ticker '{ticker}' aggiornato con successo, prezzo in uscita -> {price_in_eur:.2f} ({datetime.now(tz)})")

                    except pymysql.MySQLError as e:
                        # Gestione degli errori MySQL
                        logger.info(f"data_collector: Errore nelle query al database... Codice di errore: {e}")
                        continue  # Continuiamo con il prossimo ticker
                
                
                # Produciamo il messaggio per Kafka
                start_time = time.perf_counter()  # Tempo iniziale
                time.sleep(4) # per testare l'alert
                producer.produce(out_topic, json.dumps(f"database aggiornato: {datetime.now(tz)}"), callback=lambda err, msg: delivery_report(err, msg, start_time))
                producer.flush()  
                logger.info(f"data_collector: Messaggio prodotto {datetime.now(tz)}")
                
        except pymysql.MySQLError as e:
            # Gestione degli errori durante la connessione al database
            logger.error(f"data_collector: Tentativo di connessione al database fallito, codice di errore: {e}")
            continue

        except Exception as e:
            # Gestione generica degli errori
            logger.error(f"data_collector: Errore generico: {e}")
            continue


if __name__ == "__main__":
    # Start the Prometheus HTTP server on port 9999
    metrics.prometheus_client.start_http_server(9999)
    logger.info(f"Le metriche relative al Data Collector sono disponibili sull'interfaccia web di Prometheus")


    logger.info("data_collector: start...")
    time.sleep(30)
    producer = Producer(producer_config)
    data_collector()