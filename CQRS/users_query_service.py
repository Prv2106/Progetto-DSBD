




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










# Servizio che esegue le users query
class QueryUsersService:
    
    def handle_get_user_password(self, query: GetUserPasswordQuery):
         with query.conn.cursor() as cursor:
              cursor.execute(query.get_password_query,(query.email,))
              result = cursor.fetchone()
              return result[0] if result else None
              


