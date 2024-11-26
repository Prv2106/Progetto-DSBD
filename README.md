# Progetto DSBD
## Descrizione Applicazione

Il progetto implementa un'architettura per la gestione di utenti e di dati finanziari mediante:
- Un **server gRPC**
- Un **database MySQL**
- Un **Data Collector** con richieste verso il fornitore di servizi remoti Yahoo! Finance, protette dal **Pattern Circuit Breaker**

### Obiettivi
Ottimizzare la gestione distribuita di utenti e dati finanziari utilizzando un'architettura resiliente, tramite:
- Consolidamento delle richieste per ticker comuni.
- Politica **"at-most-once"** per la gestione degli utenti e il recupero delle informazioni.
- Aggiornamenti ciclici dei dati sui titoli seguiti dagli utenti.

### Caratteristiche principali del Data Collector
1. Comportamento adattivo nella frequenza delle richieste.
2. Limite massimo di dati per ogni ticker.
3. Pulizia dei dati inutilizzati.
4. Aggiornamento periodico dei valori per i ticker.

Il **Circuit Breaker** gestisce i malfunzionamenti con tre stati principali:
- **CLOSED**: tutte le richieste sono consentite.
- **OPEN**: le richieste sono bloccate.
- **HALF OPEN**: vengono testate alcune richieste per verificare la stabilità del servizio.

---

## Scelte Progettuali

### Schema Architetturale
![Schema Architetturale](5AC03E93-F9EA-4DB6-A382-C7E876AF345D.jpeg)

L'architettura è composta da **due microservizi principali**:
1. **Server gRPC**: gestisce le richieste degli utenti.
2. **Data Collector + Circuit Breaker**: raccoglie i dati da Yahoo! Finance.

#### Motivazioni della scelte:
- **Separazione delle responsabilità**: ogni microservizio ha compiti specifici.
- **Semplicità e manutenibilità**: l'utilizzo di due container Docker evita complessità inutili.
- **Isolamento**: i microservizi comunicano solo attraverso il database condiviso.

### Interazioni tra i componenti
I due microservizi comunicano indirettamente tramite il database MySQL, che centralizza i dati degli utenti e dei ticker.

---

## Microservizi e loro Interazioni

### Server gRPC
- **Container**: `grpc_server_container` (rete `net1`)
- **Port Mapping**: `50051:50051`
- **Politica "at-most-once"**:
  - Cache strutturata come dizionario di dizionari.
  - Limite massimo di 300 elementi nella cache.
  - Meccanismo di pulizia per eliminare gli elementi più vecchi.

#### API esposte:
1. **RegisterUser**: registra un utente (email, password, ticker).
2. **LoginUser**: consente l'accesso di un utente.
3. **UpdateUser**: aggiorna il ticker dell'utente.
4. **DeleteUser**: elimina l'account dell'utente.
5. **GetLatestValue**: restituisce l'ultimo valore aggiornato per il ticker.
6. **GetAverageValue**: calcola la media di un numero specificato di valori.

### Client gRPC
- Stabilisce la connessione solo se il server è disponibile.
- Meccanismo di **timeout** e **retry** per garantire robustezza.
- **Menu**:
  1. Inizializzazione: registrazione/login.
  2. Utente loggato: gestione ticker, cancellazione account, recupero valori.

### Data Collector
![Data Collector](AEEC651B-9CB0-4C6F-9768-29858F810302.jpeg)

- **Container**: `break_collector_container`
- **Comportamento adattivo**:
  - Frequenza iniziale rapida (2 secondi), ridotta fino a 1 ora dopo 300 cicli.
- **Gestione dati**:
  - Limite massimo di 200 valori per ogni ticker.
  - Pulizia dei dati non più utilizzati.
  - Aggiornamento periodico dei valori da Yahoo! Finance.

### Circuit Breaker
- **Stati**:
  1. **CLOSED**: tutte le richieste passano.
  2. **OPEN**: richieste bloccate per 30 secondi.
  3. **HALF OPEN**: test limitato con richieste parziali.
- Robusto contro malfunzionamenti prolungati del servizio.

### Database MySQL
- **Container**: `mysql_container`
- **Tabelle**:
  1. **Users**: include password hash per maggiore sicurezza.
  2. **Data**: registra i valori dei ticker.
- **Interazioni**:
  - Con il server gRPC.
  - Con il Data Collector.

---

## Struttura dei File e Deploy
1. **Server gRPC**:
   - Cartella: `grpc_server`
   - Porta: `50051`
2. **Data Collector e Circuit Breaker**:
   - Cartella: `data_collector`
3. **Database**:
   - Cartella: `mysql`
   - Configurazioni: file `.env` per credenziali.

---

## Conclusioni
Il progetto fornisce una base solida per la gestione di dati finanziari distribuiti. L'architettura modulare e resiliente garantisce efficienza e scalabilità, mentre l'implementazione del Circuit Breaker e del Data Collector ne rafforzano la robustezza.
