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


# metodo per testare il circuit breaker
def unreliable_service():
    if random.random() > 0.3: 
        logger.info("circuit_breaker: esecuzione metodo unreliable_service()")
        raise Exception("circuit_breaker: Test di errore")
    

class CircuitBreaker:

    # Metodo costruttore
    def __init__(self, f_threshold = 3, r_timeout = 20, e_exception = Exception):
        # definizione degli attributi di istanza:
        self.state = "CLOSED"           # inizialmente lo stato del circuit breaker è CLOSED -> tutte le richieste passano
        self.f_threshold = f_threshold  # soglia di errore oltre la quale si passa allo stato OPEN
        self.r_timeout = r_timeout      # tempo da aspettare prima di poter passare allo stato HALF_OPEN
        self.last_failure_time = None   # istante di tempo durante il quale è avvenuto l'ultimo failure
        self.f_count = 0                # contatore degli errori
        self.lock = threading.Lock()    # creazione di un lock per la gestione di una sezione critica
        self.e_exception = e_exception
        self.s_count = 0                # contatore dei successi
        self.s_threshold = 3            # soglia di richieste eseguite con successo, oltre la quale il circuito viene chiuso
        
        self.test_mode = True           # flag da abilitare per testare il passaggio tra i vari stati in modo forzato
        self.t_threshold = 8            # numero di volte in cui effettuare il test durante gli stati CLOSED e HALF_OPEN
        self.t_count = 0                # contatore per il test

    # Metodo che si occupa di eseguire la richiesta in base allo stato del circuito
    def call(self,func,*args):
        logger.info(f"circuit_breaker: stato corrente del circuito -> {self.state}")
        
        with self.lock:
            if self.state == "OPEN":
                time_since_failure = time.time() - self.last_failure_time # misuriamo il tempo trascorso dall'ultimo failure.
                if time_since_failure >= self.r_timeout: # se questo tempo superato il recovery_timeout
                    self.state = "HALF_OPEN" # passiamo allo stato HALF_OPEN (come previsto dal pattern)
                    self.f_count = 0 
                    logger.info("circuit_breaker: Recovery Timeout superato, nuovo stato -> HALF_OPEN")
                else:
                    # Il circuito è ancora aperto
                    raise CircuitBreakerOpenException("circuit_breaker: Il circuito è aperto... Chiamata rifiutata.")

            # Codice che viene eseguito se il circuito in stato CLOSED o HALF-OPEN            
            try:
                # Per testare la transizione tra gli stati del circuito
                ################# TEST #########################
                if  (self.state == "CLOSED" or self.state == "HALF_OPEN") and self.test_mode and self.t_count <= self.t_threshold:
                    self.t_count += 1
                    logger.info(f"circuit_breaker: t_count aggiornato -> {self.t_count}")
                    unreliable_service()    
                    result = func(*args) # se il servizio inaffidabile non solleva eccezioni viene eseguita la richiesta
                ################# TEST #########################
                else: # al di fuori della fase di test eseguiamo la richiesta verso yf
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
