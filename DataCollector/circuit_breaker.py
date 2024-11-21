from datetime import datetime
import time
import threading
import pytz

tz = pytz.timezone('Europe/Rome') 

class CircuitBreaker:

    # Metodo costruttore
    def __init__(self, f_threshold = 3, r_timeout = 20, e_exception = Exception):
        #definizione degli attributi di istanza:

        self.state = "CLOSED" # inizialmente lo stato del circuit breaker è closed -> tutte le richieste passano
        self.f_threshold = f_threshold # soglia di errore oltre la quale si passa allo stato OPEN
        self.r_timeout = r_timeout # tempo necessario da apettare prima di poter passare allo stato HALF_OPEN
        self.last_failure_time = None # istante di tempo durante il quale è venuto l'ultimo faailure
        self.f_count = 0 # contatore degli errori
        self.lock = threading.Lock()  # Creazione di un lock per la gestione di una sezione critica
        self.e_exception = e_exception


    # Metodo che si occupa di eseguire la richiesta in base allo stato del circuito
    def call(self,func,*args):
        with self.lock: # Acquisizione del lock
            if self.state == "OPEN":
                time_since_failure = time.time() - self.last_failure_time
                if time_since_failure >= self.r_timeout:
                    self.state = "HALF_OPEN"
                else:
                    # Il circuito è ancora aperto
                    raise CircuitBreakerOpenException("Il circuito è aperto... Chiamata rifiutata.")

            # Per testare il circuito aperto
            # raise CircuitBreakerOpenException("Il circuito è aperto... Chiamata rifiutata.")
            
            # Circuito CLOSED o HALF-OPEN            
            try:
                # tentativo di esecuzione della richiesta
                result = func(*args)

            except self.e_exception as e: # se la richiesta fallisce
                self.last_failure_time = time.time()
                self.f_count +=1
                if self.f_count >= self.f_threshold:
                    self.state = "OPEN"
                raise e # rilancia al chiamante l'eccezione generata
                
            
            # se la richiesta viene eseguita con successo 
            else:
                if self.state == "HALF_OPEN":
                    self.f_count = 0
                    self.state = "CLOSED"

                print(f"Circuit Breaker: richiesta eseguita con successo ({datetime.now(tz)})")
                return result

class CircuitBreakerOpenException(Exception): # classe che estende Exception
    pass
