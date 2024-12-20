**HOMEWORK 2 \- Distributed Systems and Big Data**  
**UniCT \- Anno Accademico 2024/2025**

# **DESCRIZIONE DEL SISTEMA**

Il progetto estende l'architettura esistente introducendo un nuovo modo di gestire l’interazione con il database (usando il pattern CQRS) e la notifica asincrona agli utenti. In particolare, gli utenti possono ora ricevere un'email ogni volta che il valore del loro ticker di interesse supera una soglia predefinita, sia al rialzo (high-value) che al ribasso (low-value). 

Alla registrazione, l'utente può fornire uno o entrambi questi parametri, successivamente aggiornabili tramite apposite RPC.

La nuova funzionalità di notifica asincrona si basa sull'integrazione di Apache Kafka. Nello specifico, la backbone di comunicazione è stata implementata con un cluster formato da 3 broker.

Un'ulteriore ottimizzazione è stata introdotta nella gestione delle soglie di notifica (high-value e low-value): per evitare notifiche ridondanti, il sistema tiene traccia delle condizioni precedenti, inviando un'email solo al verificarsi di una reale variazione di stato. Ciò è stato fatto con l’obiettivo di non avere delle email duplicate inviate all'utente, così da non inviare richieste inutili al servizio SMTP esterno e, quindi, così da garantire una maggiore efficienza complessiva del sistema.

Infine, è stata riutilizzata l’implementazione custom del Circuit Breaker anche nell’AlertNotifierSystem.

# **SCELTE PROGETTUALI**

