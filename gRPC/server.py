import grpc
from concurrent import futures
import usermanagement_pb2
import usermanagement_pb2_grpc
from threading import Lock
import pymysql
import logging
import time
import re
import bcrypt



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

# QUERIES
register_user_query = """
    INSERT INTO Users (email, pwd, ticker)
    VALUES (%s, %s, %s);
"""

login_user_query = """
    SELECT *
    FROM Users
    WHERE email = %s;
"""

update_user_query = """
    UPDATE Users
    SET ticker = %s
    WHERE email = %s;
"""

delete_user_query = """
    DELETE FROM Users
    WHERE email = %s;
"""

last_value_query = """
    SELECT * 
    FROM Data 
    WHERE ticker = (SELECT ticker FROM Users WHERE email = %s)
    ORDER BY timestamp DESC
    LIMIT 1;
"""

average_values_query = """
    SELECT ticker, AVG(valore_euro) AS media_valore
    FROM (
        SELECT *
        FROM Data
        WHERE ticker = (SELECT ticker FROM Users WHERE email = %s) 
        ORDER BY timestamp DESC
        LIMIT %s
     ) AS ultimi_valori
    GROUP BY ticker;
"""

count_ticker_query = """
    SELECT COUNT(*) FROM Data WHERE ticker = (SELECT ticker FROM Users WHERE email = %s) 
"""


def validate_email(email):
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(email_regex, email) is not None

def extract_metadata(context):
    metadata = dict(context.invocation_metadata())

    user_id = metadata.get('user_id', "unknown")
    request_id = metadata.get('request_id', "unknown")

    logger.info(f"Metadati ricevuti: UserId -> {user_id}, RequestID -> {request_id}")
    
    return user_id, request_id


def handle_request_cache(request_id, user_id):
    """
    Gestisce (l'eventuale) recupero di una richiesta già processata dalla cache.
    """
    with cache_lock:
        # Verifichiamo se la richiesta era stata già processata
        if request_id in request_cache:
            if user_id in request_cache[request_id]:
                logger.info(f"Richiesta già elaborata per l'utente {user_id}")

                # Test per il Timeout
                # time.sleep(1)

                # Ritorniamo la risposta già processata
                return request_cache[request_id][user_id]
    
    # Nessuna risposta trovata nella cache
    return None

def save_into_cache(request_id, user_id, response):
    """
    Memorizza una risposta nella cache in modo sicuro utilizzando un lock.
    """
    with cache_lock:
        # Verifica e aggiornamento della cache
        if request_id not in request_cache:
            request_cache[request_id] = {}
        request_cache[request_id][user_id] = response

    # Log dello stato della cache
    logger.info(f"Contenuto della cache:\n {request_cache}")
    
    
    

