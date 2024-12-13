import pymysql
import logging
import re


# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Command per la registrazione dell'utente
class RegisterUserCommand:
    def __init__(self, email, hashed_pwd, ticker, low_value, high_value, conn):
         # verifica che la password non sia vuota
        if not hashed_pwd:
            logger.error("password non inserita")
            raise ValueError("password non inserita")
        
        # verifica che sia stato inserito un ticker
        if not ticker:
                logger.error("ticker non inserito")
                raise ValueError("ticker non inserito")
        
        
        # Validazione dell'email
        if not self.validate_email(email):
            logger.error("Email non valida")
            raise ValueError("Email non valida")
        
        self.register_user_command = """
        INSERT INTO Users (email, pwd, ticker, low_value, high_value)
        VALUES (%s, %s, %s, %s, %s);
        """
        self.email = email
        self.hashed_pwd = hashed_pwd
        self.ticker = ticker
        self.low_value = low_value
        self.high_value = high_value
        self.conn = conn




    @staticmethod
    def validate_email(email):
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(email_regex, email) is not None
    
    
    
# Command per l'aggiornamento del ticker di un utente
class UpdateUserTickerCommand:
    def __init__(self,new_ticker,email,conn):
            
        self.update_user_ticker_command = """
            UPDATE Users
            SET ticker = %s
            WHERE email = %s;
        """
        self.new_ticker = new_ticker
        self.email = email
        self.conn = conn





# Command per l'eliminazione di un utente
class DeleteUserCommand:
    def __init__(self,email,conn):
    
        self.delete_user_command = """
            DELETE FROM Users
            WHERE email = %s;
        """
        self.email = email
        self.conn = conn



# Command per la cancellazione dei ticker
class DeleteTickerCommand:
    def __init__(self,ticker,conn):
        self.delete_unused_tickers_command = """
            DELETE FROM Data
            WHERE ticker = %s
        """
        self.ticker = ticker
        self.conn = conn

# Command per l'inserimento dei ticker
class InsertTickerCommand:
    def __init__(self, timestamp,ticker,price_in_eur,conn):
        self.insert_ticker_command = """
            INSERT INTO Data (timestamp, ticker, valore_euro)
            VALUES (%s, %s, %s);
        """
        self.timestamp = timestamp
        self.ticker = ticker
        self.price_in_eur = price_in_eur
        self.conn = conn


# Command per la rimozione dell'entry più vecchia per un dato ticker
class DeleteOldEntryByTicker:
    def _init__(self,ticker,conn):
        self.delete_old_entry_by_ticker_command = """
            DELETE FROM Data
            WHERE (ticker, timestamp) IN (
            SELECT * FROM (
                SELECT ticker, MIN(timestamp) AS oldest_timestamp
                FROM Data
                WHERE ticker = %s
                GROUP BY ticker
            ) AS subquery
        );

        """
        
        self.ticker = ticker
        self.conn = conn



    
 

# Servizio che gestisce i command
class CommandService:
    
    def handle_register_user(self, command: RegisterUserCommand):
        # Apertura della connessione al database
        with command.conn.cursor() as cursor:
            cursor.execute(command.register_user_command, (command.email, command.hashed_pwd, command.ticker,command.low_value,command.high_value,))
            command.conn.commit()
    
    
    def handle_update_user_ticker(self, command: UpdateUserTickerCommand):
        with command.conn.cursor() as cursor:
            cursor.execute(command.update_user_ticker_command, (command.new_ticker, command.email,))
            command.conn.commit()


    def handle_delete_user(self, command: DeleteUserCommand):
        with command.conn.cursor() as cursor:
            cursor.execute(command.delete_user_command, (command.email,))
            command.conn.commit()


    def handle_delete_tickers(self, command: DeleteTickerCommand):
        with command.conn.cursor() as cursor:
            cursor.execute(command.delete_unused_tickers_command, (command.ticker,))
            command.conn.commit()
            
            
    def handle_insert_tickers(self, command: InsertTickerCommand):
        with command.conn.cursor() as cursor:
            cursor.execute(command.insert_ticker_command, (command.timestamp, command.ticker,command.price_in_eur,))
            command.conn.commit()



    def handle_delete_old_entries_by_ticker(self, command: DeleteOldEntryByTicker):
        with command.conn.cursor() as cursor:
            cursor.execute(command.delete_old_entry_by_ticker_command, (command.ticker,))
            command.conn.commit()

