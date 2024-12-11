import pymysql
import logging
import re

# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configurazione per il database
db_config = {
    "host": "mysql_container",
    "user": "alberto_giuseppe",
    "password": "progetto",
    "database": "DSBD_progetto"
}



class RegisterUsersCommand:
    def __init__(self, email, hashed_pwd,ticker,conn):
        logger.info("Funzione COMMAND") 

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
        INSERT INTO Users (email, pwd, ticker)
        VALUES (%s, %s, %s);
        """
        self.email =email
        self.hashed_pwd = hashed_pwd
        self.ticker = ticker
        self.conn = conn




    @staticmethod
    def validate_email(email):
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(email_regex, email) is not None
    




        
 


class CommandUsersService:
    
    def handle_register_users(self, command: RegisterUsersCommand):
        # Apertura della connessione al database
        with command.conn.cursor() as cursor:
            cursor.execute(command.register_user_command, (command.email, command.hashed_pwd, command.ticker))
            command.conn.commit()
    
    











class CommandDataService:
    pass
