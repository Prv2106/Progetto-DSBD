import grpc
import usermanagement_pb2
import usermanagement_pb2_grpc

def run():
    # Connessione al server gRPC in ascolto sulla porta 50051
    channel = grpc.insecure_channel('server:50051')
    stub = usermanagement_pb2_grpc.UserServiceStub(channel)
    
    # Crea una richiesta per la registrazione utente
    request = usermanagement_pb2.UserRegisterRequest(email="user@example.com", ticker="AAPL")
    
    # Invoca il metodo RegisterUser e ottieni la risposta
    response = stub.RegisterUser(request)
    
    print(f"Success: {response.success}, Message: {response.message}")

if __name__ == '__main__':
    run()
