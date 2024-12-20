from confluent_kafka import Consumer, Producer
import pymysql
import json
import logging
import db_config
import query_service
from datetime import datetime
import pytz
import time
from create_topic import bootstrap_servers


tz = pytz.timezone('Europe/Rome') 

# Configurazione del logger per tracciare gli eventi del programma
logging.basicConfig(level=logging.INFO)  # Imposta il livello di log a INFO
logger = logging.getLogger(__name__)  # Crea un logger per il modulo

"""
    il componente AlertSystem è un servizio indipendente che, alla ricezione di un messaggio 
    nel topic  Kafka  "to-alert-system" (kafka consumer), scandisce il database e, 
    per ogni profilo in cui il valore del ticker è o maggiore di high-value o minore 
    di low-value (se dati), invia un messaggio  (kafka producer)  sul topic Kafka 
    "to-notifier"  contenente i parametri <email, ticker,  condizione di superamento soglia>.
"""


# Configurazione del consumatore Kafka con commit manuale (auto commit disabilitato)
consumer_config = {
    'bootstrap.servers': ','.join(bootstrap_servers), 
    'group.id': 'group1',  
    'auto.offset.reset': 'earliest',  
    'enable.auto.commit': False,  
}

producer_config = {
    'bootstrap.servers': ','.join(bootstrap_servers),  
    'acks': 'all',  
    'linger.ms': 500,  # Aspetta mezzo secondo per accumulare i messaggi in batch
    'compression.type': 'gzip',  # Compressione dei messaggi per ridurre la larghezza di banda
    'max.in.flight.requests.per.connection': 1,  # Numero massimo di richieste inviate senza risposta
    'retries': 3,  # Numero di tentativi di invio in caso di errore
}  



in_topic = 'to-alert-system'  
out_topic = 'to-notifier'  
start_time = 0 # variabile utilizzata per monitorare la latenza dei messaggi prodotti


def poll_loop():
    logger.info("In attesa di messaggi dal topic 'to-alert-system'...")  
    try:
        while True:
            # Poll per nuovi messaggi dal topic "in_topic"
            msg = consumer.poll(1.0)  
            if msg is None:
                continue  # Se nessun messaggio è stato ricevuto, continua a fare polling
            if msg.error():
                print(f"Consumer error: {msg.error()}")  
                continue  # Continua a fare polling

            """
                Una volta ricevuto un messaggio, possiamo procedere con la scansione nel database
                (non bisogna controllare il contenuto del messaggio in quanto
                il fatto che sia presente garantisce l'avvenuto aggiornamento dei valori
                nel database da parte del DataCollector)
            """

            logger.info(f"Messaggio recuperato: {json.loads(msg.value().decode('utf-8'))}") 
            logger.info(f"Dettagli messaggio: topic:{msg.topic()}, partizione:{msg.partition()}, offset:{msg.offset()}") 
           
    
            scan_database_and_notify()  # Questa funzione si occupa anche della produzione

            # Commit manuale dell'offset dopo che il messaggio è stato elaborato correttamente
            consumer.commit(asynchronous=False)  
            logger.info(f"Offset committato manualmente. topic:{msg.topic()}, partizione:{msg.partition()}, offset:{msg.offset()}") 

    except KeyboardInterrupt:
        # Interruzione del programma con Ctrl+C
        print("Consumatore interrotto dall'utente.")
    except Exception as e:
        logger.error(f"Errore durante il polling, codice di errore: {e}")
    finally:
        consumer.close()  # Chiude il consumer quando il programma termina

def check_condition(value, low, high):
    """
        Stabilisce la condizione per cui la query sul database ha dato dei risultati
        (ovvero, se è stata superata una soglia massima o una soglia minima)
    """

    higher = False
    if low > -1 and high > -1: # se l'utente ha messo entrembe le soglie
        if value > high: 
            higher = True
        elif value < low:
            higher = False
    elif low == - 1 and high > -1:
        higher = True
    else:
        higher = False
    return higher

def delivery_report(err, msg):
    end_time = time.time()  # Tempo finale
    if err is not None:
        logger.error(f"delivery_report: Errore nella consegna del messaggio: {err}")
    else:
        latency = end_time - msg.timestamp()[1] / 1000  # Calcola latenza in secondi
        logger.info(f"delivery_report: Messaggio consegnato con successo al topic {msg.topic()} "
                    f"nella partizione {msg.partition()} con latenza {latency:.3f}s")

def scan_database_and_notify():
    global start_time
    """
    Scansiona il database per identificare ticker che superano le soglie e invia notifiche.
    """
    try:
        conn = pymysql.connect(**db_config.db_config)
        
        service = query_service.QueryService() # Recupera i risultati delle query di selezione distinti per utenti
        results = service.handle_get_distinct_users_values(query_service.GetDistinctUsersValuesQuery(conn))
        logger.info(f"\nRESULTS:\n {results}")
        # Elabora i risultati e invia notifiche per ogni profilo
        for email, ticker, value, low, high in results:
                is_higher = check_condition(value, low, high)
                message = {
                    "email": email,  # Indirizzo email del destinatario
                    "ticker": ticker,  # Ticker del profilo
                    "condition": f"Aggiornamento {datetime.now(tz)}:\nIl valore di {ticker} ({value}) è salito al di sopra della soglia da te indicata ({high})" if is_higher else f"Aggiornamento {datetime.now(tz)}:\nIl valore di {ticker} ({value}) è sceso al di sotto della soglia da te indicata ({low})",
                    "condition_placeholder": "higher" if is_higher else "lower",
                    "value": float(value)
                }
                # Log per tracciare l'invio del messaggio prima del flush
                logger.info(f"Preparazione per inviare il messaggio: {message}")

                start_time = time.time()
                producer.produce(out_topic, json.dumps(message), callback=delivery_report)
                
                # Log prima del flush per confermare l'invio del messaggio al produttore
                logger.info("Invio messaggio al producer Kafka...")
                producer.flush()  # Assicura che tutti i messaggi siano inviati
                logger.info(f"Notifica inviata: {message}") 
        
    except pymysql.MySQLError as e:
        # Gestione degli errori di connessione al database
        logger.error(f"Errore durante la scansione del database: {e}")
    finally:
        conn.close()  

if __name__ == "__main__":
    logger.info("Preparazione dell'alert system...")
    time.sleep(30)
    
    consumer = Consumer(consumer_config)  
    producer = Producer(producer_config)  

    consumer.subscribe([in_topic])
    poll_loop()  # Avvia il ciclo di polling per ricevere messaggi