# Implementazione del servizio UserService che estende UserServiceServicer generato da protoc
class UserService(usermanagement_pb2_grpc.UserServiceServicer): 

    # Servizio per la registrazione degli utenti
    def RegisterUser(self, request, context):
        logger.info("Funzione richiesta: RegisterUser")
        user_id, request_id = extract_metadata(context)

        result = handle_request_cache(request_id, user_id)
        if result:
            # test per il timeout
            time.sleep(1)
            return result 

        conn = None  # Inizializziamo conn con None
        try:
            # Logica di registrazione utente
            logger.info(f"Registrazione utente: {request.email}, Ticker: {request.ticker}")

            # Validazione dei dati
            if not validate_email(request.email):
                logger.error("Email non valida")
                raise ValueError("Email non valida")

            # Hash della password
            hashed_password = bcrypt.hashpw(request.password.encode('utf-8'), bcrypt.gensalt())
            hashed_password_str = hashed_password.decode('utf-8')  # Convertiamo l'hash in stringa per il database

            # Apertura della connessione al database
            conn = pymysql.connect(**db_config)
            with conn.cursor() as cursor:
                cursor.execute(register_user_query, (request.email, hashed_password_str, request.ticker))
                conn.commit()

            # Creazione della risposta di successo
            response = usermanagement_pb2.UserResponse(success=True, message="Utente registrato con successo!")

        except pymysql.MySQLError as err:
            # Gestione degli errori specifici del database
            if err.args[0] == 1062:  # Codice per duplicate entry (violazione chiave univoca)
                logger.error(f"Errore di duplicazione: {err}")
                response = usermanagement_pb2.UserResponse(success=False, message="Errore: l'utente con questa email esiste già.")
            else:
                logger.error(f"Errore durante l'inserimento nel database: {err}")
                response = usermanagement_pb2.UserResponse(success=False, message=f"Errore database: {err}")

        except ValueError as e:
            # Gestione degli errori di validazione
            logger.error("Email non valida")
            response = usermanagement_pb2.UserResponse(success=False, message="Errore: email non valida")

        finally:
            # Chiudiamo la connessione al database
            if conn:  # Verifichiamo che conn non sia None
                conn.close()
                
            # Memorizzazione della risposta nella cache
            save_into_cache(request_id, user_id, response)
                
        # test per il timeout
        time.sleep(4)
        return response

    def LoginUser(self, request, context):
        logger.info("Funzione richiesta: LoginUser")
        user_id, request_id = extract_metadata(context)

        result = handle_request_cache(request_id, user_id)
        if result:
            # test per il timeout
            #time.sleep(1)
            return result 
        else:
            try:
                # Logica di login utente
                logger.info(f"Login utente: {request.email}")
            
                conn = pymysql.connect(**db_config)
                with conn.cursor() as cursor:
                    cursor.execute(login_user_query, (request.email,))
                    result = cursor.fetchone()
                    
                    if result is None:
                        response = usermanagement_pb2.UserResponse(success=False, message="Email o password non corrette")
                    else:
                        _, _, hashed_password_db, _ = result
                        
                        if isinstance(hashed_password_db, str):
                            hashed_password_db = hashed_password_db.encode('utf-8')

                        # Confronto della password
                        if bcrypt.checkpw(request.password.encode('utf-8'), hashed_password_db):
                            response = usermanagement_pb2.UserResponse(success=True, message="Login effettuato con successo")
                        else:
                            response = usermanagement_pb2.UserResponse(success=False, message="Email o password non corrette")

            except ValueError as e:
                logger.error(f"Errore bcrypt, codice di errore: {e}")
                response = usermanagement_pb2.UserResponse(success=False, message="Errore durante il controllo della password")
            except pymysql.MySQLError as err:
                logger.error(f"Errore nel database, codice di errore: {err}")
                response = usermanagement_pb2.UserResponse(success=False, message=f"Errore database, codice di errore: {err}")

            finally:
                # Chiudiamo la connessione al database
                conn.close()
            
                # Memorizzazione della risposta nella cache
                save_into_cache(request_id, user_id, response)
            
        # test per il timeout
        #time.sleep(4)
        return response


    # Servizio per l'aggiornamento del ticker seguito da un utente
    def UpdateUser(self, request, context):
        logger.info("Funzione richiesta: UpdateUser")
        user_id, request_id = extract_metadata(context)

        result = handle_request_cache(request_id, user_id)
        if result:
            # test per il timeout
            #time.sleep(1)
            return result 
        else:
            try:
                # Logica di aggiornamento dell'azione associata a quell'utente
                logger.info(f"Aggiornamento ticker utente: {request.email}, Ticker: {request.new_ticker}")
            
                conn = pymysql.connect(**db_config)
                with conn.cursor() as cursor:
                    cursor.execute(update_user_query, (request.new_ticker, request.email))
                    conn.commit()

                response = usermanagement_pb2.UserResponse(success=True, message="Ticker aggiornato con successo!")

            except pymysql.MySQLError as err:
                logger.error(f"Errore durante l'inserimento nel database: {err}")
                response = usermanagement_pb2.UserResponse(success=False, message=f"Errore database: {err}")

            finally:
                # Chiudiamo la connessione al database
                conn.close()
            
                # Memorizzazione della risposta nella cache
                save_into_cache(request_id, user_id, response)

        # test per il timeout
        #time.sleep(4)
        return response



    # eliminazione dell'utente loggato
    def DeleteUser(self, request, context):
        logger.info("Funzione richiesta: DeleteUser")
        user_id, request_id = extract_metadata(context)

        result = handle_request_cache(request_id, user_id)
        if result:
            # test per il timeout
            #time.sleep(1)
            return result 
        else:
            try:
                logger.info(f"Eliminazione dell'utente: {request.email}")
            
                conn = pymysql.connect(**db_config)
                with conn.cursor() as cursor:
                    cursor.execute(delete_user_query, (request.email))
                    conn.commit()

                response = usermanagement_pb2.UserResponse(success=True, message="Eliminazione avvenuta con successo")

            except pymysql.MySQLError as err:
                # Log dell'errore SQL
                logger.error(f"Errore durante l'eliminazione dell'utente, codice di errore: {err}")
                response = usermanagement_pb2.UserResponse(success=False, message="Errore durante l'eliminazione dell'utente. Riprovare più tardi.")
            
            except Exception as e:
                # Log per errori generici
                logger.error(f"Errore inatteso durante l'eliminazione dell'utente, codice di errore: {e}")
                response = usermanagement_pb2.UserResponse(success=False, message="Si è verificato un errore imprevisto.")

            finally:
                # Chiudiamo la connessione al database
                conn.close()
            
                # Memorizzazione della risposta nella cache
                save_into_cache(request_id, user_id, response)

        # test per il timeout
        #time.sleep(4)
        return response
    

    # recupero dell'ultimo valore
    def GetLatestValue(self, request, context):
        logger.info("Funzione GetLatestValue")
        user_id, request_id = extract_metadata(context)

        result = handle_request_cache(request_id, user_id)
        if result:
            # test per il timeout
            #time.sleep(1)
            return result 
        else:
            try:
                logger.info(f"\nRecupero ultimo valore del ticker seguito dall'utente: {request.email}")
            
                conn = pymysql.connect(**db_config)
                with conn.cursor() as cursor:
                    cursor.execute(last_value_query, (request.email))
                    result = cursor.fetchone()
                    if result is None:
                        response = usermanagement_pb2.StockValueResponse(success = False, message = "Nessun valore disponibile per il ticker registrato")
                    else: 
                        timestamp, ticker, value = result
                        logger.info(f"\timestamp: {timestamp}, ticker: {ticker}, value: {value}")
                        response = usermanagement_pb2.StockValueResponse(success = True, message = "Valore recuperato", timestamp = str(timestamp), ticker = ticker, value = float(value))

            except pymysql.MySQLError as err:
                # Log dell'errore SQL
                logger.error(f"Errore durante il recupero dell'informazione dal database: {err}")
                response = usermanagement_pb2.StockValueResponse(success=False, message="Errore durante il recupero dell'informazione dal database. Riprovare più tardi.")

            finally:
                # Chiudiamo la connessione al database
                conn.close()
            
                # Memorizzazione della risposta nella cache
                save_into_cache(request_id, user_id, response)

        # test per il timeout
        #time.sleep(4)
        return response


    # recupero della media degli X valori
    def GetAverageValue(self, request, context):
        logger.info("Funzione richiesta: GetAverageValue")
        user_id, request_id = extract_metadata(context)

        result = handle_request_cache(request_id, user_id)
        if result:
            # test per il timeout
            #time.sleep(1)
            return result 
        else:
            try:
                logger.info(f"Recupero media degli ultimi {request.num_values} valori del ticker seguito dall'utente: {request.email}")
            
                conn = pymysql.connect(**db_config)
                with conn.cursor() as cursor:
                    cursor.execute(average_values_query, (request.email, request.num_values))
                    result = cursor.fetchone()
                    if result is None:
                        response = usermanagement_pb2.AverageResponse(success = False, message = "Nessun valore disponibile per il ticker registrato")
                    else: 
                        ticker, average = result
                        logger.info(f"ticker: {ticker}, average: {average}")

                        # facciamo anche la query per vedere quante occorrenze ci sono
                        cursor.execute(count_ticker_query, (request.email))
                        count = cursor.fetchone()[0]
                        note_text = ''
                        if count < request.num_values: # se sono presenti nel DB meno valori di quelli indicati
                            note_text = f" N.B: il valore inserito ({request.num_values}) è maggiore al massimo numero di valori presenti nel database ({count}), la media verrà calcolata per {count} valori"

                        response = usermanagement_pb2.AverageResponse(success=True, message=f"Media recuperata con successo {note_text}", ticker = ticker, average = float(average))

            except pymysql.MySQLError as err:
                # Log dell'errore SQL
                logger.error(f"Errore durante il recupero dell'informazione dal database, codice di errore: {err}")
                response = usermanagement_pb2.AverageResponse(success=False, message="Errore durante il recupero dell'informazione dal database. Riprovare più tardi.")
            
            except Exception as e:
                # Log per errori generici
                logger.error(f"Errore inatteso, codice di errore: {e}")
                response = usermanagement_pb2.AverageResponse(success=False, message="Si è verificato un errore imprevisto.")

            finally:
                # Chiudiamo la connessione al database
                conn.close()
            
                # Memorizzazione della risposta nella cache
                save_into_cache(request_id, user_id, response)

        # test per il timeout
        #time.sleep(4)
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
