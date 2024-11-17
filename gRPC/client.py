import grpc
import usermanagement_pb2
import usermanagement_pb2_grpc
import random



def register_user(stub):
    # Crea una richiesta per la registrazione utente (modifica i dettagli come desiderato)
    email = input("Inserisci la tua email: ")
    ticker = input("Inserisci il ticker del tuo investimento: ")

    metadata = [
        ('user_id', email),
        ('request_id',"register_req") 
    ]

    max_attempts = 20

    # Meccanismo di "timeout & retry"
    for attempt in range(max_attempts):
        request = usermanagement_pb2.UserRegisterRequest(email=email, ticker=ticker)
        try:
            # Invoca il metodo RegisterUser e ottieni la risposta
            response = stub.RegisterUser(request, metadata = metadata,timeout = 2)
            print(f"Esito: {response.success}, Messaggio: {response.message}")
            return
        
        except grpc.RpcError as error:
            if error.code() == grpc.StatusCode.DEADLINE_EXCEEDED: # se è scaduto il timeout
                print(f"Timeout superato, tentativo {attempt + 1} di {max_attempts}")
                continue  # Prova un altro tentativo
            
            elif error.code() in {grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.CANCELLED}:
                print(f"Errore: {error}")
                break  # Esce dal ciclo poiché l'errore non è recuperabile
    
    print("Non è stato possibile completare la richiesta")

###########################################################################
# TODO:

def update_user(stub):
    email = input("Inserisci la tua email per l'aggiornamento: ")
    nuovo_ticker = input("Inserisci il nuovo ticker: ")

    request = usermanagement_pb2.UserUpdateRequest(email=email, nuovo_ticker=nuovo_ticker)
    try:
        response = stub.UpdateUser(request)
        print(f"Esito: {response.success}, Messaggio: {response.message}")
    except grpc.RpcError as error:
        print(f"Errore durante l'aggiornamento: {error}")

def delete_user(stub):
    email = input("Inserisci la tua email per la cancellazione: ")

    request = usermanagement_pb2.UserDeleteRequest(email=email)
    try:
        response = stub.DeleteUser(request)
        print(f"Esito: {response.success}, Messaggio: {response.message}")
    except grpc.RpcError as error:
        print(f"Errore durante la cancellazione: {error}")

def get_last_value(stub):
    ticker = input("Inserisci il ticker per recuperare l'ultimo valore disponibile: ")

    request = usermanagement_pb2.LastValueRequest(ticker=ticker)
    try:
        response = stub.GetLastValue(request)
        print(f"Ultimo valore disponibile: {response.value}")
    except grpc.RpcError as error:
        print(f"Errore durante il recupero del valore: {error}")

def calculate_average(stub):
    ticker = input("Inserisci il ticker per calcolare la media: ")
    x = int(input("Inserisci il numero di ultimi valori da considerare: "))

    request = usermanagement_pb2.AverageRequest(ticker=ticker, count=x)
    try:
        response = stub.CalculateAverage(request)
        print(f"Media degli ultimi {x} valori: {response.average}")
    except grpc.RpcError as error:
        print(f"Errore durante il calcolo della media: {error}")


#############################################################################

def show_menu():
    print("\nMenu:")
    print("1. Registrazione Utente")
    print("2. Aggiornamento Utente")
    print("3. Cancellazione Utente")
    print("4. Recupero Ultimo Valore Disponibile")
    print("5. Calcolo della Media degli Ultimi Valori")
    print("6. Esci")



def run():
       # Connessione al server gRPC in ascolto sulla porta 50051
    with grpc.insecure_channel('localhost:50051') as channel:
        # Crea uno stub per il servizio UserService
        stub = usermanagement_pb2_grpc.UserServiceStub(channel)

        while True:
            # Mostra il menu e ottieni la scelta dell'utente
            show_menu()
            choice = input("Scegli un'opzione: ")
            
            if choice == "1":
                register_user(stub)
            elif choice == "6":
                print("Uscita...")
                break
            else:
                print("Opzione non valida, riprova.")





if __name__ == '__main__':
    run()
