# Progetto DSBD
**DESCRIZIONE APPLICAZIONE**

Il progetto implementa un'architettura per la gestione di utenti e di dati finanziari mediante un server gRPC, un database MySQL ed un Data Collector le cui richieste verso il fornitore di servizi remoti Yahoo\! Finance sono protette mediante il Pattern Circuit Breaker.

Il nostro lavoro mira ad ottimizzare la gestione dei dati utilizzando un’architettura resiliente. In particolare, sono stati implementati dei meccanismi come, ad esempio, il consolidamento delle richieste per ticker comuni: se più utenti seguono lo stesso titolo azionario, viene effettuata una singola richiesta a Yahoo\! Finance, riducendo il carico sul sistema e migliorando l'efficienza.

Inoltre, il server gRPC implementa la politica "at-most-once" per tutte le funzionalità di gestione degli utenti e di recupero delle informazioni. 

Il Data Collector opera ciclicamente per aggiornare i dati relativi ai titoli seguiti dagli utenti. Le sue caratteristiche principali sono (che verranno discusse in seguito):

* Aggiornamento dei valori in uscita per i ticker.  
* Comportamento adattivo nella frequenza delle richieste.  
* Limite per dati di uno stesso ticker.   
* Pulizia dati.


Il Circuit Breaker, invece, previene sovraccarichi o richieste ripetute al servizio di Yahoo\! Finance in caso di malfunzionamenti. Prevede tre stati principali: *CLOSED* (fa passare tutte le richieste), *OPEN* (le richieste vengono bloccate), e *HALF OPEN* (fase di test in cui passano solo alcune richieste per valutare il ripristino del servizio). 

**SCELTE PROGETTUALI**

