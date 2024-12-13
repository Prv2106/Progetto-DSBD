

# Query per il recupero della password
class GetUserPasswordQuery:
        def __init__(self,email,conn):
            self.get_password_query = """
                SELECT pwd
                FROM Users
                WHERE email = %s;
            """
            self.email = email
            self.conn = conn



# Query per recuperare i ticker (senza duplicati) dalla tabella Users
class GetDistinctUsersTicker:
    def __init__(self,conn):
        self.distinct_ticker_query = """
            SELECT DISTINCT ticker 
            FROM Users;      
        """
        self.conn = conn
        
        
        



# Query per ottenere l'ultimo valore di un ticker
class GetLastTickerValueQuery:
    def __init__(self,email,conn ):
        self.last_value_query= """
            SELECT * 
            FROM Data 
            WHERE ticker = (SELECT ticker FROM Users WHERE email = %s)
            ORDER BY timestamp DESC
            LIMIT 1;
        """
        self.email =email
        self.conn = conn
        
# Query per ottenere il valore medio degli ultimi x valori di un ticker
class GetAverageTickerValueQuery:
    def __init__(self,email, num_values, conn):
        self.average_values_query = """
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
        self.email = email
        self.num_values = num_values
        self.conn = conn
        
# Query per ottenere il numero di occorrenze di un ticker relativamente ad un utente
class GetTickerCountByUserQuery:
    def __init__(self,email,conn):
        self.count_ticker_query = """
            SELECT COUNT(*) FROM Data WHERE ticker = (SELECT ticker FROM Users WHERE email = %s) 
        """
        self.email = email
        self.conn = conn      




# Query per ottenere il numero di occorrenze di un ticker            
class GetEntryCountByTickerQuery:
    def __init__(self,ticker,conn):
        self.count_entry_by_ticker_query = """
           SELECT COUNT(*) 
           FROM Data 
           WHERE ticker = %s
        """
        self.ticker = ticker
        self.conn = conn      







# Servizio che esegue le query
class QueryService:
    
    def handle_get_user_password(self, query: GetUserPasswordQuery):
         with query.conn.cursor() as cursor:
            cursor.execute(query.get_password_query,(query.email,))
            result = cursor.fetchone()
            return result[0] if result else None
              
    def handle_get_distinct_users_ticker(self, query: GetDistinctUsersTicker):
        with query.conn.cursor() as cursor:
              cursor.execute(query.distinct_ticker_query)
              result = cursor.fetchall()
              if not result:
                  return None
              
              # otteniamo una lista a partire dalla lista di tuple
              # result è una lista di tuple per esempio: [('AAPL',), ('GOOG',), ('TSLA',)]
              tickers = [row[0] for row in result]
              return tickers

    def handle_get_last_ticker_value(self, query: GetLastTickerValueQuery):
        with query.conn.cursor() as cursor:
            cursor.execute(query.last_value_query,(query.email,))
            return cursor.fetchone()
             
             
    def handle_get_average_ticker_value(self, query: GetAverageTickerValueQuery):
        with query.conn.cursor() as cursor:
            cursor.execute(query.average_values_query,(query.email, query.num_values,))
            return cursor.fetchone()


    def handle_get_ticker_count_by_user(self, query: GetTickerCountByUserQuery):
        with query.conn.cursor() as cursor:
            cursor.execute(query.count_ticker_query,(query.email,))
            return cursor.fetchone()[0]

    def handle_get_entry_count_by_ticker(self, query: GetEntryCountByTickerQuery):
        with query.conn.cursor() as cursor:
            cursor.execute(query.count_entry_by_ticker_query,(query.ticker,))
            return cursor.fetchone()[0]




