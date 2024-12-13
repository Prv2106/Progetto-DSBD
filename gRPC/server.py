import grpc
from concurrent import futures
import usermanagement_pb2
import usermanagement_pb2_grpc
from threading import Lock
import pymysql
import logging
import time
import bcrypt
import users_command_service
import db_config


# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

request_cache = {}  # dizionario di dizionari per consentire il controllo non soltanto sulla richiesta ma anche sull'utente
cache_lock = Lock() # per gestire l'aggiornamento della cache in modo consistente (pool di thread)


# QUERIEs

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


def extract_metadata(context):
    """
    Funzione che estrae i metadati passati lato client.
    """
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

                # Ritorniamo la risposta già processata
                return request_cache[request_id][user_id]
    
    # Nessuna risposta trovata nella cache
    return None


def save_into_cache(request_id, user_id, response):
    """
    Memorizza una risposta nella cache. Se la dimensione totale della cache supera il limite,
    rimuove gli elementi più vecchi.
    """
    max_cache_size = 300  # Limite della cache

    with cache_lock:
        # Aggiungiamo la nuova risposta nella cache
        if request_id not in request_cache:
            request_cache[request_id] = {}

        request_cache[request_id][user_id] = response

        # Controlliamo la dimensione totale della cache
        if len(request_cache) > max_cache_size:
            # Rimuoviamo il primo elemento inserito (FIFO - First In, First Out)
            oldest_request_id = next(iter(request_cache))
            del request_cache[oldest_request_id]

    # Log dello stato della cache
    logger.info(f"Cache aggiornata. Dimensione attuale: {len(request_cache)}")
    logger.info(f"Contenuto della cache:\n {request_cache}")

    
def populate_db():
    """
    Funzione di test che inserisce degli utenti per inizializzare il database.
    """
    pwd = "1234"
    success = False
    while not success:
        try:
            # Apertura della connessione al database
            conn = pymysql.connect(**db_config)
            command_users_service = users_command_service.CommandUsersService()
            command_users_service.handle_register_users(users_command_service.RegisterUsersCommand("utente1@example.com", bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "AAPL",conn))
            command_users_service.handle_register_users(users_command_service.RegisterUsersCommand("utente2@example.com", bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "AMZN",conn))
            command_users_service.handle_register_users(users_command_service.RegisterUsersCommand("utente3@example.com", bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "GOOG",conn))
            success = True
        except pymysql.MySQLError as err:
            if err.args[0] == 1062: # Gli utenti sono stati già inseriti
                success = True # Perché significa che il server è stato riavviato e il database è stato già inizializzato
         
        finally:
            # Chiudi la connessione
            try:
                conn.close()
            except:
                pass
            

    
    

