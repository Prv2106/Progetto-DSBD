




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






# Servizio che esegue le users query
class QueryUsersService:
    
    def handle_get_user_password(self, query: GetUserPasswordQuery):
         with query.conn.cursor() as cursor:
              cursor.execute(query.get_password_query,(query.email,))
              result = cursor.fetchone()
              return result[0] if result else None
              
    def handle_get_distinct_users_ticker(self, query: GetDistinctUsersTicker):
        with query.conn.cursor() as cursor:
              cursor.execute(query.get_password_query)
              result = cursor.fetchall()
              if not result:
                  return None
              
              # otteniamo una lista a partire dalla lista di tuple
              # result è una lista di tuple per esempio: [('AAPL',), ('GOOG',), ('TSLA',)]
              tickers = [row[0] for row in result]
              return tickers

