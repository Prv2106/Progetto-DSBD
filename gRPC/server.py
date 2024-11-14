import grpc
from concurrent import futures
import usermanagement_pb2
import usermanagement_pb2_grpc

# Configurazione per il database degli utenti
db_1_config = {
    "host": "users_db_container",
    "user": "alberto_giuseppe",
    "password": "dsbd_users",
    "database": "DSBD_users"
}

# Configurazione per il database dei dati da collezionare
db_2_config = {
    "host": "data_db_container",
    "user": "alberto_giuseppe",
    "password": "dsbd_data",
    "database": "DSBD_data"
}


# Implementazione del servizio UserService
class UserServiceServicer(usermanagement_pb2_grpc.UserServiceServicer):
    def RegisterUser(self, request, context):
        # Logica di registrazione utente
        print(f"Registrazione utente: {request.email}, Ticker: {request.ticker}")
        # TODO: query database
        response = usermanagement_pb2.UserResponse(success=True, message="User registered successfully by server gRPC!")
        
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    usermanagement_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)
    
    # Ascolta sulla porta 50051
    server.add_insecure_port('[::]:50051')
    print("Server in ascolto sulla porta 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
