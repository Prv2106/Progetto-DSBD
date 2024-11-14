import pymysql

# Configurazione per il database degli utenti
db_config = {
    "host": "mysql_container",
    "user": "alberto_giuseppe",
    "password": "progetto",
    "database": "DSBD_progetto"
}

# Query per creare la tabella Users
create_users_table_query = """
CREATE TABLE IF NOT EXISTS Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    ticker VARCHAR(50) NOT NULL
);
"""

# Query per creare la tabella Data
create_data_table_query = """
CREATE TABLE IF NOT EXISTS Data (
    timestamp DATETIME NOT NULL,
    id INT NOT NULL,
    ticker VARCHAR(50) NOT NULL,
    valore_euro DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (timestamp, id, ticker),
    FOREIGN KEY (id) REFERENCES Users(id)
);
"""

# Query per inserire i dati iniziali nella tabella Users
insert_query_users = """
INSERT INTO Users (email, ticker)
VALUES (%s, %s)
ON DUPLICATE KEY UPDATE email = email;
"""

# Query per contare le righe nella tabella Users
count_query_users = "SELECT COUNT(*) FROM Users;"

def mysqlInit():
    try:
        # Connessione al database
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        # Creazione della tabella Users
        cursor.execute(create_users_table_query)
        print("Tabella Users creata con successo (o già esistente).")

        # Creazione della tabella Data
        cursor.execute(create_data_table_query)
        print("Tabella Data creata con successo (o già esistente).")

        # Verifica se la tabella Users è vuota
        cursor.execute(count_query_users)
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Inserimento delle ricorrenze iniziali nella tabella Users
            initial_users = [
                ("user1@example.com", "AAPL"),
                ("user2@example.com", "GOOGL"),
                ("user3@example.com", "MSFT"),
                ("user4@example.com", "TSLA")
            ]

            for user in initial_users:
                cursor.execute(insert_query_users, user)
            
            # Commit delle modifiche
            conn.commit()
            print("Dati iniziali inseriti con successo nella tabella Users.")
        else:
            print("La tabella Users non è vuota. Nessun dato inserito.")

    except pymysql.MySQLError as e:
        print(f"Errore durante l'esecuzione: {e}")
    finally:
        # Chiusura della connessione al database
        if conn:
            cursor.close()
            conn.close()
            print("Connessione chiusa.")

if __name__ == "__main__":
    mysqlInit()