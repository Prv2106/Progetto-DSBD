**HOMEWORK 3 \- Distributed Systems and Big Data**  
**UniCT \- Anno Accademico 2024/2025**

# **DESCRIZIONE DEL SISTEMA**

Il progetto estende l'architettura esistente introducendo la migrazione a k8s, insieme ad un meccanismo di white-box monitoring con Prometheus per quanto riguarda i 2 microservizi Data Collector e gRPC Server. 

In particolare, il cluster Kubernetes è stato testato attraverso Minikube e consiste in un insieme di oggetti di tipo Deployment, Service, PersistentVolumeClaim e PersistentVolume.

Per quanto concerne il monitoraggio del Server, sono state scelte delle metriche che permettono l’analisi della latenza delle risposte, del carico totale, delle richieste completate con successo, dei tentativi di login falliti (per possibili problemi di sicurezza) e dell’efficacia della cache.  
Per il Data Collector, invece, le metriche si focalizzano sul monitoraggio del numero dei ticker seguiti dagli utenti, sulla latenza nella produzione di messaggi verso il topic e sul carico di richieste verso il servizio esterno di Yahoo Finance.

In aggiunta al monitoraggio delle metriche, è stato implementato il componente di Prometheus Alert Manager, configurato per inviare notifiche email in risposta a specifici eventi o soglie critiche. Questa scelta consente di garantire un monitoraggio proattivo del sistema, permettendo interventi tempestivi in caso di anomalie e migliorando la resilienza complessiva dell'infrastruttura.

