import datetime
import random
import hashlib
from typing import Dict, List, Optional

class DatabaseService:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    def save_user(self, user):
        print(f"Saving user to database: {user.name}")
    
    def update_user(self, user):
        print(f"Updating user in database: {user.name}")
    
    def delete_user(self, user_id: str):
        print(f"Deleting user from database: {user_id}")

class EmailService:
    def __init__(self, smtp_server: str, port: int):
        self.smtp_server = smtp_server
        self.port = port
    
    def send_email(self, to: str, subject: str, body: str):
        print(f"Sending email to: {to}")
        print(f"Subject: {subject}")

class SMSService:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def send_sms(self, phone_number: str, message: str):
        print(f"Sending SMS to: {phone_number}")
        print(f"Message: {message}")

class FileService:
    def __init__(self, upload_path: str):
        self.upload_path = upload_path
    
    def upload_file(self, file_data: bytes, file_name: str) -> str:
        print(f"Uploading file: {file_name}")
        return f"{self.upload_path}/{file_name}"

class SecurityConfig:
    MAX_LOGIN_ATTEMPTS = 5
    PASSWORD_EXPIRY_DAYS = 90

class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
        self.password: Optional[str] = None
        self.is_active = True
        self.role = "USER"
        self.last_login: Optional[datetime.datetime] = None
        self.login_attempts = 0
        self.phone_number: Optional[str] = None
        self.registration_date = datetime.datetime.now()
        self.login_history: List[str] = []
        self.preferences: Dict[str, str] = {}
        self.notifications: List[str] = []
        self.profile_picture_url: Optional[str] = None
        self.email_verified = False
        
        self.db_service = DatabaseService("jdbc:mysql://localhost:3306/userdb")
        self.email_service = EmailService("smtp.company.com", 587)
        self.sms_service = SMSService("api_key_12345")
        self.file_service = FileService("/uploads")
        
        self.initialize_default_preferences()
    
    def save_to_database(self):
        self.db_service.save_user(self)
    
    def send_welcome_email(self):
        subject = "Welcome to our platform!"
        body = self.create_welcome_email_body()
        self.email_service.send_email(self.email, subject, body)
    
    def send_password_reset_email(self):
        reset_token = self.generate_password_reset_token()
        subject = "Password Reset Request"
        body = self.create_password_reset_email_body(reset_token)
        self.email_service.send_email(self.email, subject, body)
    
    def send_sms_verification(self):
        if self.phone_number:
            sms_code = self.generate_sms_verification_code()
            message = f"Your verification code: {sms_code}"
            self.sms_service.send_sms(self.phone_number, message)
    
    def create_welcome_email_body(self) -> str:
        return f"Dear {self.name},\n\nWelcome to our platform! Complete your profile and explore our features.\n\nBest regards,\nThe Team"
    
    def create_password_reset_email_body(self, token: str) -> str:
        return f"Hello {self.name},\n\nReset your password: https://oursite.com/reset?token={token}\n\nLink expires in 24 hours."
    
    def generate_password_reset_token(self) -> str:
        timestamp = int(datetime.datetime.now().timestamp() * 1000)
        random_part = str(random.random())[2:8]
        return f"RESET_{timestamp}_{random_part}"
    
    def generate_sms_verification_code(self) -> str:
        return str(random.randint(100000, 999999))
    
    def validate_email_format(self, email: str) -> bool:
        if not email or not email.strip():
            return False
        return "@" in email and "." in email and len(email.split("@")) == 2
    
    def validate_password_strength(self, password: str) -> bool:
        if not password or len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def hash_password(self, password: str) -> str:
        hash_value = 7
        for char in password:
            hash_value = hash_value * 31 + ord(char)
        return f"HASH:{hex(abs(hash_value))[2:].upper()}"
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        computed_hash = self.hash_password(plain_password)
        return computed_hash == hashed_password
    
    def authenticate(self, password: str) -> bool:
        if self.login_attempts >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
            print("Account locked due to too many failed attempts")
            return False
        
        if self.password and self.verify_password(password, self.password):
            self.login_attempts = 0
            self.last_login = datetime.datetime.now()
            self.add_to_login_history("Successful login from IP: 192.168.1.100")
            return True
        
        self.login_attempts += 1
        self.add_to_login_history("Failed login attempt from IP: 192.168.1.100")
        return False
    
    def lock_account(self):
        self.is_active = False
        self.log_security_event("ACCOUNT_LOCKED", f"Account locked for user: {self.name}")
        self.send_account_notification("Your account has been locked due to security reasons.")
    
    def unlock_account(self):
        self.is_active = True
        self.login_attempts = 0
        self.log_security_event("ACCOUNT_UNLOCKED", f"Account unlocked for user: {self.name}")
        self.send_account_notification("Your account has been successfully unlocked.")
    
    def log_security_event(self, event_type: str, description: str):
        timestamp = datetime.datetime.now()
        log_entry = f"[{timestamp}] {event_type}: {description}"
        print(f"SECURITY LOG: {log_entry}")
    
    def send_account_notification(self, message: str):
        self.add_notification(message)
        if self.email_verified:
            self.email_service.send_email(self.email, "Account Security Alert", message)
        if self.phone_number:
            self.sms_service.send_sms(self.phone_number, f"Security Alert: {message}")
    
    def add_to_login_history(self, entry: str):
        timestamped_entry = f"{datetime.datetime.now()}: {entry}"
        self.login_history.append(timestamped_entry)
        if len(self.login_history) > 100:
            self.login_history.pop(0)
    
    def initialize_default_preferences(self):
        self.preferences.update({
            "theme": "light",
            "language": "en",
            "notifications": "enabled"
        })
    
    def update_preference(self, key: str, value: str):
        old_value = self.preferences.get(key)
        self.preferences[key] = value
        self.log_preference_change(key, old_value, value)
    
    def log_preference_change(self, key: str, old_value: str, new_value: str):
        log_entry = f"Preference '{key}' changed from '{old_value}' to '{new_value}'"
        print(f"PREFERENCE LOG: {log_entry}")
    
    def get_preference(self, key: str) -> str:
        return self.preferences.get(key)
    
    def upload_profile_picture(self, image_data: bytes, file_name: str):
        if self.validate_image_file(image_data, file_name):
            self.profile_picture_url = self.file_service.upload_file(image_data, f"profile_{self.name}_{file_name}")
            self.log_activity_event("PROFILE_PICTURE_UPLOADED", "User uploaded new profile picture")
        else:
            raise ValueError("Invalid image file")
    
    def validate_image_file(self, image_data: bytes, file_name: str) -> bool:
        if not image_data or len(image_data) == 0 or len(image_data) > 5 * 1024 * 1024:
            return False
        lower = file_name.lower()
        return lower.endswith((".jpg", ".jpeg", ".png", ".gif"))
    
    def log_activity_event(self, event_type: str, description: str):
        timestamp = datetime.datetime.now()
        log_entry = f"[{timestamp}] {event_type}: {description} (User: {self.name})"
        print(f"ACTIVITY LOG: {log_entry}")
    
    def add_notification(self, message: str):
        timestamped_notification = f"{datetime.datetime.now()}: {message}"
        self.notifications.append(timestamped_notification)
        if len(self.notifications) > 50:
            self.notifications.pop(0)
    
    def change_password(self, old_password: str, new_password: str):
        if not self.authenticate(old_password):
            raise SecurityError("Current password is incorrect")
        
        if not self.validate_password_strength(new_password):
            raise ValueError("New password does not meet strength requirements")
        
        self.password = self.hash_password(new_password)
        self.log_security_event("PASSWORD_CHANGED", "Password changed successfully")
        self.send_account_notification("Your password has been changed successfully.")
    
    def generate_user_report(self) -> str:
        report = []
        report.append("=== USER REPORT ===")
        report.append(f"Name: {self.name}")
        report.append(f"Email: {self.email}")
        report.append(f"Active: {self.is_active}")
        report.append(f"Registration Date: {self.registration_date}")
        report.append(f"Login History: {len(self.login_history)} entries")
        return "\n".join(report)
    
    def delete_account(self):
        self.log_security_event("ACCOUNT_DELETION_STARTED", "User initiated account deletion")
        self.is_active = False
        self.email = "[DELETED]"
        self.password = None
        self.login_history.clear()
        self.notifications.clear()
        self.db_service.delete_user(self.name)
        self.log_security_event("ACCOUNT_DELETED", "Account deletion completed")
    
    def set_password(self, password: str):
        self.password = self.hash_password(password)

class SecurityError(Exception):
    pass