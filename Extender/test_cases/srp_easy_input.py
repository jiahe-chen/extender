class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
    
    def save_to_database(self):
        print(f"Saving user {self.name} to database")
    
    def send_welcome_email(self):
        print(f"Sending welcome email to {self.email}")