# Implementazione del servizio UserService che estende UserServiceServicer generato da protoc
class UserService(usermanagement_pb2_grpc.UserServiceServicer): 

    # Funzione di registrazione degli utenti
    def RegisterUser(self, request, context):
        logger.info("Funzione richiesta: RegisterUser")
        user_id, request_id = extract_metadata(context)
        
        result = handle_request_cache(request_id, user_id) # vediamo se tale richiesta era già ricevuta dal server (presente nella cache)
        if result: 
            # test per il timeout
            time.sleep(1)
            return result # la restituiamo

        # questa parte del codice a seguire viene eseguita solo se quella da processare è una nuova richiesta

        conn = None  # Inizializziamo conn con None
        try:
            # Logica di registrazione utente
            logger.info(f"Registrazione utente: {request.email}, Ticker: {request.ticker}")

            # Hash della password
            hashed_password = bcrypt.hashpw(request.password.encode('utf-8'), bcrypt.gensalt())
            hashed_password_str = hashed_password.decode('utf-8')  # Convertiamo l'hash in stringa per il database

            # Apertura della connessione al database
            conn = pymysql.connect(**db_config)
           
            command_users_service = users_command_service.CommandUsersService()
            command_users_service.handle_register_users(users_command_service.RegisterUsersCommand(request.email, hashed_password_str, request.ticker,conn))


            # Creazione della risposta di successo
            response = usermanagement_pb2.UserResponse(success=True, message="Utente registrato con successo!")

        except pymysql.MySQLError as err:
            # Gestione degli errori specifici del database
            if err.args[0] == 1062:  # Codice per duplicate entry (email già esistente)
                logger.error(f"Errore di duplicazione, codice di errore: {err}")
                response = usermanagement_pb2.UserResponse(success=False, message="Errore: l'utente con questa email esiste già.")
            else:
                logger.error(f"Errore durante l'inserimento nel database, codice di errore: {err}")
                response = usermanagement_pb2.UserResponse(success=False, message=f"Errore database: {err}")

        except ValueError as e:
            # Gestione degli errori di validazione
            response = usermanagement_pb2.UserResponse(success=False, message= str(e))

        finally:
            # Chiudiamo la connessione al database
            if conn:  # Verifichiamo che conn non sia None
                conn.close()
                
            # Memorizzazione della risposta nella cache
            save_into_cache(request_id, user_id, response)
                
        # test per il timeout
        time.sleep(4)
        return response


    # Funzione per il login degli utenti
    def LoginUser(self, request, context):
        logger.info("Funzione richiesta: LoginUser")
        user_id, request_id = extract_metadata(context)

        
        result = handle_request_cache(request_id, user_id) # vediamo se tale richiesta era già ricevuta dal server (presente nella cache)
        if result:
            # test per il timeout
            #time.sleep(1)
            return result 
        else: # questa parte del codice a seguire viene eseguita solo se quella da processare è una nuova richiesta
            try:
                # Logica di login utente
                logger.info(f"Login utente: {request.email}")
            
                conn = pymysql.connect(**db_config)
                
                # LOGICA DI LOGIN: dapprima verifichiamo che l'email inserita dall'utente sia presente...
                # se l'email è presente allora la password recuperata dal db viene confrontata con quella inviata dall'utente

                query_users_service = users_query_service.QueryUsersService()
                hashed_password_db = query_users_service.handle_get_user_password(users_query_service.GetUserPasswordQuery(request.email,conn))

                if hashed_password_db is None:
                    response = usermanagement_pb2.UserResponse(success=False, message="Email o password non corrette")
                else:
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


    # Funzione per l'aggiornamento del ticker seguito da un utente
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



    # Funzione di eliminazione dell'utente loggato
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
    

    # Funzione di recupero dell'ultimo valore
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
                logger.info(f"Recupero ultimo valore del ticker seguito dall'utente: {request.email}")
            
                conn = pymysql.connect(**db_config)
                with conn.cursor() as cursor:
                    cursor.execute(last_value_query, (request.email))
                    result = cursor.fetchone()
                    if result is None:
                        response = usermanagement_pb2.StockValueResponse(success = False, message = "Nessun valore disponibile per il ticker registrato")
                    else: 
                        timestamp, ticker, value = result
                        logger.info(f"timestamp: {timestamp}, ticker: {ticker}, value: {value}")
                        response = usermanagement_pb2.StockValueResponse(success = True, message = "Valore recuperato", timestamp = str(timestamp), ticker = ticker, value = float(value))

            except pymysql.MySQLError as err:
                # Log dell'errore SQL
                logger.error(f"Errore nel database, codice di errore: {err}")
                response = usermanagement_pb2.StockValueResponse(success=False, message=f"Errore database, codice di errore: {err}")

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
                logger.error(f"Errore nel database, codice di errore: {err}")
                response = usermanagement_pb2.AverageResponse(success=False, message=f"Errore database, codice di errore: {err}")
            
            finally:
                # Chiudiamo la connessione al database
                conn.close()
            
                # Memorizzazione della risposta nella cache
                save_into_cache(request_id, user_id, response)

        # test per il timeout
        #time.sleep(4)
        return response



def initialize():
    try:
        populate_db()
        logger.info("Database inizializzato correttamente.")
    except Exception as e:
        logger.error(f"Errore durante l'inizializzazione del database: {e}")
        raise  # Interrompe l'avvio del server in caso di errori gravi

def serve():
    try:
        # Inizializzazione del database
        initialize()
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
