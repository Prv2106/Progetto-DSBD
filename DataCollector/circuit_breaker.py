from datetime import datetime
import time
import threading
import pytz
import logging
import random

tz = pytz.timezone('Europe/Rome') 

# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def unreliable_service():
    # metodo per testare il circuit breaker
    if random.random() > 0.3:
        logger.info("circuit_breaker: esecuzione metodo unreliable_service()")
        raise Exception("circuit_breaker: Test di errore")
    


class CircuitBreaker:

    # Metodo costruttore
    def __init__(self, f_threshold = 3, r_timeout = 20, e_exception = Exception):
        # definizione degli attributi di istanza:
        self.state = "CLOSED"           # inizialmente lo stato del circuit breaker è closed -> tutte le richieste passano
        self.f_threshold = f_threshold  # soglia di errore oltre la quale si passa allo stato OPEN
        self.r_timeout = r_timeout      # tempo da apettare prima di poter passare allo stato HALF_OPEN
        self.last_failure_time = None   # istante di tempo durante il quale è venuto l'ultimo failure
        self.f_count = 0                # contatore degli errori
        self.lock = threading.Lock()    # Creazione di un lock per la gestione di una sezione critica
        self.e_exception = e_exception
        self.s_count = 0                # contatore dei successi
        self.s_threshold = 3            # soglia di richieste eseguite con successo, oltre la quale il cirxuito viene chiusoù
        
        self.test_mode = True           # Flag da abilitare per testare il passaggio da stato OPEN ad HALF_OPEN e da HALF_OPEN a CLOSED in modo forzato
        self.t_threshold = 20           # numero di volte in cui effettuare il test
        self.t_count = 0                # contatore per il test

    # Metodo che si occupa di eseguire la richiesta in base allo stato del circuito
    def call(self,func,*args):
        logger.info(f"circuit_breaker: stato corrente del circuito -> {self.state}")

        if self.state == "OPEN":
            time_since_failure = time.time() - self.last_failure_time
            if time_since_failure >= self.r_timeout:
                self.state = "HALF_OPEN"
                self.f_count = 0
                logger.info("circuit_breaker: Recovery Timeout superato, nuovo stato -> HALF_OPEN")
            else:
                # Il circuito è ancora aperto
                raise CircuitBreakerOpenException("circuit_breaker: Il circuito è aperto... Chiamata rifiutata.")


        # Circuito CLOSED o HALF-OPEN            
        try:
            # Per testare la transizione del circuito da OPEN ad HALF_OPEN
            ################# TEST #########################
            if  (self.state == "CLOSED" or self.state == "HALF_OPEN") and self.test_mode and self.t_count <= self.t_threshold:
                self.t_count += 1
                unreliable_service()
                result = func(*args) # se il servizio inaffidabile non solleva eccezioni viene eseguita la richiesta
            ################# TEST #########################
            else:
                # tentativo di esecuzione della richiesta
                result = func(*args)
                    

        except self.e_exception as e: # se la richiesta fallisce
            if self.state == "CLOSED":
                self.last_failure_time = time.time()
                self.f_count = self.f_count + 1
                logger.error(f"circuit_breaker: Errore nella richiesta al servizio, failure_count -> {self.f_count}")
                if self.f_count >= self.f_threshold:
                    logger.info("circuit_breaker: Soglia di failure superata, nuovo stato -> OPEN")
                    self.state = "OPEN"
                
            elif self.state == "HALF_OPEN":
                logger.info(f"circuit_breaker: Richiesta fallita nello stato {self.state}, nuovo stato -> OPEN")
                self.s_count = 0
                self.last_failure_time = time.time()
                self.state = "OPEN"
            raise e # rilancia al chiamante l'eccezione generata
                
            
        # se la richiesta viene eseguita con successo 
        else:
            if self.state == "HALF_OPEN":
                self.s_count += 1
                if self.s_count >= self.s_threshold:
                    logger.info(f"circuit_breaker: Richieste eseguite con successo pari a {self.s_count}, nuovo stato -> CLOSED")
                    self.state = "CLOSED"
                    self.s_count = 0

            logger.info(f"circuit_breaker: richiesta eseguita con successo ({datetime.now(tz)})")
            return result
       

class CircuitBreakerOpenException(Exception): # classe che estende Exception
    pass
