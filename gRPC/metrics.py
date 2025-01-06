from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import Histogram
import prometheus_client
import socket   # Per ottenere dinamicamente il nome dell'host

HOSTNAME = socket.gethostname() # per avere il nodo che ospita lo script di esecuzione del server
APP_NAME = "server_exporter" 


#### ELENCO DELLE METRICHE ######

# ➤ per le performance del sistema.
response_time_seconds = Histogram(
    'response_time_seconds',                                                                    # nome
    'Distribuzione della latenza di risposta del server per ogni richiesta',                    # descrizione
    ['uservice', 'hostname', 'function'],
    buckets=[0.1, 0.2, 0.5, 1.0, 2.0, 5.0]                                                                                                                                        # chiavi per le labels (per le PromQL)
)

# ➤ per monitorare l'efficacia della cache e garantire che non venga saturata.
cache_size = Gauge(
    'cache_size',                              
    'numero di entry nella cache',             
    ['uservice', 'hostname']
)

# ➤ carico sul server.
request_total = Counter(
    'request_total',                              
    'numero di richiesta totali ricevute dal server',             
    ['uservice', 'hostname']
)

# ➤ utile per monitorare il corretto funzionamento del server.
success_request = Counter(
    'success_request',
    'numero di richieste riuscite da parte del server',
    ['uservice', 'hostname']
)

# ➤  utile anche dal punto di vista della sicurezza (potrebbe, se alto, indicare la presenza di attacchi).
login_failures_total = Counter(
    'login_failures_total',                              
    'numero di entry nella cache',             
    ['uservice', 'hostname']
)
