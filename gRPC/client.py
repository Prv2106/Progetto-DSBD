import grpc
import usermanagement_pb2
import usermanagement_pb2_grpc
import uuid
import time

max_attempts = 20 # numero massimo di tentativi di ritrasmissione
max_retries = 20  # Numero massimo di tentativi di riconnessione
retry_interval = 5  # Intervallo di attesa tra i tentativi di connessione

"""
    la variabile (globale) serve per gestire lo stato di utente loggato... 
    In particolare, se è una stringa vuota il menù del client sarà quello per un utente non loggato;
    diversamente, l'utente è loggato e quindi mostreremo il menù con cui può interagire.
"""
email = '' 


def register_user(stub, channel):
    global email

    # di seguito si chiede all'utente di inserire i dati necessari alla registrazione
    email = input("Inserisci la tua email: ")
    password = input("Inserisci la tua password: ") 
    ticker = input("Inserisci il ticker del tuo investimento: ")
    low_value = -1
    high_value = -1

    metadata = [
        ('user_id', email),
        ('request_id', str(uuid.uuid4())) # generiamo uno uuid4 per garantire l'unicità della richiesta.
    ]

    print("****PARAMETRI OPZIONALI****")

    while True:
        condition = input("Vuoi inserire una soglia minima? [s/n]: ")
        if condition == "s" or condition == "S":
            low_value = int(input("inserisci valore soglia minima: "))
            break
        elif condition == "n" or condition == "N": 
            break
        print("digitare s o n")

    while True:
        condition = input("Vuoi inserire una soglia massima? [s/n]: ")
        if condition == "s" or condition == "S":
            high_value = int(input("inserisci valore soglia massima: "))
            break
        elif condition == "n" or condition == "N": 
            break
        print("digitare s o n")



    print(f"Metadati che verranno passati al server: {metadata}")

    # andiamo a "inizializzare" il messaggio di richiesta del file .proto
    request = usermanagement_pb2.UserRegisterRequest(email=email, password=password, ticker=ticker, low_value = low_value, high_value = high_value)

    # Meccanismo di "timeout & retry"
    for attempt in range(max_attempts):
        try:
             # qui ci interfacciamo con il server (invochiamo la funzione apposita)
            response = stub.RegisterUser(request, timeout = 2, metadata = metadata)
            print(f"\nEsito: {response.success}, Messaggio: {response.message}")
            if response.success is False:
                email = '' # settiamo la variabile globale 'email' a stringa vuota perchè non è avvenuta effettivamente la registrazione (e il conseguente login)
            return
        
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.DEADLINE_EXCEEDED: # se è scaduto il timeout
                print("\n############################################################")
                print(f"Timeout superato, tentativo {attempt + 1} di {max_attempts}")
                print("############################################################")
                continue  # Prova un altro tentativo
            
            # se, durante la richiesta, la connessione col server viene persa, viene ritentata 
            # la connessione e, in caso di successo, la richiesta viene ripetuta.
            elif err.code() == grpc.StatusCode.UNAVAILABLE: 
                print("Errore: server non disponibile")
                wait_for_server(channel)
                continue
            else: # nel caso di altri tipi di errori, la richiesta al server fallisce in maniera non recuperabile.
                print(f"Errore: {err}")
                break

        except ValueError as e: # errori del tipo: email non valida, password vuota o ticker vuoto.
            print(f"Errore: {e}")
            break

    # questa parte di codice viene eseguita nel caso in cui non è possibile eseguire la richiesta
    # cioè, errore irrecuperabile o tentativi superati.
    email = '' 
    print("Non è stato possibile completare la richiesta")