SCHEMA ARCHITETTURALE:
![IMG_3500](https://github.com/user-attachments/assets/3d36baaa-04d7-4cd8-b6e6-010b48f5a890)

Per la realizzazione della nostra applicazione distribuita abbiamo utilizzato 3 container: uno per il database (mysql\_container), uno per il server gRPC (grpc\_server\_container) e uno per il Data Collector \+ il Circuit Breaker (break\_collector\_container). Di conseguenza, ci siamo limitati a implementare solamente 2 microservizi (server gRPC e  Data Collector \+ Circuit Breaker). 

La scelta di utilizzare un solo container per il server gRPC è stata presa in funzione del fatto che esso sia relativamente semplice; pertanto, una sua ulteriore scomposizione in microservizi non avrebbe portato ad un miglioramento significativo, anzi, avrebbe aumentato la complessità (gestione di più container, endpoint, configurazioni, e bilanciamento del carico). 

Specificamente, il server si occupa di gestire le richieste degli utenti, mentre il Data Collector, è responsabile della raccolta dei dati da Yahoo\! Finance. Separando questi due compiti (con 2 container docker), abbiamo garantito una chiara separazione delle responsabilità, pur mantenendo l'architettura semplice e facilmente manutenibile.  
La separazione delle responsabilità tra i due microservizi è ulteriormente evidenziata dalla nostra scelta di utilizzare due reti Docker separate (net1 e net2) che permettono di isolare i servizi tra di loro anche a livello di rete, in modo da ridurre i rischi associati a comunicazioni non necessarie tra i vari componenti.

I due microservizi  comunicano indirettamente attraverso il database (che si trova in entrambe le reti), che funge da punto centrale per i dati degli utenti e i dati finanziari. 

Infine, il client gRPC di test comunica con il server mediante il canale realizzato sulla porta 50051 grazie al port mapping.

**MICROSERVIZI E LORO INTERAZIONI**:

* **Server gRPC**

  * **Dettagli implementativi:**  
    * Inserito nel container “grpc\_server\_container” all’interno della rete “net1”.  
    * Port Mapping 50051:50051 per consentire la comunicazione tra il client e il server.  
    * La politica at-most-once è stata implementata per tutte le RPC (Remote Procedure Call) esposte dal server, questo perché, così facendo, non solo viene garantita l’idempotenza delle operazioni che modificano lo stato del sistema (modificano il db) ma viene anche ridotto l’eventuale overhead dovuto alla ri-esecuzione di query al database che erano già stati effettuati per una data richiesta. Per implementare tale politica si è scelto di utilizzare come cache un dizionario di dizionari dove la prima chiave corrisponde al request\_id (uuid generato dal client ogni volta prima di effettuare la richiesta) e il valore è un ulteriore dizionario la cui chiave è lo user\_id (email dell’utente),  il cui valore è la risposta in sé. In questo modo, quando il il server deve verificare se una richiesta è già stata processata fa una doppia verifica (una sul request\_id e una sullo user\_id) in modo da ridurre ulteriormente la probabilità di avere inconsistenza nelle risposte a causa di eventuali richieste con lo stesso id (in collisione).  
    * Meccanismo di pulizia della cache: per rendere il server più efficiente, è stato impostato un limite sulla dimensione della cache (ovvero, il numero di chiavi sul dizionario più esterno) ed è stato implementato un meccanismo per il quale, non appena tale limite viene superato, viene rimosso dalla cache l’elemento più vecchio (per fare ciò si è sfruttato il fatto che a partire dalla 3° versione di python i dizionari seguono l’ordine di inserimento).  

  * **Interazioni:**  
    * Comunica con il DB per leggere o aggiornare i dati relativi agli utenti e ai ticker.  
    * Fornisce API verso il client per esporre le funzionalità richieste dal progetto. Nello specifico, fornisce le seguenti funzionalità:  
      * *RegisterUser*: permette la registrazione dell’utente inserendo email, password e ticker.   
      * *LoginUser*: permette all’utente di accedere fornendo email e password.  
      * *UpdateUser*: permette all’utente di aggiornare il proprio ticker.  
      * *DeleteUser*: permette all’utente di cancellare il proprio account.  
      * *GetLatestValue*: permette all’utente di recuperare l’ultimo valore aggiornato relativo alla propria azione.  
      * *GetAverageValue*: permette all’utente di ricevere la media dell’azione seguita su un numero di valori da lui specificato.   
        * N.B: Nel caso in cui il numero inserito è maggiore delle occorrenze nel db relative a quel ticker viene restituita la media sul massimo numero di occorrenze possibili.
![photo_2024-11-28_17-02-12](https://github.com/user-attachments/assets/0d7f3209-7253-4a6f-92a0-432432a1a07d)



* **Client gRPC**

  * **Dettagli Implementativi:**  
    * La connessione col server viene stabilita solo se il server è disponibile, altrimenti il client tenta di riconnettersi periodicamente per un massimo di 20 tentativi, con un intervallo di 5 secondi tra i tentativi (questo meccanismo viene utilizzato anche nel caso in cui la connessione viene persa dopo che questa era stata stabilita) e tale  comportamento è gestito dalla funzione wait\_for\_server()*.*   
      * Se la connessione viene persa durante una richiesta, il client tenta di riconnettersi e, in caso di successo, la ritrasmette.  
    * Per ogni funzione viene utilizzato un meccanismo di *timeout e retry*. Ovvero, ogni richiesta ha un timeout di 2 secondi dopo i quali, se la risposta non arriva, la chiamata scade: in questo caso (e nel caso in cui il server è offline) il client tenta di eseguire nuovamente la richiesta fino al numero massimo di tentativi (20).  
    * Il client presenta all'utente 2 menu principali:  
      * Menu di inizializzazione (quando l'utente non è loggato): permette all'utente di registrarsi o effettuare il login.  
      * Menu dell'utente loggato: offre le funzionalità per aggiornare il suo ticker, cancellare il suo account, ottenere l'ultimo valore disponibile o la media degli X ultimi valori per l’azione da lui seguita.

* **Data Collector**

  * **Dettagli Implementativi:**  
    * Inserito, insieme al Circuit Breaker, all’interno del container “break\_collector\_container”.   
    * Focus su quanto implementato:  
      * Aggiornamento dei valori in uscita per i ticker: ad ogni ciclo per ognuno dei ticker recuperati dal database viene inserito nella tabella Data il valore in uscita recuperato da Yahoo\! Finance (convertito in euro).  
      * Comportamento adattivo nella frequenza delle richieste: inizia con un ritmo rapido per poi rallentare (passa da 2 secondi ad 1 ora dopo 300 cicli). Ciò per garantire, da un lato, un funzionamento accettabile nel caso di un primo avvio (e quindi per garantire che i dati raccolti da Yahoo\! Finance siano, in quantità, sufficienti per testare le funzionalità offerte dal server), e, dall’altro lato, per far sì che, a regime, la funzionalità di recupero della media del valore di un’azione per un tot di valori sia significativa.  
      * Limite per dati di uno stesso ticker: si garantisce che non si superi un limite massimo di occorrenze per ciascun ticker (200) attraverso l’eliminazione dei dati più vecchi. In particolare, se per un determinato ticker il numero di occorrenze supera il limite, viene eseguita una query che va a rimuovere l’occorrenza più vecchia.  
      * Pulizia dati: I ticker non più seguiti dagli utenti vengono eliminati dal database per risparmiare spazio. Nello specifico, viene utilizzata una lista che memorizza i ticker elaborati nell'iterazione precedente che, ad ogni ciclo, viene confrontata con la lista dei ticker appena recuperati: per ogni ticker della prima lista che non è presente nella seconda viene effettuata una query che si occupa di eliminare le entry relative a tale ticker nella tabella Data.

  * **Interazioni:**  
    * col DB, per recuperare i ticker degli utenti e per memorizzare o eliminare i dati recuperati da yf (mediante il Circuit Breaker)
  ![IMG_3502](https://github.com/user-attachments/assets/4e19ceb5-27f1-45ed-b130-23bb0be5fab1)

* **Circuit Breaker** (integrato nel DataCollector)

  * **Dettagli Implementativi:**  
    * Integrato come modulo nel Data Collector.  
    * Quando il numero di errori consecutivi supera la soglia configurata (f\_threshold \= 3), il circuito passa allo stato OPEN: si resta in questo stato per 20 secondi. Dopodiché, il circuito entra in uno stato di HALF\_OPEN: se hanno successo 3 richieste **consecutive** passiamo allo stato CLOSED (diversamente, torniamo a OPEN). Tale scelta (vincolo della consecutività delle richieste eseguite con successo) è stata presa con lo scopo di conferire al sistema maggiore robustezza.

  * **Interazioni:**  
    * Gestisce l’interazione del Data Collector con l’API esterna.

* **Database** (MySQL)

  * **Dettagli Implementativi:**  
    * Inserito nel container “mysql\_container”.  
    * Consiste in 2 tabelle:

      * **Users**: ![Immagine 2024-11-28 172550](https://github.com/user-attachments/assets/f7eedf1b-9bb2-48d4-a4ee-285101fdef28)


        * Da evidenziare che  il salvataggio della password nel database (in fase di registrazione) avviene, per questioni di sicurezza, attraverso l’hashing della stessa (eseguito lato server).

      * **Data**:
     
     
        ![Immagine 2024-11-28 215622](https://github.com/user-attachments/assets/c3c63aa0-8f37-4fc8-a9d8-66ad20c2ff54)


        * Non è stata esplicitamente definita una relazione tra le tabelle perché il valore in uscita di un’azione è lo stesso indipendentemente dall’utente che lo possiede; quindi, avremmo avuto inutilmente repliche ridondanti.

  * **Interazioni:**  
    * con il server gRPC.  
    * con il Data Collector.
   





## File Per il Build e il deploy
[Build&Deploy&Setup_info.pdf](https://github.com/user-attachments/files/17950628/Build.Deploy.Setup_info.pdf)

