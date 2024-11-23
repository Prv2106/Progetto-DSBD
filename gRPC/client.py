import grpc
import usermanagement_pb2
import usermanagement_pb2_grpc
import uuid

max_attempts = 10

email = ''


def register_user(stub):
    # Crea una richiesta per la registrazione utente (modifica i dettagli come desiderato)
    global email
    email = input("Inserisci la tua email: ")
    ticker = input("Inserisci il ticker del tuo investimento: ")


    metadata = [
        ('user_id', email),
        ('request_id', str(uuid.uuid4())) 
    ]
    print(f"Metadati che verranno passati al server: {metadata}")

    request = usermanagement_pb2.UserRegisterRequest(email=email, ticker=ticker)

    # Meccanismo di "timeout & retry"
    for attempt in range(max_attempts):
        try:
            response = stub.RegisterUser(request, timeout = 2 ,metadata = metadata)
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
                print(f"Errore: {err}")
                break  # Esce dal ciclo poiché l'errore non è recuperabile

    email = ''
    print("Non è stato possibile completare la richiesta")


def login_user(stub):
    global email
    email = input("Inserisci la tua email: ")

    metadata = [
        ('user_id', email),
        ('request_id', str(uuid.uuid4())) 
    ]

    print(f"Metadati che verranno passati al server: {metadata}")

    request = usermanagement_pb2.UserIdentifier(email=email)

    # Meccanismo di "timeout & retry"
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
                print(f"Errore: {err}")
                break  # Esce dal ciclo poiché l'errore non è recuperabile
    
    email = ''
    print("Non è stato possibile completare la richiesta")


def update_user(stub):
    # questa funzione verrà chiamata solo dopo che l'utente si sarà loggato,
    # quindi, chiederemo all'utente esclusivamente il nuovo ticker che vorrà seguire
    ticker = input("Inserisci il nuovo ticker: ")

    # i metadati saranno uguali alla registrazione, ma l'email è quella inizializzata
    metadata = [
        ('user_id', email),
        ('request_id', str(uuid.uuid4())) 
    ]

    # andiamo a "inizializzare" il messaggio di richiesta del file .proto
    request = usermanagement_pb2.UserUpdateRequest(email=email, new_ticker=ticker)

    # Meccanismo di "timeout & retry"
    for attempt in range(max_attempts):
        try:
            # qui ci interfacciamo con il server (invochiamo la funzione apposita)
            response = stub.UpdateUser(request, timeout = 2 , metadata = metadata)
            print(f"\nEsito: {response.success}, Messaggio: {response.message}")
            return
        
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.DEADLINE_EXCEEDED: # se è scaduto il timeout
                print("\n############################################################")
                print(f"Timeout superato, tentativo {attempt + 1} di {max_attempts}")
                print("############################################################")
                continue  # Prova un altro tentativo
            
            elif err.code() == grpc.StatusCode.UNAVAILABLE:
                print(f"Errore: {err}")
                break  # Esce dal ciclo poiché l'errore non è recuperabile
    
    print("Non è stato possibile completare la richiesta")



def delete_user(stub):
    # questa funzione verrà chiamata solo dopo che l'utente si sarà loggato...

    # metadati 
    metadata = [
        ('user_id', email),
        ('request_id', str(uuid.uuid4())) 
    ]

    # andiamo a "inizializzare" il messaggio di richiesta del file .proto
    request = usermanagement_pb2.UserIdentifier(email=email)

    # Meccanismo di "timeout & retry"
    for attempt in range(max_attempts):
        try:
            # qui ci interfacciamo con il server (invochiamo la funzione apposita)
            response = stub.DeleteUser(request, timeout = 2 , metadata = metadata)
            print(f"\nEsito: {response.success}, Messaggio: {response.message}")
            return response.success
        
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.DEADLINE_EXCEEDED: # se è scaduto il timeout
                print("\n############################################################")
                print(f"Timeout superato, tentativo {attempt + 1} di {max_attempts}")
                print("############################################################")
                continue  # Prova un altro tentativo
            
            elif err.code() == grpc.StatusCode.UNAVAILABLE:
                print(f"Errore: {err}")
                break  # Esce dal ciclo poiché l'errore non è recuperabile
    
    print("Non è stato possibile completare la richiesta")