def login_user(stub, channel):
    global email
    email = input("Inserisci la tua email: ")
    password = input("Inserisci la tua password: ") 

    metadata = [
        ('user_id', email),
        ('request_id', str(uuid.uuid4())) 
    ]

    print(f"Metadati che verranno passati al server: {metadata}")

    request = usermanagement_pb2.UserLoginRequest(email=email, password = password)

    for attempt in range(max_attempts):
        try:
            response = stub.LoginUser(request, timeout = 2 ,metadata = metadata)
            print(f"\nEsito: {response.success}, Messaggio: {response.message}")
            if response.success is False:
                email = ''
            return
        
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.DEADLINE_EXCEEDED: # se è scaduto il timeout
                print("\n############################################################")
                print(f"Timeout superato, tentativo {attempt + 1} di {max_attempts}")
                print("############################################################")
                continue  # Prova un altro tentativo
            
            elif err.code() == grpc.StatusCode.UNAVAILABLE:
                print("Errore: server non disponibile")
                wait_for_server(channel)
                continue
            else:
                print(f"Errore: {err}")
                break

    email = ''
    print("Non è stato possibile completare la richiesta")


def update_user(stub, channel):
    # questa funzione può essere chiamata solo dopo che l'utente si sarà loggato,
    # quindi, chiederemo all'utente esclusivamente il nuovo ticker che vorrà seguire
    ticker = input("Inserisci il nuovo ticker: ")

    # i metadati hanno la stessa struttura di quelli della registrazione e login, 
    # con la differenza che qui l'email è quella già inizializzata (in fase di login o registrazione).
    metadata = [
        ('user_id', email),
        ('request_id', str(uuid.uuid4())) 
    ]

    request = usermanagement_pb2.UserUpdateRequest(email=email, new_ticker=ticker)

    for attempt in range(max_attempts):
        try:
            response = stub.UpdateUser(request, timeout = 2 , metadata = metadata)
            print(f"\nEsito: {response.success}, Messaggio: {response.message}")
            return
        
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.DEADLINE_EXCEEDED: # se è scaduto il timeout
                print("\n############################################################")
                print(f"Timeout superato, tentativo {attempt + 1} di {max_attempts}")
                print("############################################################")
                continue  
            
            elif err.code() == grpc.StatusCode.UNAVAILABLE:
                print("Errore: server non disponibile")
                wait_for_server(channel)
                continue
            else:
                print(f"Errore: {err}")
                break

    print("Non è stato possibile completare la richiesta")



def delete_user(stub, channel):
    # questa funzione può essere chiamata solo dopo che l'utente si sarà loggato...
    global email
    metadata = [
        ('user_id', email),
        ('request_id', str(uuid.uuid4())) 
    ]

    request = usermanagement_pb2.UserIdentifier(email=email)

    for attempt in range(max_attempts):
        try:
            response = stub.DeleteUser(request, timeout = 2 , metadata = metadata)
            print(f"\nEsito: {response.success}, Messaggio: {response.message}")
            email = ''
            return
        
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.DEADLINE_EXCEEDED: # se è scaduto il timeout
                print("\n############################################################")
                print(f"Timeout superato, tentativo {attempt + 1} di {max_attempts}")
                print("############################################################")
                continue  # Prova un altro tentativo
            
            elif err.code() == grpc.StatusCode.UNAVAILABLE:
                print("Errore: server non disponibile")
                wait_for_server(channel)
                continue
            else:
                print(f"Errore: {err}")
                break

    print("Non è stato possibile completare la richiesta")


def get_last_value(stub, channel):
    # anche questa funzione verrà chiamata solo dopo che l'utente si sarà loggato

    metadata = [
        ('user_id', email),
        ('request_id', str(uuid.uuid4())) 
    ]

    request = usermanagement_pb2.UserIdentifier(email = email)

    for attempt in range(max_attempts):
        try:
            response = stub.GetLatestValue(request, timeout = 2 , metadata = metadata)
            if response.success:
                print(f"\nTicker: {response.ticker}, Valore: {response.value}, Timestamp: {response.timestamp}")
            else: 
                print(f"\n{response.message}")
            return
        
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                print("\n############################################################")
                print(f"Timeout superato, tentativo {attempt + 1} di {max_attempts}")
                print("############################################################")
                continue 
            
            elif err.code() == grpc.StatusCode.UNAVAILABLE:
                print("Errore: server non disponibile")
                wait_for_server(channel)
                continue
            else:
                print(f"Errore: {err}")
                break

    print("Non è stato possibile completare la richiesta")


