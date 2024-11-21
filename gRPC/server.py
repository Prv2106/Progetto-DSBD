import grpc
from concurrent import futures
import usermanagement_pb2
import usermanagement_pb2_grpc
from threading import Lock
import pymysql
import logging
import time

# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

request_cache = {}  # dizionario di dizionari per consentire il controllo non soltanto sulla richiesta ma anche sull'utente
cache_lock = Lock()

# Configurazione per il database
db_config = {
    "host": "mysql_container",
    "user": "alberto_giuseppe",
    "password": "progetto",
    "database": "DSBD_progetto"
}

# QUERYs
register_user_query = """
    INSERT INTO Users (email, ticker)
    VALUES (%s,%s);
"""

# Implementazione del servizio UserService che estende UserServiceServicer generato da protoc
class UserService(usermanagement_pb2_grpc.UserServiceServicer): 

    # Servizio per la registrazione degli utenti
    def RegisterUser(self, request, context):
        
        # Estrazione dei metadati dal contesto
        metadata = dict(context.invocation_metadata())
        user_id = metadata.get('user_id', "unknown")
        request_id = metadata.get('request_id', "unknown")

        logger.info(f"\nMetadati ricevuti: UserId -> {user_id}, RequestID -> {request_id}")
        

        with cache_lock:
            # Verifichiamo se la richiesta era stata già processata
            if request_id in request_cache:
                if user_id in request_cache[request_id]:
                    logger.info(f"\nRichiesta già elaborata per l'utente {user_id}")

                    # Test per il Timeout
                    # time.sleep(1)
                    return request_cache[request_id][user_id] # ritorniamo la risposta già processata
        try:
            # Logica di registrazione utente
            logger.info(f"\nRegistrazione utente: {request.email}, Ticker: {request.ticker}")
        
            conn = pymysql.connect(**db_config)
            with conn.cursor() as cursor:
                cursor.execute(register_user_query, (request.email, request.ticker))
                conn.commit()

            response = usermanagement_pb2.UserResponse(success=True, message="Utente registrato con successo!")

        except pymysql.MySQLError as err:
            if err.args[0] == 1062:  # Codice per duplicate entry (violazione chiave univoca)
                logger.error(f"\nErrore di duplicazione: {err}")
                response = usermanagement_pb2.UserResponse(success=False, message="Errore: l'utente con questa email esiste già.")

            else:
                logger.error(f"\nErrore durante l'inserimento nel database: {err}")
                response = usermanagement_pb2.UserResponse(success=False, message=f"Errore database: {err}")

        finally:
            # Chiudiamo la connessione al database
            conn.close()
                # Log della cache per il debug
        
            # Memorizzazione della risposta nella cache
            with cache_lock:
                if request_id not in request_cache:
                    request_cache[request_id] = {}
                request_cache[request_id][user_id] = response
                
            logger.info("#########################################")
            logger.info(f"Contenuto della cache: {request_cache}")

        
            
        # test per il timeout
        time.sleep(4)
        return response


def serve():
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        usermanagement_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)

        # Ascolta sulla porta 50051
        server.add_insecure_port('[::]:50051')
        logger.info("Server in ascolto sulla porta 50051...")
        server.start()
        server.wait_for_termination()

    except Exception as e:
        logger.error(f"Errore durante l'avvio del server: {e}")


if __name__ == '__main__':
    serve()
