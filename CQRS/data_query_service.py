
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
        
# Query per ottenere il numero di occorrenze di un ticker
class GetTickerCountQuery:
    def __init__(self,email,conn):
        self.count_ticker_query = """
            SELECT COUNT(*) FROM Data WHERE ticker = (SELECT ticker FROM Users WHERE email = %s) 
        """
        self.email = email
        self.conn = conn      








# Servizio che gestisce le data query
class QueryDataService:
    def handle_get_last_ticker_value(self, query: GetLastTickerValueQuery):
        with query.conn.cursor() as cursor:
              cursor.execute(query.last_value_query,(query.email,))
              return cursor.fetchone()
             
             
    def handle_get_average_ticker_value(self, query: GetAverageTickerValueQuery):
        with query.conn.cursor() as cursor:
              cursor.execute(query.average_values_query,(query.email, query.num_values,))
              return cursor.fetchone()

    def handle_get_ticker_count(self, query: GetTickerCountQuery):
        with query.conn.cursor() as cursor:
              cursor.execute(query.count_ticker_query,(query.email,))
              return cursor.fetchone()[0]



             