![image](https://github.com/user-attachments/assets/86b686c9-bccc-4b5c-b14b-04cb84727805)


Per l’implementazione delle nuove funzionalità richieste sono stati utilizzati 3 nuovi container (custom): uno che gestisce sia la creazione dei topic che il recupero periodico dei metadati associati a questi (kafka-admin-container), uno per il componente *AlertSystem* (alert\_system\_container) ed uno per il componente *AlertNotifierSystem* (alert\_notifier\_container). 

Oltre a quelli discussi sopra, vi sono anche altri 4 container: uno per ZooKeeper e gli altri per i 3 broker kafka (uno ciascuno). Zookeeper è un servizio centrale per la gestione dei metadati e il coordinamento dei broker Kafka; infatti, si occupa di mantenere la configurazione del cluster e di gestire l'elezione del controller tra i broker. In altre parole, senza tale componente i 3 broker non formerebbero un cluster.

Si è scelto di isolare le funzionalità di amministrazione di Kafka in un container dedicato per garantire il principio di separazione delle responsabilità, mantenendo chiara la distinzione tra le operazioni di gestione del cluster Kafka e le altre componenti del sistema. Si è, inoltre, deciso di implementare un unico container (anziché suddividerlo in due), poiché la creazione di topic e il recupero dei metadati sono operazioni strettamente correlate tra loro e condividono la stessa logica di interazione con il cluster Kafka.

Per quanto riguarda, invece, l’integrazione del pattern Command Query Responsibility Segregation, è stata adottata una strategia che separa nettamente i due aspetti fondamentali della gestione del sistema: tutti i *command* sono stati collocati nel file “command\_service.py”, mentre le *queries* nel file “*query\_service.py*”. 

# **DETTAGLI IMPLEMENTATIVI:**

* **CQRS**  
  * Due classi, *CommandService* e *QueryService*, gestiscono rispettivamente le operazioni di scrittura e lettura, centralizzando le logiche operative.   
    * In alcuni casi, il  *command* include controlli di validazione per garantire che i dati siano coerenti prima di interagire con il database. Ad esempio, abbiamo:  
* La verifica della validità dell’email in RegisterUserCommand.  
* Il controllo che il valore high\_value sia maggiore di low\_value (sia nel comando relativo all’operazione di registrazione del cliente che di modifica in un tempo successivo).  
* La gestione di valori non inseriti nelle soglie (ovvero, sono impostate \-1 se non inserite, con le logiche di controllo del superamento delle soglie che dipendono da questa struttura di memorizzazione).  
  * I *command* e le *query,* inoltre, contengono la logica di creazione della query SQL che viene poi eseguita dagli handler delle classi CommandService e QueryService.
   ![image](https://github.com/user-attachments/assets/b46030d1-ee84-4ef0-8ab7-880660e7d61b)


            

* **Sistema di notifica con Apache Kafka**
![image](https://github.com/user-attachments/assets/e08c4599-0a46-4a19-9cbc-0ad8331252df)


* **KafkaAdmin (management)**: Componente responsabile dell’inizializzazione del cluster kafka (creazione e configurazione dei topic) e del monitoraggio di quest’ultimo.  
  * La funzione create\_topic permette la creazione dei topic “to-alert-system” e “to-notifier”. Entrambi i topic sono stati configurati con una sola partizione e un fattore di replica pari a tre. La scelta di utilizzare una sola partizione è legata allo scenario iniziale, in cui è presente un solo AlertSystem e un solo AlertNotifierSystem, rendendo superfluo un numero maggiore di partizioni. Tuttavia, qualora in futuro fosse necessario effettuare uno scale-out del sistema (ad esempio, replicando il numero di AlertSystem e AlertNotifierSystem), il numero di partizioni potrà essere aumentato di conseguenza per sfruttare il meccanismo dei competing consumers, consentendo l'invio delle email in parallelo a più utenti e migliorando così il throughput del sistema. Il fattore di replica è stato impostato a 3 per garantire una maggiore robustezza: utilizzando 3 broker Kafka, il sistema può continuare a funzionare correttamente anche in caso di indisponibilità di uno o due broker.  
    * La funzione get\_metadata permette di monitorare il funzionamento del cluster Kafka. Ogni 2 minuti, vengono recuperati e stampati i seguenti metadati:  
      * Informazioni sui broker: ID, host e porta di ciascun broker nel cluster.  
        * Informazioni sui topic: per ogni topic, vengono riportati l'ID delle partizioni, il broker leader, le repliche e le repliche In-Sync (ISR).


    * **Configurazione dei Producer:**

      * **Data Collector**: Dopo ogni ciclo di aggiornamento, produce un messaggio su Kafka (topic to-alert-system) contenente un timestamp (il contenuto del messaggio non ha un valore intrinseco, ma serve solo a “svegliare” il consumer sottoscritto al topic in questione).

      * **AlertSystem:** scrive sul topic to-notifier un messaggio contenente delle informazioni correlate all’utente da notificare tramite email; ovvero: email, ticker, valore del ticker, condizione di superamento e corpo dell’e-mail.  
        * Dettagli implementativi:  
          * Utilizzo del pattern Circuit Breaker per quanto concerne la comunicazione col server SMTP.  
          * Meccanismo di blocco di email ridondanti: è stata utilizzata una cache che tiene traccia, per ogni email inviata, di 3 variabili: valore del ticker al momento dell’invio dell’email, condizione associata (‘higher’ o ‘lower’) e ticker (il simbolo, es: ‘AAPL’). Nello specifico, un’email viene mandata solo se almeno uno di questi 3 fattori varia.  
            * In particolare, la logica di variazione del valore di un ticker, vista la leggera volatilità del mercato azionario, è stata progettata per evitare l'invio di notifiche per fluttuazioni insignificanti: un valore viene considerato significativo se cambia l'unità della parte intera, piuttosto che i decimali.  
          * Batch di messaggi (piuttosto che singoli messaggi): A differenza del Data Collector, visto che l’interrogazione al database può restituire molti risultati, al fine di aumentare il throughput e diminuire l’utilizzo della larghezza di banda di rete utilizzata, è stato scelto di sfruttare la possibilità di Apache Kafka di accumulare più messaggi nel buffer del producer prima di inviarli al broker.

      * Per quanto riguarda i **parametri di configurazione** sono stati impostati:  
        * bootstrap.servers: “kafka-broker-1:9092,kafka-broker-2:9092,kafka-broker-3:9092”→ specifica l'elenco degli indirizzi dei broker Kafka (in questo caso, i container Docker kafka-broker-1, kafka-broker-2 e kafka-broker-3), utilizzando il DNS di Docker per la risoluzione dei nomi.  
        * acks: ‘all’ →  garantisce che il broker leader restituisca un ack solo dopo aver scritto il messaggio su tutte le repliche In-Sync (ISR). Questo approccio massimizza l'affidabilità: se il broker leader dovesse fallire, le repliche avranno comunque una copia consistente del messaggio. Tuttavia, questa configurazione può aumentare leggermente la latenza.


        * linger.ms:   
          * 0 → **configurazione utilizzata per il data collector:** I messaggi sono inviati immediatamente (non inviamo batch ma singoli messaggi in quanto produce 1 solo messaggio per ciclo).  
          * 500 \-\> **configurazione utilizzata per l’alert system:** aspetta 500ms prima di inviare i messaggi al broker, in questo modo si formano batch di messaggi.  
        * max.in.flight.requests.per.connection: 1 → non vogliamo più richieste simultanee da parte del producer verso il broker perchè prediligiamo l’affidabilità e la coerenza temporale.  
        * retries: 3 → tenterà di inviare il messaggio fino a tre volte prima di fallire definitivamente. In combinazione al parametro precedente garantiamo resilienza (a scapito del throughput).

    * **Configurazione dei Consumer:**

      * **AlertSystem**: effettua la sottoscrizione al topic to-alert-system: ogni messaggio rappresenta una notifica che i dati nel database sono stati aggiornati.   
        * Si occupa, inoltre, di interrogare il database per identificare i ticker i cui valori hanno oltrepassato le soglie indicate dagli utenti. Include anche la logica per capire quali delle due (high\_value o low\_value) è stata superata, se entrambe presenti.

      * **AlertNotifierSystem:** effettua la sottoscrizione al topic to-notifier: ogni messaggio rappresenta il contenuto dell’email da inviare all’utente nel caso in cui si è verificata una certa condizione con una delle due soglie.   
        * Elaborazione: all’interno del poll loop, abbiamo deciso di procedere con l’invio delle email al raggiungimento di una lunghezza del batch di 10\. Il commit viene effettuato solo alla fine dell’elaborazione di tutti i 10 messaggi in modo da evitare che vi siano perdite di messaggi (ovvero, preferiamo una eventuale duplicazione della mail in quanto è un’operazione idempotente) in caso di fault del consumer durante l’elaborazione del batch.  
        * Gestione dei fallimenti temporanei del server SMTP: la chiamata al metodo call del Circuit Breaker (a cui viene passata la funzione send_email) è incapsulata all’interno di un ciclo while che esegue per un numero massimo di 5 volte se la connessione al server da errore. Questo perché si vuole evitare che errori temporanei impediscano l’invio delle email.

      * Per quanto riguarda i **parametri di configurazione**:  
        * bootstrap.servers: “kafka-broker-1:9092,kafka-broker-2:9092,kafka-broker-3:9092”→ specifica l'elenco degli indirizzi dei broker Kafka (in questo caso, i container Docker kafka-broker-1, kafka-broker-2 e kafka-broker-3), utilizzando il DNS di Docker per la risoluzione dei nomi.  
        * group.id: ‘group1’→  definisce il gruppo al quale appartiene il consumer, questo permette di implementare il meccanismo dei competing consumer nel caso in cui si fossero usate più partizioni e fossero stati replicati i consumer.  
        * auto.offset.reset: ‘earliest’ → per assicurare che, al momento della sottoscrizione a un topic, il consumer recuperi i messaggi dall'inizio della partizione. Questo è utile nei casi in cui il consumer non ha offset salvati o quando viene eseguita una rielezione. In alternativa, il valore latest farebbe leggere solo i nuovi messaggi prodotti dopo la sottoscrizione.  
        * enable.auto.commit: False → in questo modo implementiamo il meccanismo di commit in modo customizzato, in particolare, in tutti i consumer si è scelto di *committare* solo successivamente all’elaborazione del messaggio in modo da prevenire il rischio di perdere messaggi (a scapito di eventuali duplicazioni in caso di riavvii del consumer).


## File per il Build e il Deploy
[Build&Deploy&Setup_info.pdf](https://github.com/user-attachments/files/18212758/Build.Deploy.Setup_info.pdf)

