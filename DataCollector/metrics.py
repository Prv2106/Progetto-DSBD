from prometheus_client import Counter
from prometheus_client import Gauge
import prometheus_client

import socket   # Per ottenere dinamicamente il nome dell'host

HOSTNAME = socket.gethostname()
APP_NAME = "data_collector_exporter" 



#### ELENCO DELLE METRICHE ######

# numero di ticker attualmente monitorati
monitored_tickers = Gauge(
    'monitored_tickers',                                             # nome
    'numero di tutti i tickers (distinti) nel database',             # descrizione
    ['uservice']                                                     # chiavi per le labels (per le PromQL)
)

# numero totale di richieste a Yahoo! Finance
request_to_yf = Counter(
    'request_to_yf', 
    'numero totale di richieste verso yahoo finance', 
    ['uservice']
)