def get_last_value(stub):
    # anche questa funzione verrà chiamata solo dopo che l'utente si sarà loggato

    # metadati 
    metadata = [
        ('user_id', email),
        ('request_id', str(uuid.uuid4())) 
    ]

    # andiamo a "inizializzare" il messaggio di richiesta del file .proto
    request = usermanagement_pb2.UserIdentifier(email = email)

    # Meccanismo di "timeout & retry"
    for attempt in range(max_attempts):
        try:
            # qui ci interfacciamo con il server (invochiamo la funzione apposita)
            response = stub.GetLatestValue(request, timeout = 2 , metadata = metadata)
            if response.success:
                print(f"\nTicker: {response.ticker}, Valore: {response.value}, Timestamp: {response.timestamp}")
            else: 
                print(f"\n{response.message}")
            return
        
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.DEADLINE_EXCEEDED: # se è scaduto il timeout
                print("\n############################################################")
                print(f"Timeout superato, tentativo {attempt + 1} di {max_attempts}")
                print("############################################################")
                continue  # Prova un altro tentativo
            
            elif err.code() == grpc.StatusCode.UNAVAILABLE:
                print(f"Errore: {err}")
                break  # Esce dal ciclo poiché l'errore non è recuperabile
    
    print("Non è stato possibile completare la richiesta")


def calculate_average(stub):
    # anche questa  verrà chiamata solo dopo che l'utente si sarà loggato..

    # metadati 
    metadata = [
        ('user_id', email),
        ('request_id', str(uuid.uuid4())) 
    ]

    num_values = input("Inserisci il numero di valori di cui vuoi venga calcolata la media: ")

    # andiamo a "inizializzare" il messaggio di richiesta del file .proto
    request = usermanagement_pb2.AverageRequest(email=email, num_values=int(num_values))

    # Meccanismo di "timeout & retry"
    for attempt in range(max_attempts):
        try:
            # qui ci interfacciamo con il server (invochiamo la funzione apposita)
            response = stub.GetAverageValue(request, timeout = 2 , metadata = metadata)
            if response.success:
                print(f"\n {response.message}")
                print(f"\nTicker: {response.ticker}, Valore: {response.average}")

            else: 
                print(f"\n{response.message}")
            return
        
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.DEADLINE_EXCEEDED: # se è scaduto il timeout
                print("\n############################################################")
                print(f"Timeout superato, tentativo {attempt + 1} di {max_attempts}")
                print("############################################################")
                continue  # Prova un altro tentativo
            
            elif err.code() == grpc.StatusCode.UNAVAILABLE:
                print(f"Errore: {err}")
                break  # Esce dal ciclo poiché l'errore non è recuperabile
    
    print("Non è stato possibile completare la richiesta")


#############################################################################

def initial_menu():
    print("\nMenu:")
    print("1. Registrazione Utente")
    print("2. Login Utente")
    print("0. Esci")

def logged_menu():
    print("\nMenu:")
    print("1. Aggiorna ticker seguito")
    print("2. Cancellami")
    print("3. Recupero Ultimo Valore Disponibile")
    print("4. Calcolo della Media degli Ultimi Valori")
    print("0. Logout")



def run():
    global email
    # Connessione al server gRPC in ascolto sulla porta 50051
    with grpc.insecure_channel('localhost:50051') as channel:
        # Crea uno stub per il servizio UserService
        stub = usermanagement_pb2_grpc.UserServiceStub(channel)

        while True:
            # Mostra il menu e ottieni la scelta dell'utente
            if len(email) == 0:
                initial_menu()
                # 1. Registrazione Utente
                # 2. Login Utente
                # 0. Esci
                choice = input("Scegli un'opzione: ")
                if choice == "1":
                    register_user(stub)
                elif choice == "2":
                    login_user(stub)
                elif choice == "0":
                    print("Uscita...")
                    break
                else:
                    print("Opzione non valida, riprova.")
            else:
                logged_menu()
                # 1. Aggiorna ticker seguito
                # 2. Cancellami
                # 3. Recupero ultimo valore disponibile
                # 4. Calcolo della Media degli Ultimi Valori
                # 0. Logout
                choice = input("Scegli un'opzione: ")
                if choice == "1":
                    update_user(stub)
                elif choice == '2':
                    if delete_user(stub):
                        email = ''
                elif choice == "3":
                    get_last_value(stub)
                elif choice == '4':
                    calculate_average(stub)
                elif choice == "0":
                    email = ''
                else:
                    print("Opzione non valida, riprova.")


if __name__ == '__main__':
    run()
