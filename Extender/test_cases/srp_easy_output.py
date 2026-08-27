class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
    
    def get_name(self):
        return self.name
    
    def get_email(self):
        return self.email


class UserRepository:
    def save(self, user):
        print(f"Saving user {user.get_name()} to database")


class EmailService:
    def send_welcome_email(self, user):
        print(f"Sending welcome email to {user.get_email()}")