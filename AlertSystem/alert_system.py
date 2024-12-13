from confluent_kafka import Consumer, Producer
import pymysql
import json
import logging
import db_config


# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


"""
    il componente AlertSystem è un servizio indipendente che, alla ricezione di messaggio 
    nel topic  Kafka  "to-alert-system" (kafka consumer), scandisce il database e, 
    per ogni profilo in cui il valore del ticker è o maggiore di  high-value o minore 
    di low-value (se dati), invia un messaggio  (kafka producer)  sul topic Kafka 
    "to-notifier"  contenente i parametri 
                                    <email, ticker,  condizione di superamento soglia>.
"""

# configurazione indirizzo del broker (sfruttando il DNS di docker)
kafka_broker = "kafka_container:9092"

# configurazione consumatore
consumer_config = {
    'bootstrap.servers': kafka_broker, 
    'group.id': 'group1', 
    'auto.offset.reset': 'latest',
    'enable.auto.commit': True,  
    'auto.commit.interval.ms': 5000  # 5 seconds
}

# configurazione produttore
producer_config = {
    'bootstrap.servers': kafka_broker,
    'acks': 1, 
    'linger.ms': 0, # tempo max (ms) che aspetta prima di inviare i messaggi accumulati nel buffer. Se 0, vengono inviati immediatamente.
    'compression.type': 'gzip',
    'max.in.flight.requests.per.connection': 1,  
    'retries': 3 ,
}  

consumer = Consumer(consumer_config)
producer = Producer(producer_config)

in_topic = 'to-alert-system'  
out_topic = 'to-notifier'  


consumer.subscribe([in_topic]) 


def poll_loop():
    try:
        while True:
            # Poll for new messages from "in_topic"
            msg = consumer.poll(1.0)
            if msg is None:
                continue  # No message received, continue polling
            if msg.error():
                print(f"Consumer error: {msg.error()}")  
                continue
            
            """
                posso procedere con la scansione nel database
                (non bisgona controllare il contenuto del messaggio in quanto
                il fatto che sia presente garantisce l'avvenuto aggiornamento dei valori
                nel database da parte del DataCollector)
            """
           
            scan_database_and_notify() # questa si occupa anche della produzione
            

    except KeyboardInterrupt:
        # Shutdown on user interruption (Ctrl+C)
        print("Consumatore interrotto dall'utente.")
    finally:
        consumer.close()


def delivery_report(err, msg):
    """Callback to report the result of message delivery."""
    if err:
        print(f"Delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
    

def scan_database_and_notify():
    """
    Scansiona il database per identificare ticker che superano le soglie e invia notifiche.
    """
    try:
        conn = pymysql.connect(**db_config)
        with conn.cursor() as cursor:
            # Query per trovare profili che superano le soglie
            query = """
            SELECT u.email, u.ticker, d.valore_euro, u.low_value, u.high_value
            FROM Users u
            JOIN Data d ON u.ticker = d.ticker
            WHERE 
                (u.low_value IS NOT NULL AND d.valore_euro < u.low_value)
                OR 
                (u.high_value IS NOT NULL AND d.valore_euro > u.high_value);
            """
            cursor.execute(query)
            results = cursor.fetchall()
            
            for email, ticker, value, low, high in results:
                message = {
                    "email": email,
                    "ticker": ticker,
                    "condition": "low" if value < low else "high"
                }
                # Invia il messaggio al topic `to-notifier`
                producer.send("to-notifier", json.dumps(message), callback=delivery_report)
                producer.flush() 
                print(f"Produced: {message}")
                logger.info(f"Notifica inviata: {message}")

    except pymysql.MySQLError as e:
        logger.error(f"Errore durante la scansione del database: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    poll_loop()
