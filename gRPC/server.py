import grpc
from concurrent import futures
import usermanagement_pb2
import usermanagement_pb2_grpc

# Implementazione del servizio UserService
class UserServiceServicer(usermanagement_pb2_grpc.UserServiceServicer):
    def RegisterUser(self, request, context):
        # Logica di registrazione utente
        print(f"Registrazione utente: {request.email}, Ticker: {request.ticker}")
        response = usermanagement_pb2.UserResponse(success=True, message="User registered successfully.")
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