# **SCELTE PROGETTUALI**
**![photo_2025-01-06_12-59-28](https://github.com/user-attachments/assets/6266ae11-1e20-47f5-89f5-09a37fa78156)**



Alcuni microservizi sono stati containerizzati utilizzando immagini Docker personalizzate, definite tramite Dockerfile specifici. Queste immagini, pubblicate su Docker Hub, permettono un controllo granulare sulle configurazioni dei container, assicurando una maggiore sicurezza e facilitandone il riutilizzo.. 

Per ottimizzare la fase di inizializzazione del cluster Kubernetes, sono stati adottati accorgimenti riguardo la gestione dei volumi persistenti. Nello specifico, è stato scelto di dichiarare esplicitamente i Persistent Volumes (PV), associandoli manualmente ai Persistent Volume Claims (PVC) tramite il campo volumeName. Questo approccio previene errori di *provisioning* e, al contempo, assicura che i volumi soddisfino i requisiti. 

Relativamente al  monitoraggio, sono stati utilizzati tre tipi di metriche principali: Histogram, Gauge e Counter, ognuna scelta in base alla natura del dato da misurare. Le metriche di tipo Histogram (response\_time\_seconds e production\_latency) sono state adottate per analizzare la distribuzione di valori continui, come la latenza di risposta o la latenza di produzione, permettendo un monitoraggio su intervalli di tempo definiti. Quelle di tipo Gauge (cache\_size e monitored\_tickers) sono state utilizzate per tenere traccia di valori che possono fluttuare nel tempo, come il numero di entry nella cache o il numero di ticker monitorati nel database. Infine, le metriche Counter (request\_total, success\_request, e request\_to\_yf) misurano valori cumulativi, ideali per conteggiare eventi come richieste ricevute, successi o fallimenti di login.

Tutte le metriche posseggono delle *labels* che aggiungono un contesto ai dati raccolti, consentendo di individuare rapidamente i componenti, le funzioni o i nodi che richiedono attenzione.

Infine, le regole di allerta scelte permettono di identificare anomalie e problemi di performance nei microservizi. Per il Server, vengono generati avvisi relativamente alla latenza di risposta quando l’80° percentile supera i 2 secondi in un intervallo di 10 minuti (almeno il 20% delle latenze misurate in quell’intervallo supera i 2 secondi) o quando si rilevano aumenti anomali nei fallimenti di login, segnalando potenziali attacchi. Per il Data Collector, invece, altre regole controllano la variazione nel numero di ticker monitorati, attivando notifiche in caso di cali significativi, e analizzano la latenza nella produzione (kafka) di messaggi.

# **DETTAGLI IMPLEMENTATIVI:**

* **Kubernetes**  
  * **Controllo sul primo avvio del cluster**: è stata utilizzata la chiave initContainers (negli oggetti Deployment), la quale svolge un ruolo fondamentale nel garantire l’ordine nell'avvio dei microservizi all'interno di un cluster.   
    * Gli initContainers sono container eseguiti prima di quelli principali definiti in un Pod e sono stati adoperati nei microservizi che necessitano dell’esecuzione di altri prima di avviarsi.   
      * Per implementare questo meccanismo di attesa, è stata utilizzata un’immagine leggera come *busybox*, contenente uno script shell che sfrutta lo strumento di connessione *netcat* per verificare la disponibilità della porta associata al Service del Deployment da attendere.   
        * Il controllo viene ripetuto ciclicamente fino a quando il servizio richiesto non diventa disponibile, garantendo così un avvio ordinato e sincronizzato dei microservizi.  
      * Microservizi che “attendono”:  
        * I brokers kafka attendono Zookeeper perché quest’ultimo è responsabile di gestire la configurazione del cluster e di coordinare le operazioni dei broker (elezione del controller ecc.)  
        * Data collector, Alert notifier, Alert system e Kafka Admin aspettano uno dei 3 broker poiché, senza uno attivo, non possono inviare, ricevere o gestire i messaggi e né configurare i topic richiesti. Pertanto, la disponibilità di almeno un broker garantisce che la pipeline di dati tra i microservizi sia attiva e funzionante.  
        * Prometheus attende il Data Collector ed il Server perché deve accedere agli endpoint delle metriche esposti da questi microservizi per avviare il monitoraggio.  
        * Il Server attende il Database MySQL poiché senza questo disponibile non può elaborare richieste che richiedono accesso ai dati.  
      * Alla luce di quanto si è configurato, nel test con minikube, si è ottenuto il seguente ordine di avvio:  
1. Alert manager  
2. Redis  
3. MySQL  
4. Zookeeper  
5. Brokers Kafka  
6. Server  
7. Alert system  
8. Alert notifier  
9. Data collector  
10. Prometheus

	 

* **Chiave ‘replicas’ di ‘spec’:** si è scelto di impostare ad 1 tale parametro per tutti i deployment per uno scenario iniziale in cui il sistema non è sottoposto a un carico elevato, ma con la consapevolezza che, nel caso in cui fosse necessario uno scale-out del sistema, basterebbe aumentare tale valore e k8s si occuperebbe di gestire automaticamente la replicazione e il load balancing delle richieste tra le varie repliche. Per consentire ciò si è deciso, inoltre, di modificare il server–grpc e si è scelto di aggiungere redis come nuovo microservizio, in modo da garantire il rispetto della politica *at-most-once* anche nel caso in cui si decidesse, appunto, di avere più repliche del server. 

              

* **Prometheus**

**![photo_2025-01-06_12-59-34](https://github.com/user-attachments/assets/e830963e-f103-4e7e-9f74-1236294534c3)**

**\- N.B:** è stata utilizzata la libreria prometheus\_client di python.

* **Data Collector**:  si è scelto di raccogliere le seguenti metriche:  
  * **monitored\_tickers** (Gauge): è il numero di tickers (distinti) che sono presenti nel database. In particolare, al metodo set sull’oggetto Gauge è stata passata la lunghezza della lista restituita dalla funzione fetch\_ticker\_from\_db.  
    * La scelta di questa metrica è motivata dal fatto che consente di identificare rapidamente problemi nei processi di raccolta e nell’aggiornamento dei dati.  
  * **production\_latency** (Histogram): ogni volta che il Data Collector invia un messaggio al broker Kafka, viene calcolata la latenza totale, partendo dal momento in cui la produzione del messaggio inizia fino a quando il broker ha finito di scriverlo in tutte le repliche In-Sync. Questo valore viene poi osservato dalla metrica, che registra la latenza in bucket predefiniti (fino a 5 secondi), consentendo un’analisi dettagliata delle prestazioni.   
    * Una latenza elevata potrebbe indicare problemi di rete o un  sovraccarico del broker, rendendo questa metrica fondamentale per identificare e risolvere eventuali colli di bottiglia.  
  * **request\_to\_yf** (Counter): tiene traccia del numero totale di richieste effettuate dal Data Collector verso il servizio esterno Yahoo Finance, permettendo di valutare il carico generato dal sistema e di identificare eventuali anomalie come un numero insolitamente alto (o basso) di richieste, o consentendo di distinguere se gli eventuali problemi di risposta sono causati da limitazioni del servizio esterno o da errori interni.   
    * Nello specifico, la metrica viene incrementata solo per le richieste effettivamente gestite.

* **Server:** si è scelto di raccogliere le seguenti metriche:  
  * **cache\_size** (Gauge): monitora il numero totale di chiavi memorizzate nella cache Redis.   
    * Consente di monitorare il corretto aggiornamento della cache.   
  * **response\_time\_seconds** (Histogram): è una metrica simile sia per struttura che per scopo alla production\_latency vista per il Data Collector. Nello specifico, è calcolata per ogni funzione del server che gestisce una richiesta e consiste nella differenza tra gli istanti di tempo finali e iniziali di tali funzioni.   
    * Permette di mettere in luce, con precisione, i punti in cui il codice impiega più tempo a rispondere, segnalando così eventuali colli di bottiglia e fornendo una visione approfondita delle prestazioni complessive del Server.  
  * **request\_total** (counter): è un contatore che viene incrementato ogni volta che il Server riceve una nuova richiesta.   
    * In questo modo è possibile capire come varia il carico a cui è sottoposto il Server e, di conseguenza, sarà possibile prevedere eventuali picchi di utilizzo.  
  * **success\_request** (counter): è un contatore che si incrementa ogni volta che il Server gestisce con esito positivo una richiesta.   
    * Confrontando il valore di questa con quello di *request\_total*, si può calcolare il tasso di successo (e di fallimento) dell’applicazione.   
  * **login\_failures\_total** (counter): contatore che si incrementa ogni volta che un’operazione di login fallisce.   
    * Grazie a questa metrica, è possibile individuare potenziali anomalie di sicurezza (attacchi di tipo brute force) o, più semplicemente, potrebbe indicare problemi di usabilità.

* **Alert Manager**

  * **Data Collector**: si è scelto di utilizzare delle regole di alerting riguardanti le metriche *monitored\_tickers* e *production\_latency*, in particolare:  
    * **DrasticDropInMonitoredTickers**: la regola si attiva se il numero di ticker monitorati diminuisce di oltre 10 nell’arco di 5 minuti. Un calo così repentino potrebbe segnalare problemi che richiedono un intervento urgente di verifica.  
    * **HighProductionLatency**: se l’80° percentile della latenza osservata nelle ultime 24 ore supera i 2 secondi (ovvero, almeno il 20% delle latenze misurate nell'ultimo giorno ha superato i 2 secondi), l’allerta indica che la fase di produzione kafka sta subendo ritardi; ovvero, potrebbero esserci problemi a livello di rete, di configurazione di Kafka o del codice stesso.

  * **Server:** si è scelto di utilizzare delle regole di alerting riguardanti le metriche *login\_failures\_total* e *response\_time\_seconds\_bucket*, in particolare:  
    * **HighResponseTimePerRequest**:  l’allerta si attiva quando l’80° percentile del tempo di risposta del server supera i 2 secondi negli ultimi 10 minuti e risulta utile per individuare rallentamenti nelle chiamate in ingresso.  
    * **LoginFailuresSpike**: rileva se, in un intervallo di 5 minuti, avvengono più di 50 tentativi di login falliti. Un picco simile può segnalare problemi di sicurezza o difficoltà generali di accesso da parte di molti utenti in contemporanea.	
## File per il Build e il Deploy
[Build&Deploy&Setup_info.pdf](https://github.com/user-attachments/files/18319050/Build.Deploy.Setup_info.pdf)