def calculate_average(stub, channel):
    # anche questa può essere chiamata solo dopo che l'utente si sarà loggato..

    # metadati 
    metadata = [
        ('user_id', email),
        ('request_id', str(uuid.uuid4())) 
    ]

    num_values = input("Inserisci il numero di valori di cui vuoi venga calcolata la media: ")

    request = usermanagement_pb2.AverageRequest(email=email, num_values=int(num_values))

    for attempt in range(max_attempts):
        try:
            response = stub.GetAverageValue(request, timeout = 2 , metadata = metadata)
            if response.success:
                print(f"\n{response.message}")
                print(f"\nTicker: {response.ticker}, Valore: {response.average}")
            else: 
                print(f"\n{response.message}")
            return
        
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                print("\n############################################################")
                print(f"Timeout superato, tentativo {attempt + 1} di {max_attempts}")
                print("############################################################")
                continue
            
            elif err.code() == grpc.StatusCode.UNAVAILABLE:
                print("Errore: server non disponibile")
                wait_for_server(channel)
                continue
            else:
                print(f"Errore: {err}")
                break

    print("Non è stato possibile completare la richiesta")



#############################################################################

def initial_menu():
    print("\nMenu:")
    print("1. Registrazione Utente")
    print("2. Login Utente")
    print("0. Esci")

def logged_menu():
    print(f"\nAccount: {email}")
    print("Menu:")
    print("1. Aggiorna ticker seguito")
    print("2. Cancella account")
    print("3. Recupero ultimo valore disponibile della mia azione")
    print("4. Calcolo della media degli ultimi valori")
    print("0. Logout")


def wait_for_server(channel, retry_interval=5, max_retries=20):
    """
    Attende che il server gRPC sia disponibile, controllando periodicamente lo stato del canale.

    Spiegazione dei parametri:
    - channel: Il canale gRPC.
    - retry_interval: Intervallo (in secondi) tra i tentativi di riconnessione.
    - max_retries: Numero massimo di tentativi di riconnessione prima di terminare il programma.
    """
    retry_count = 0
    print("\nConnessione al server...")
    while retry_count < max_retries:
        try:
            # Prova a connettersi al server
            grpc.channel_ready_future(channel).result(timeout=10)
            print("Connesso al server!")
            return  # Esce dal loop se la connessione è stabilita
        except grpc.FutureTimeoutError:
            retry_count += 1
            print(f"Connessione al server fallita. Tentativo {retry_count}/{max_retries} di riconnessione...")
            time.sleep(retry_interval)

    # Se il limite di tentativi è raggiunto, termina il programma
    print(f"Impossibile connettersi al server dopo {max_retries} tentativi. Si prega di riprovare più tardi.")
    exit(1)  # Termina il programma


def run():
    global email
    # Connessione al server gRPC in ascolto sulla porta 50051
    with grpc.insecure_channel('localhost:50051') as channel:

        # Attende che il server sia disponibile
        wait_for_server(channel)
     
        # Crea uno stub per il servizio UserService
        stub = usermanagement_pb2_grpc.UserServiceStub(channel)

        while True:
            # Mostra il menu e ottiene la scelta dell'utente
            if len(email) == 0:
                initial_menu()
                choice = input("Scegli un'opzione: ")
                if choice == "1":
                    register_user(stub,channel)
                elif choice == "2":
                    login_user(stub,channel)
                elif choice == "0":
                    print("Uscita...")
                    break
                else:
                    print("Opzione non valida, riprova.")
            else:
                logged_menu()
                choice = input("Scegli un'opzione: ")
                if choice == "1":
                    update_user(stub,channel)
                elif choice == '2':
                    delete_user(stub,channel)
                elif choice == "3":
                    get_last_value(stub,channel)
                elif choice == '4':
                    calculate_average(stub,channel)
                elif choice == "0":
                    email = ''
                else:
                    print("Opzione non valida, riprova.")


if __name__ == '__main__':
    run()
