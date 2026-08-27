from abc import ABC, abstractmethod

class Database(ABC):
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def get_user_email(self, user_id):
        pass

class MySQLDatabase(Database):
    def connect(self):
        print("Connected to MySQL")
    
    def get_user_email(self, user_id):
        return f"user{user_id}@example.com"

class EmailService:
    def __init__(self, database: Database):
        self.database = database
    
    def send_email(self, user_id, message):
        self.database.connect()
        email = self.database.get_user_email(user_id)
        print(f"Sending email to {email}: {message}")
