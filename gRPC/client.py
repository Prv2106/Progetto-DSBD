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
    

def show_menu():
    print("\nMenu:")
    print("1. Registrati")
    print("2. Esci")



def run():
       # Connessione al server gRPC in ascolto sulla porta 50051
    with grpc.insecure_channel('localhost:50051') as channel:
        # Crea uno stub per il servizio UserService
        stub = usermanagement_pb2_grpc.UserServiceStub(channel)

        while True:
            # Mostra il menu e ottieni la scelta dell'utente
            show_menu()
            choice = input("Scegli un'opzione (1 o 2): ")

            if choice == "1":
                register_user(stub)
            elif choice == "2":
                print("Uscita...")
                break
            else:
                print("Opzione non valida, riprova.")





if __name__ == '__main__':
    run()
