from confluent_kafka import Consumer
import json
import logging

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import email_config


# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
    il componente AlertNotifierSystem è un servizio indipendente che, alla ricezione 
    di un messaggio nel topic  Kafka  "to-notifier",  invia una email con parametri:
     --> to: email, 
     --> subject: ticker
     --> body:  condizione di superamento soglia (superiore o inferiore)
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

consumer = Consumer(consumer_config)
in_topic = 'to-notifier'  

consumer.subscribe([in_topic]) 


def poll_loop():
    logger.info("In attesa di messaggi dal topic 'to-notifier'...")
    try:
        while True:
            # Poll for new messages from "in_topic"
            msg = consumer.poll(1.0)
            if msg is None:
                continue  # No message received, continue polling
            if msg.error():
                print(f"Consumer error: {msg.error()}")  
                continue
            
            
            # Parsing del messaggio ricevuto
            data = json.loads(msg.value().decode('utf-8'))
            email = data['email']
            ticker = data['ticker']
            condition = data['condition']
            logger.info(f"Notifier: messaggio ricevuto: email={email}, ticker={ticker}, condition={condition}")

            # Invio dell'email
            subject = f"Ticker: {ticker}"
            body = f"{condition}!"
            send_email(email, subject, body)

    except json.JSONDecodeError as e:
        logger.error(f"Errore nel parsing del messaggio: {e}")
    except KeyError as e:
        logger.error(f"Messaggio malformato, manca il campo: {e}")

    except KeyboardInterrupt:
        # Shutdown on user interruption (Ctrl+C)
        print("Consumatore interrotto dall'utente.")
    finally:
        consumer.close()
           

def send_email(to_email, subject, body):
    try:
        # Creazione del messaggio
        msg = MIMEMultipart()
        msg['From'] = email_config.email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        logger.info(f"Connessione al server SMTP in corso...")
        with smtplib.SMTP(email_config.smtp_host, 587) as server:
            server.set_debuglevel(1)  # Mostra log dettagliati
            server.starttls()
            server.login(email_config.email, email_config.password)
            server.sendmail(email_config.email, to_email, msg.as_string())  # Invio dell'email
            logger.info(f"Notifier: email inviata con successo a {to_email}")
    except Exception as e:
        print(f"Errore durante l'invio dell'email: {e}")
            


if __name__ == "__main__":
    poll_loop()