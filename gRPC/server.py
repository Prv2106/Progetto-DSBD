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
class UserServiceServicer(usermanagement_pb2_grpc.UserServiceServicer): 

    # Servizio per la registrazione degli utenti
    def RegisterUser(self, request, context):
        
        # Estrazione dei metadati dal contesto
        metadata = dict(context.invocation_metadata())
        user_id = metadata.get('user_id', "unknown")
        request_id = metadata.get('request_id', "unknown")

        logger.info(f"Metadati ricevuti: UserId -> {user_id}, RequestID -> {request_id}")

        with cache_lock:
            # Log della cache per il debug
            logger.info("Contenuto della cache (chiave -> valore):")
            for request_id_key, user_cache in request_cache.items():
                for user_id_key, processed in user_cache.items():
                    logger.info(f"RequestID: {request_id_key}, UserID: {user_id_key}, Processato: {processed}")
            
            # Verifichiamo se la richiesta era stata già processata
            if request_id in request_cache:
                if user_id in request_cache[request_id]:
                    logger.info(f"Richiesta già elaborata per l'utente {user_id}")
                    return usermanagement_pb2.UserResponse(success=True, message="Utente già registrato")

        try:
            # Logica di registrazione utente
            logger.info(f"Registrazione utente: {request.email}, Ticker: {request.ticker}")
            conn = pymysql.connect(**db_config)
            with conn.cursor() as cursor:
                cursor.execute(register_user_query, (request.email, request.ticker))
                conn.commit()

            response = usermanagement_pb2.UserResponse(success=True, message="Utente registrato con successo!")

            # Memorizzazione della risposta nella cache
            with cache_lock:
                if request_id not in request_cache:
                    request_cache[request_id] = {}
                request_cache[request_id][user_id] = True

        except pymysql.MySQLError as err:
            logger.error(f"Errore durante l'inserimento nel database: {err}")
            response = usermanagement_pb2.UserResponse(success=False, message=f"Errore database: {err}")
        
        finally:
            # Chiudiamo la connessione al database
            conn.close()
            
        # test per il timeout
        # time.sleep(3)
        return response


def serve():
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        usermanagement_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)

        # Ascolta sulla porta 50051
        server.add_insecure_port('[::]:50051')
        logger.info("Server in ascolto sulla porta 50051...")
        server.start()
        server.wait_for_termination()
    except Exception as e:
        logger.error(f"Errore durante l'avvio del server: {e}")


if __name__ == '__main__':
    serve()
