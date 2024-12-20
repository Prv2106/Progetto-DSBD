from confluent_kafka import Consumer
import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email_config
import time
from create_topic import bootstrap_servers
from circuit_breaker import CircuitBreakerOpenException, CircuitBreaker


# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# istanza del Circuit Breaker
circuit_breaker = CircuitBreaker(f_threshold=3, r_timeout=20)

"""
    Il componente AlertNotifierSystem è un servizio indipendente che, alla ricezione 
    di un messaggio nel topic Kafka "to-notifier", invia una email con parametri:
     --> to: email, 
     --> subject: ticker
     --> body: condizione di superamento soglia (superiore o inferiore)
"""

# Configurazione del consumer Kafka con commit manuale
consumer_config = {
    'bootstrap.servers': ','.join(bootstrap_servers), 
    'group.id': 'group1',  
    'auto.offset.reset': 'earliest',  
    'enable.auto.commit': False,  # Disabilita l'auto-commit degli offset
}

in_topic = 'to-notifier' 

received_messages = []  # Buffer per gestire i messaggi durante il processamento del batch


# dizionario di dizionari che serve per evitare di mandare due o più email con lo stesso valore
# chiave: email utente; valore = dizionario contenente valore, condizione e ticker
mail_cache = {} 
"""
        E' qualcosa del tipo:
        {
            'utente@example.come': {
                'value': 10
                'condition': 'higher'
                'ticker' 'AMZN'
            }
        }
"""

def is_cache_outdated(email, value, condition_placeholder, ticker):
    '''
        Questa funzione fa un check sulla cache sulla base dei valori del ciclo corrente...
        Se il valore del ticker e la condizione sono uguali a quelle memorizzate allora 
        blocchiamo l'invio della mail (ritorniamo false), altrimenti,
        ritorniamo true (così nel codice che la invoca continuiamo l'esecuzione).

        N.B: facciamo il casting del valore del ticker in int per far si che le variazioni
             decimali non siano considerati fluttuazioni degne di essere notificate.
    '''
    if mail_cache is not None and email in mail_cache:
        old_value = int(mail_cache[email]['value'])  
        old_condition = mail_cache[email]['condition']
        old_ticker = mail_cache[email]['ticker']

        logger.info(f"Confronto cache: email={email},"
                    f"old_ticker={old_ticker}, new_ticker={ticker}, ," 
                    f"old_value={old_value}, new_value={int(value)},"
                    f"old_condition={old_condition}, new_condition={condition_placeholder}")

        # Forza il tipo di value a float prima del confronto
        if int(value) == old_value and condition_placeholder == old_condition and old_ticker == ticker:
            return False  # non inviare l'email
    return True  # inviare l'email
         
                    
def save_into_cache(email, value, condition_placeholder, ticker):
    if email not in mail_cache:  # se è la prima volta dobbiamo inizializzare
        mail_cache[email] = {}
    mail_cache[email]['value'] = int(value)
    mail_cache[email]['condition'] = condition_placeholder
    mail_cache[email]['ticker'] = ticker


def poll_loop():
    """
    Funzione principale che ascolta i messaggi dal topic Kafka.
    Dopo aver elaborato correttamente ogni messaggio, il commit dell'offset viene eseguito manualmente.
    """

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

            # gestiamo i batch di messaggi
            handle_msg(msg)

    except KeyboardInterrupt:
        # Chiusura del consumer su interruzione manuale (Ctrl+C)
        logger.info("Consumatore interrotto dall'utente.")
    finally:
        # Chiusura ordinata del consumer
        consumer.close()




def handle_msg(msg):
    try:
        # Parsing del messaggio ricevuto 
        data = json.loads(msg.value().decode('utf-8'))
        received_messages.append(data) 
        logger.info(f"lunghezza del batch: {len(received_messages)}")


        if len(received_messages) == 10:
            for message in received_messages:
                email = message['email']
                ticker = message['ticker']
                condition = message['condition']
                condition_placeholder = message['condition_placeholder'] 
                value = message['value']

                logger.info(f"Notifier: messaggio ricevuto: email={email}, ticker={ticker}, condition={condition}")
                logger.info(f"Dettagli messaggio: topic:{msg.topic()}, partizione:{msg.partition()}, offset:{msg.offset()}") 

                # vediamo se possiamo procedere con l'invio della mail o questa è ridondante
                ok = is_cache_outdated(email, value, condition_placeholder, ticker)
                attempts_count = 0
                if ok:
                    # Invio dell'email... creazione del contenuto dell'email
                    subject = f"Ticker: {ticker}"
                    body = f"{condition}!"

                    max_num_attempts = 5
                    while attempts_count < max_num_attempts:
                        try:
                            # qui è dove ci interfacciamo al servizio SMTP esterno (Mailo o Google)
                            circuit_breaker.call(send_email, email, subject, body)
                            logger.info(f"Notifier: email inviata con successo a {email}")
                            break
                        
                        except CircuitBreakerOpenException as e:
                            # Eccezione sollevata quando il Circuit Breaker è nello stato "OPEN"
                            logger.error(f"{e}")
                            attempts_count +=1
                            
                        except Exception as e:
                            # Altri tipi di eccezione (es. server fallisce)
                            logger.error(f"{e}")
                            attempts_count +=1
                            

                    # salvataggio in memoria dell'email per evitare (in futuro) email ridondanti
                    save_into_cache(email, value, condition_placeholder, ticker)
                else:
                    logger.info(f"Notifier: l'email non è stata mandata perchè ridondante! email={email}, ticker={ticker}")


                if attempts_count == 5:
                    logger.info(f"richiesta NON andata a buon fine (server SMTP non raggiungibile)")
                else:
                    logger.info(f"richiesta eseguita con successo")

            # reset del batch
            received_messages.clear()

            # Commit manuale dell'offset dopo elaborazione 
            consumer.commit(asynchronous=False) # commit sincrono => il consumer aspetta che Kafka confermi che il commit dell'offset è stato completato prima di proseguire con l'elaborazione del prossimo messaggio
            logger.info(f"Offset committato manualmente dopo elaborazione del batch")


    except json.JSONDecodeError as e:
        # Errore di parsing JSON
        logger.error(f"Errore nel parsing del messaggio: {e}")
    except KeyError as e:
        # Errore per mancanza di campi nel messaggio JSON
        logger.error(f"Messaggio malformato, manca il campo: {e}")
    except Exception as e:
        # Gestione generale degli errori
        logger.error(f"Errore durante l'elaborazione del messaggio: {e}")
    
    


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
    except Exception as e:
        logger.error(f"Errore durante l'invio dell'email: {e}")
        raise Exception(f"Errore, codice di errore: {e}") 


if __name__ == "__main__":      
    # Avvio del loop principale di ascolto dei messaggi
    logger.info("Preparazione del notifier...")
    time.sleep(30)
    # Creazione del consumer Kafka
    consumer = Consumer(consumer_config)
    # Iscrizione del consumer al topic
    consumer.subscribe([in_topic])
    poll_loop()