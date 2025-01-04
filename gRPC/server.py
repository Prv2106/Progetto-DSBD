import grpc
from concurrent import futures
import usermanagement_pb2
import usermanagement_pb2_grpc
from threading import Lock
import pymysql
import logging
import time
import bcrypt
import command_service
import query_service
import db_config
import metrics
import redis
from google.protobuf.json_format import MessageToJson
from google.protobuf.json_format import Parse



# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

request_cache = {}  # dizionario di dizionari per consentire il controllo non soltanto sulla richiesta ma anche sull'utente
cache_lock = Lock() # per gestire l'aggiornamento della cache in modo consistente (pool di thread)

# Configurazione di Redis
rdb = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)


def handle_request_cache(request_id, user_id, response_class):
    """
    Gestisce il recupero di una richiesta processata dalla cache Redis.
    """
    try:
        cached_response = rdb.hget(request_id, user_id)
        if cached_response:
            logger.info(f"Richiesta trovata in cache per UserID: {user_id}")
            
            # Converti il JSON di nuovo in un oggetto gRPC
            response = Parse(cached_response, response_class())
            return response
    except Exception as e:
        logger.error(f"Errore durante il recupero o la deserializzazione della risposta: {e}")

    return None

def save_into_cache(request_id, user_id, response):
    """
    Memorizza una risposta nella cache Redis e stampa il contenuto della cache.
    """
    max_cache_size = 300  # Limite della cache

    try:
        # Converti l'oggetto gRPC in JSON
        serialized_response = MessageToJson(response)

        # Salva il JSON in Redis
        rdb.hset(request_id, user_id, serialized_response)
        logger.info(f"Cache Redis aggiornata per RequestID: {request_id}, UserID: {user_id}")

        # Recupera e stampa il contenuto della cache per il request_id
        cache_content = rdb.hgetall(request_id)
        logger.info(f"Contenuto attuale della cache per RequestID: {request_id}: {cache_content}")

        # dimensione attuale della cache
        total_keys = len(rdb.keys())

        if total_keys > max_cache_size:
            oldest_key = sorted(rdb.keys())[0]  # Ordiniamo le chiavi e prendiamo la prima occorrenza
            rdb.delete(oldest_key)
            logger.info(f"Rimossa la chiave più vecchia: {oldest_key}")

        metrics.cache_size.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).set(len(rdb.keys()))
        
        logger.info(f"Cache Redis totale: {total_keys} chiavi memorizzate.")

    except Exception as e:
        logger.error(f"Errore durante la serializzazione o memorizzazione della risposta in Redis: {e}")

def extract_metadata(context):
    """
    Funzione che estrae i metadati passati lato client.
    """
    metadata = dict(context.invocation_metadata())

    user_id = metadata.get('user_id', "unknown")
    request_id = metadata.get('request_id', "unknown")

    logger.info(f"Metadati ricevuti: UserId -> {user_id}, RequestID -> {request_id}")
    
    return user_id, request_id
    
