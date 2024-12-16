from confluent_kafka import Consumer
import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email_config
import time

# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
    Il componente AlertNotifierSystem è un servizio indipendente che, alla ricezione 
    di un messaggio nel topic Kafka "to-notifier", invia una email con parametri:
     --> to: email, 
     --> subject: ticker
     --> body: condizione di superamento soglia (superiore o inferiore)
"""

# Configurazione indirizzo del broker Kafka (DNS di Docker)
kafka_broker = "kafka_container:9092"

# Configurazione del consumer Kafka con commit manuale
consumer_config = {
    'bootstrap.servers': kafka_broker,  # Indirizzo del broker Kafka
    'group.id': 'group1',  
    'auto.offset.reset': 'latest',  # Se il consumer non ha un offset salvato legge solo i nuovi messaggi (non quelli vecchi)
    'enable.auto.commit': False  # Disabilita l'auto-commit degli offset
}

# Creazione del consumer Kafka
consumer = Consumer(consumer_config)
in_topic = 'to-notifier' 

# Iscrizione del consumer al topic
consumer.subscribe([in_topic])


def poll_loop():
    """
    Funzione principale che ascolta i messaggi dal topic Kafka.
    Dopo aver elaborato correttamente ogni messaggio, il commit dell'offset viene eseguito manualmente.
    """
    logger.info("Preparazione del notifier...")
    time.sleep(10) # Diamo il tempo a kafka di mettere su la connessione

    logger.info("In attesa di messaggi dal topic 'to-notifier'...")
    try:
        while True:
            # Recupero dei messaggi dal topic Kafka con un timeout di 1 secondo
            msg = consumer.poll(1.0)

            # Se nessun messaggio è stato ricevuto, continua
            if msg is None:
                continue  

            # Gestione degli errori di polling
            if msg.error():
                logger.error(f"Errore del consumer: {msg.error()}")
                continue

            try:
                # Log dell'offset del messaggio letto
                offset = msg.offset()
                logger.info(f"Messaggio ricevuto con offset: {offset}")

                # Parsing del messaggio ricevuto (decodifica da JSON)
                data = json.loads(msg.value().decode('utf-8'))
                email = data['email']
                ticker = data['ticker']
                condition = data['condition']
                logger.info(f"Notifier: messaggio ricevuto: email={email}, ticker={ticker}, condition={condition}")

                # Creazione del contenuto dell'email
                subject = f"Ticker: {ticker}"
                body = f"{condition}!"

                # Invio dell'email
                send_email(email, subject, body)

                # Commit manuale dell'offset dopo elaborazione riuscita
                # asynchronous=False significa che il consumer aspetta che Kafka confermi che il commit dell'offset è stato completato prima di proseguire con l'elaborazione del prossimo messaggio
                consumer.commit(asynchronous=False)
                logger.info("Offset committato manualmente dopo elaborazione del messaggio.")

            except json.JSONDecodeError as e:
                # Errore di parsing JSON
                logger.error(f"Errore nel parsing del messaggio: {e}")
            except KeyError as e:
                # Errore per mancanza di campi nel messaggio JSON
                logger.error(f"Messaggio malformato, manca il campo: {e}")
            except Exception as e:
                # Gestione generale degli errori
                logger.error(f"Errore durante l'elaborazione del messaggio: {e}")
    
    except KeyboardInterrupt:
        # Chiusura del consumer su interruzione manuale (Ctrl+C)
        logger.info("Consumatore interrotto dall'utente.")
    finally:
        # Chiusura ordinata del consumer
        consumer.close()


def send_email(to_email, subject, body):
    """
    Funzione per inviare un'email con i parametri specificati.
    """
    try:
        # Creazione del messaggio email
        msg = MIMEMultipart()
        msg['From'] = email_config.email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connessione al server SMTP e invio dell'email
        logger.info("Connessione al server SMTP in corso...")
        with smtplib.SMTP(email_config.smtp_host, 587) as server:
          #  server.set_debuglevel(1)  # Mostra log dettagliati sullo scambio con il server SMTP
            server.starttls()  # Attiva la connessione TLS
            server.login(email_config.email, email_config.password)  # Login al server
            server.sendmail(email_config.email, to_email, msg.as_string())  # Invio del messaggio
            logger.info(f"Notifier: email inviata con successo a {to_email}")
    except Exception as e:
        logger.error(f"Errore durante l'invio dell'email: {e}")


if __name__ == "__main__":
    # Avvio del loop principale di ascolto dei messaggi
    poll_loop()