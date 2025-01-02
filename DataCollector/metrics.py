from prometheus_client import Counter
from prometheus_client import Gauge
import prometheus_client
import socket   # Per ottenere dinamicamente il nome dell'host

HOSTNAME = socket.gethostname()      # per avere il nodo che ospita lo script di esecuzione del data collector
APP_NAME = "data_collector_exporter" 


#### ELENCO DELLE METRICHE ######

# ➤ utile per tenere traccia dei ticker (anche in ottica di marketing)
monitored_tickers = Gauge(
    'monitored_tickers',                                             # nome
    'numero di tutti i tickers (distinti) nel database',             # descrizione
    ['uservice', 'hostname']                                         # chiavi per le labels (per le PromQL)
)

# ➤ utile per monitorare la latenza di produzione dei messaggi 
production_latency = Gauge(
    'production_latency',                                             
    'è la latenza di produzione del messaggio nel topic "to-alert-system"',             
    ['uservice', 'hostname']                                                     
)

# ➤ utile come statistica per per monitorare il carico delle chiamate verso il servizio esterno
request_to_yf = Counter(
    'request_to_yf', 
    'numero totale di richieste verso yahoo finance', 
    ['uservice', 'hostname']
)


