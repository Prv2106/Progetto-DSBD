import grpc
import usermanagement_pb2
import usermanagement_pb2_grpc

def register_user(stub):
    # Crea una richiesta per la registrazione utente (modifica i dettagli come desiderato)
    email = input("Inserisci la tua email: ")
    ticker = input("Inserisci il ticker del tuo investimento: ")

    request = usermanagement_pb2.UserRegisterRequest(email=email, ticker=ticker)
    
    # Invoca il metodo RegisterUser e ottieni la risposta
    response = stub.RegisterUser(request)
    
    print(f"Success: {response.success}, Message: {response.message}")
    

def show_menu():
    print("\nMenu:")
    print("1. Registrati")
    print("2. Esci")

def run():
    # Connessione al server gRPC in ascolto sulla porta 50051
    channel = grpc.insecure_channel('localhost:50051')
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
