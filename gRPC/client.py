import grpc
import usermanagement_pb2
import usermanagement_pb2_grpc
import uuid


def register_user(stub):
    # Crea una richiesta per la registrazione utente (modifica i dettagli come desiderato)
    email = input("Inserisci la tua email: ")
    ticker = input("Inserisci il ticker del tuo investimento: ")


    metadata = [
        ('user_id', email),
        ('request_id', str(uuid.uuid4())) 
        
    ]

    max_attempts = 10

    request = usermanagement_pb2.UserRegisterRequest(email=email, ticker=ticker)
    # Meccanismo di "timeout & retry"
    for attempt in range(max_attempts):
        try:
            # Invoca il metodo RegisterUser e ottieni la risposta
            response = stub.RegisterUser(request, metadata = metadata,timeout = 2)
            print(f"\nEsito: {response.success}, Messaggio: {response.message}")
            return
        
        except grpc.RpcError as error:
            if error.code() == grpc.StatusCode.DEADLINE_EXCEEDED: # se è scaduto il timeout
                print("\n############################################################")
                print(f"Timeout superato, tentativo {attempt + 1} di {max_attempts}")
                print("############################################################")
                continue  # Prova un altro tentativo
            
            elif error.code() in {grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.CANCELLED}:
                print(f"Errore: {error}")
                break  # Esce dal ciclo poiché l'errore non è recuperabile
    
    print("Non è stato possibile completare la richiesta")

###########################################################################
# TODO:

def update_user(stub):
    pass

def delete_user(stub):
    pass

def get_last_value(stub):

    email = input("Inserisci la tua email: ")

    metadata = [
        ('user_id', email),
        ('request_id',  str(uuid.uuid4()))
    ]



# TODO: 
    try:
        pass
    except:
        pass
    finally:
        pass




    pass

def calculate_average(stub):
    pass


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