def populate_db():
    """
    Funzione di test che inserisce degli utenti per inizializzare il database.
    """
    pwd = "1234"
    success = False
    while not success:
        try:
            # Apertura della connessione al database
            conn = pymysql.connect(**db_config.db_config)
            service = command_service.CommandService()
            service.handle_register_user(command_service.RegisterUserCommand("provi.al2106@gmail.com", bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "AAPL",150,200,conn))
            service.handle_register_user(command_service.RegisterUserCommand("peppeleocata@gmail.com", bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "AMZN",300,-1,conn))
            service.handle_register_user(command_service.RegisterUserCommand("utente1@example.com", bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "GOOG",-1,-1,conn))
            service.handle_register_user(command_service.RegisterUserCommand("utente2@example.com", bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "TSLA",-1,-1,conn))
            service.handle_register_user(command_service.RegisterUserCommand("utente3@example.com", bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "AMZN",-1,-1,conn))
            service.handle_register_user(command_service.RegisterUserCommand("utente4@example.com", bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), "AAPL",-1,-1,conn))
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
        start_time = time.time()
        metrics.request_total.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

        logger.info("Funzione richiesta: RegisterUser")
        user_id, request_id = extract_metadata(context)
        
        result = handle_request_cache(request_id, user_id, usermanagement_pb2.UserResponse) # vediamo se tale richiesta era già ricevuta dal server (presente nella cache)
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
            conn = pymysql.connect(**db_config.db_config)
           
            service = command_service.CommandService()
            service.handle_register_user(command_service.RegisterUserCommand(request.email, hashed_password_str, request.ticker,request.low_value,request.high_value,conn))


            # Creazione della risposta di successo
            response = usermanagement_pb2.UserResponse(success=True, message="Utente registrato con successo!")
            metrics.success_request.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

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
        # time.sleep(4)
        metrics.response_time_seconds.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).observe(time.time() - start_time)
        return response


    # Funzione per il login degli utenti
    def LoginUser(self, request, context):
        start_time = time.time()
        metrics.request_total.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

        logger.info("Funzione richiesta: LoginUser")
        user_id, request_id = extract_metadata(context)

        
        result = handle_request_cache(request_id, user_id, usermanagement_pb2.UserResponse) # vediamo se tale richiesta era già ricevuta dal server (presente nella cache)
        if result:
            # test per il timeout
            #time.sleep(1)
            return result 
        else: # questa parte del codice a seguire viene eseguita solo se quella da processare è una nuova richiesta
            try:
                # Logica di login utente
                logger.info(f"Login utente: {request.email}")
            
                conn = pymysql.connect(**db_config.db_config)
                
                # LOGICA DI LOGIN: dapprima verifichiamo che l'email inserita dall'utente sia presente...
                # se l'email è presente allora la password recuperata dal db viene confrontata con quella inviata dall'utente

                service = query_service.QueryService()
                hashed_password_db = service.handle_get_user_password(query_service.GetUserPasswordQuery(request.email,conn))

                if hashed_password_db is None:
                    response = usermanagement_pb2.UserResponse(success=False, message="Email o password non corrette")
                    metrics.login_failures_total.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()
                else:
                    if isinstance(hashed_password_db, str):
                            hashed_password_db = hashed_password_db.encode('utf-8')

                    # Confronto della password
                    if bcrypt.checkpw(request.password.encode('utf-8'), hashed_password_db):
                        response = usermanagement_pb2.UserResponse(success=True, message="Login effettuato con successo")
                        metrics.success_request.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()
                    else:
                        response = usermanagement_pb2.UserResponse(success=False, message="Email o password non corrette")
                        metrics.login_failures_total.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

            except ValueError as e:
                logger.error(f"Errore bcrypt, codice di errore: {e}")
                response = usermanagement_pb2.UserResponse(success=False, message="Errore durante il controllo della password")
                metrics.login_failures_total.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

            except pymysql.MySQLError as err:
                logger.error(f"Errore nel database, codice di errore: {err}")
                response = usermanagement_pb2.UserResponse(success=False, message=f"Errore database, codice di errore: {err}")
                metrics.login_failures_total.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

            finally:
                # Chiudiamo la connessione al database
                conn.close()
            
                # Memorizzazione della risposta nella cache
                save_into_cache(request_id, user_id, response)
            
        # test per il timeout
        #time.sleep(4)
        metrics.response_time_seconds.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).observe(time.time() - start_time)
        return response


    # Funzione per l'aggiornamento del ticker seguito da un utente
    def UpdateUser(self, request, context):
        start_time = time.time()
        metrics.request_total.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

        logger.info("Funzione richiesta: UpdateUser")
        user_id, request_id = extract_metadata(context)

        result = handle_request_cache(request_id, user_id, usermanagement_pb2.UserResponse)
        if result:
            # test per il timeout
            #time.sleep(1)
            return result 
        else:
            try:
                # Logica di aggiornamento dell'azione associata a quell'utente
                logger.info(f"Aggiornamento ticker utente: {request.email}, Ticker: {request.new_ticker}")
            
                conn = pymysql.connect(**db_config.db_config)
                service = command_service.CommandService()
                service.handle_update_user_ticker(command_service.UpdateUserTickerCommand(request.new_ticker, request.email,conn))
                
                response = usermanagement_pb2.UserResponse(success=True, message="Ticker aggiornato con successo!")
                metrics.success_request.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

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
        metrics.response_time_seconds.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).observe(time.time() - start_time)
        return response



    # Funzione di eliminazione dell'utente loggato
    def DeleteUser(self, request, context):
        start_time = time.time()
        metrics.request_total.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

        logger.info("Funzione richiesta: DeleteUser")
        user_id, request_id = extract_metadata(context)

        result = handle_request_cache(request_id, user_id, usermanagement_pb2.UserResponse)
        if result:
            # test per il timeout
            #time.sleep(1)
            return result 
        else:
            try:
                logger.info(f"Eliminazione dell'utente: {request.email}")
            
                conn = pymysql.connect(**db_config.db_config)
                
                service = command_service.CommandService()
                service.handle_delete_user(command_service.DeleteUserCommand(request.email,conn))

                response = usermanagement_pb2.UserResponse(success=True, message="Eliminazione avvenuta con successo")
                metrics.success_request.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

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
        metrics.response_time_seconds.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).observe(time.time() - start_time)
        return response
    

    # Funzione di recupero dell'ultimo valore
    def GetLatestValue(self, request, context):
        start_time = time.time()
        metrics.request_total.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

        logger.info("Funzione GetLatestValue")
        user_id, request_id = extract_metadata(context)

        result = handle_request_cache(request_id, user_id, usermanagement_pb2.UserResponse)
        if result:
            # test per il timeout
            #time.sleep(1)
            return result 
        else:
            try:
                logger.info(f"Recupero ultimo valore del ticker seguito dall'utente: {request.email}")
            
                conn = pymysql.connect(**db_config.db_config)
                
                service = query_service.QueryService()
                result = service.handle_get_last_ticker_value(query_service.GetLastTickerValueQuery(request.email,conn))
                if result is None:
                    response = usermanagement_pb2.StockValueResponse(success = False, message = "Nessun valore disponibile per il ticker registrato")
                else: 
                    timestamp, ticker, value = result
                    logger.info(f"timestamp: {timestamp}, ticker: {ticker}, value: {value}")
                    response = usermanagement_pb2.StockValueResponse(success = True, message = "Valore recuperato", timestamp = str(timestamp), ticker = ticker, value = float(value))
                    metrics.success_request.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

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
        metrics.response_time_seconds.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).observe(time.time() - start_time)
        return response


    # recupero della media degli X valori
    def GetAverageValue(self, request, context):
        start_time = time.time()
        metrics.request_total.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

        logger.info("Funzione richiesta: GetAverageValue")
        user_id, request_id = extract_metadata(context)

        result = handle_request_cache(request_id, user_id, usermanagement_pb2.UserResponse)
        if result:
            # test per il timeout
            #time.sleep(1)
            return result 
        else:
            try:
                logger.info(f"Recupero media degli ultimi {request.num_values} valori del ticker seguito dall'utente: {request.email}")
            
                conn = pymysql.connect(**db_config.db_config)
                
                service = query_service.QueryService()
                result = service.handle_get_average_ticker_value(query_service.GetAverageTickerValueQuery(request.email, request.num_values,conn))
                if result is None:
                    response = usermanagement_pb2.AverageResponse(success = False, message = "Nessun valore disponibile per il ticker registrato")
                else: 
                    ticker, average = result
                    logger.info(f"ticker: {ticker}, average: {average}")

                    # facciamo anche la query per vedere quante occorrenze ci sono
                    service = query_service.QueryService()
                    count = service.handle_get_ticker_count_by_user(query_service.GetTickerCountByUserQuery(request.email,conn))

                    note_text = ''
                    if count < request.num_values: # se sono presenti nel DB meno valori di quelli indicati
                        note_text = f" N.B: il valore inserito ({request.num_values}) è maggiore al massimo numero di valori presenti nel database ({count}), la media verrà calcolata per {count} valori"

                    response = usermanagement_pb2.AverageResponse(success=True, message=f"Media recuperata con successo {note_text}", ticker = ticker, average = float(average))
                    metrics.success_request.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

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
        metrics.response_time_seconds.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).observe(time.time() - start_time)
        return response



    def UpdateLowValue(self, request, context):
        start_time = time.time()
        metrics.request_total.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

        logger.info("Funzione richiesta: UpdateLowValue")
        user_id, request_id = extract_metadata(context)

        result = handle_request_cache(request_id, user_id, usermanagement_pb2.UserResponse)
        if result:
            # test per il timeout
            #time.sleep(1)
            return result 
        else:
            try:
                logger.info(f"Aggiornamento low_value utente: {request.email}, low_value: {request.low_value}")
            
                conn = pymysql.connect(**db_config.db_config)
                
                # Verifichiamo se l'utente ha inserito un high_value 
                service = query_service.QueryService()
                high_value = service.handle_get_high_value_by_user(query_service.GetHighValueByUserQuery(request.email,conn))
                
                service = command_service.CommandService()
                service.handle_update_low_value_by_user(command_service.UpdateLowValueByUserCommand(request.email, request.low_value, high_value,conn))
                
                response = usermanagement_pb2.UserResponse(success=True, message="low_value aggiornato con successo!")
                metrics.success_request.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

            except pymysql.MySQLError as err:
                logger.error(f"Errore nel database, codice di errore: {err}")
                response = usermanagement_pb2.UserResponse(success=False, message=f"Errore database, codice di errore: {err}")
            except ValueError as e:
                response = usermanagement_pb2.UserResponse(success=False, message= str(e))

            finally:
                # Chiudiamo la connessione al database
                conn.close()
            
                # Memorizzazione della risposta nella cache
                save_into_cache(request_id, user_id, response)

        # test per il timeout
        #time.sleep(4)
        metrics.response_time_seconds.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).observe(time.time() - start_time)
        return response


    def UpdateHighValue(self, request, context):
        start_time = time.time()
        metrics.request_total.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

        logger.info("Funzione richiesta: UpdateHighValue")
        user_id, request_id = extract_metadata(context)

        result = handle_request_cache(request_id, user_id, usermanagement_pb2.UserResponse)
        if result:
            # test per il timeout
            #time.sleep(1)
            return result 
        else:
            try:
                logger.info(f"Aggiornamento high_value utente: {request.email}, low_value: {request.high_value}")
            
                conn = pymysql.connect(**db_config.db_config)
                
                # Verifichiamo se l'utente ha inserito un low_value 
                service = query_service.QueryService()
                low_value = service.handle_get_low_value_by_user(query_service.GetLowValueByUserQuery(request.email,conn))
                
                service = command_service.CommandService()
                service.handle_update_high_value_by_user(command_service.UpdateHighValueByUserCommand(request.email, request.high_value, low_value,conn))
                
                response = usermanagement_pb2.UserResponse(success=True, message="high_value aggiornato con successo!")
                metrics.success_request.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

            except pymysql.MySQLError as err:
                logger.error(f"Errore nel database, codice di errore: {err}")
                response = usermanagement_pb2.UserResponse(success=False, message=f"Errore database, codice di errore: {err}")
                
            except ValueError as e:
                response = usermanagement_pb2.UserResponse(success=False, message= str(e))

            finally:
                # Chiudiamo la connessione al database
                conn.close()
            
                # Memorizzazione della risposta nella cache
                save_into_cache(request_id, user_id, response)

        # test per il timeout
        #time.sleep(4)
        metrics.response_time_seconds.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).observe(time.time() - start_time)
        return response


    def ShowDetails(self, request, context):
        start_time = time.time()
        metrics.request_total.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

        logger.info("Funzione richiesta: ShowDetails")
        user_id, request_id = extract_metadata(context)

        result = handle_request_cache(request_id, user_id, usermanagement_pb2.UserResponse)
        if result:
            # test per il timeout
            #time.sleep(1)
            return result 
        else:
            try:
                conn = pymysql.connect(**db_config.db_config)
                
                service = query_service.QueryService()
                ticker,low_value,high_value = service.handle_get_user_details(query_service.GetUserDetailsQuery(request.email,conn))
            
                response = usermanagement_pb2.DetailsResponse(success=True, ticker = ticker, low_value = low_value, high_value = high_value)
                metrics.success_request.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).inc()

            except pymysql.MySQLError as err:
                logger.error(f"Errore nel database, codice di errore: {err}")
                response = usermanagement_pb2.UserResponse(success=False, message=f"Errore database, codice di errore: {err}")
                
            except ValueError as e:
                response = usermanagement_pb2.UserResponse(success=False, message= str(e))

            finally:
                # Chiudiamo la connessione al database
                conn.close()
            
                # Memorizzazione della risposta nella cache
                save_into_cache(request_id, user_id, response)

        # test per il timeout
        #time.sleep(4)
        metrics.response_time_seconds.labels(uservice=metrics.APP_NAME, hostname=metrics.HOSTNAME).observe(time.time() - start_time)
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
    metrics.prometheus_client.start_http_server(9999) # per permettere a Prometheus a fare le richieste di Pull
    logger.info(f"Le metriche relative al Server gRPC sono disponibili sull'interfaccia web di Prometheus")
    serve()