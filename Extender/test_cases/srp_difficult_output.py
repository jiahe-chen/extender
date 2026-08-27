import datetime
import random
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
    
    def validate_image_file(self, image_data: bytes, file_name: str) -> bool:
        if not image_data or len(image_data) == 0 or len(image_data) > 5 * 1024 * 1024:
            return False
        lower = file_name.lower()
        return lower.endswith((".jpg", ".jpeg", ".png", ".gif"))

class EmailContentService:
    def create_welcome_email_body(self, name: str) -> str:
        return f"Dear {name},\n\nWelcome to our platform! Complete your profile and explore our features.\n\nBest regards,\nThe Team"
    
    def create_password_reset_email_body(self, name: str, token: str) -> str:
        return f"Hello {name},\n\nReset your password: https://oursite.com/reset?token={token}\n\nLink expires in 24 hours."

class TokenGenerationService:
    def generate_password_reset_token(self) -> str:
        timestamp = int(datetime.datetime.now().timestamp() * 1000)
        random_part = str(random.random())[2:8]
        return f"RESET_{timestamp}_{random_part}"
    
    def generate_sms_verification_code(self) -> str:
        return str(random.randint(100000, 999999))

class ValidationService:
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

class PasswordService:
    def hash_password(self, password: str) -> str:
        hash_value = 7
        for char in password:
            hash_value = hash_value * 31 + ord(char)
        return f"HASH:{hex(abs(hash_value))[2:].upper()}"
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        computed_hash = self.hash_password(plain_password)
        return computed_hash == hashed_password

class AuthenticationService:
    def __init__(self):
        self.password_service = PasswordService()
    
    def authenticate(self, user, password: str) -> bool:
        if user.login_attempts >= 5:
            print("Account locked due to too many failed attempts")
            return False
        
        if user.password and self.password_service.verify_password(password, user.password):
            user.reset_login_attempts()
            user.update_last_login()
            user.add_to_login_history("Successful login from IP: 192.168.1.100")
            return True
        
        user.increment_login_attempts()
        user.add_to_login_history("Failed login attempt from IP: 192.168.1.100")
        return False

class SecurityService:
    def log_security_event(self, event_type: str, description: str):
        timestamp = datetime.datetime.now()
        log_entry = f"[{timestamp}] {event_type}: {description}"
        print(f"SECURITY LOG: {log_entry}")
    
    def log_activity_event(self, event_type: str, description: str, user_name: str):
        timestamp = datetime.datetime.now()
        log_entry = f"[{timestamp}] {event_type}: {description} (User: {user_name})"
        print(f"ACTIVITY LOG: {log_entry}")
    
    def log_preference_change(self, key: str, old_value: str, new_value: str):
        log_entry = f"Preference '{key}' changed from '{old_value}' to '{new_value}'"
        print(f"PREFERENCE LOG: {log_entry}")

class AccountService:
    def __init__(self):
        self.security_service = SecurityService()
        self.notification_service = NotificationService()
    
    def lock_account(self, user):
        user.set_active(False)
        self.security_service.log_security_event("ACCOUNT_LOCKED", f"Account locked for user: {user.name}")
        self.notification_service.send_account_notification(user, "Your account has been locked due to security reasons.")
    
    def unlock_account(self, user):
        user.set_active(True)
        user.reset_login_attempts()
        self.security_service.log_security_event("ACCOUNT_UNLOCKED", f"Account unlocked for user: {user.name}")
        self.notification_service.send_account_notification(user, "Your account has been successfully unlocked.")
    
    def delete_account(self, user, db_service: DatabaseService):
        self.security_service.log_security_event("ACCOUNT_DELETION_STARTED", "User initiated account deletion")
        user.set_active(False)
        user.set_email("[DELETED]")
        user.set_password(None)
        user.clear_login_history()
        user.clear_notifications()
        db_service.delete_user(user.name)
        self.security_service.log_security_event("ACCOUNT_DELETED", "Account deletion completed")

class NotificationService:
    def send_account_notification(self, user, message: str):
        user.add_notification(message)
        
        if user.email_verified:
            email_service = EmailService("smtp.company.com", 587)
            email_service.send_email(user.email, "Account Security Alert", message)
        
        if user.phone_number:
            sms_service = SMSService("api_key_12345")
            sms_service.send_sms(user.phone_number, f"Security Alert: {message}")

class ReportService:
    def generate_user_report(self, user) -> str:
        report = []
        report.append("=== USER REPORT ===")
        report.append(f"Name: {user.name}")
        report.append(f"Email: {user.email}")
        report.append(f"Active: {user.is_active}")
        report.append(f"Registration Date: {user.registration_date}")
        report.append(f"Login History: {user.get_login_history_size()} entries")
        return "\n".join(report)

class UserManagementService:
    def __init__(self):
        self.email_service = EmailService("smtp.company.com", 587)
        self.sms_service = SMSService("api_key_12345")
        self.email_content_service = EmailContentService()
        self.token_service = TokenGenerationService()
        self.validation_service = ValidationService()
        self.password_service = PasswordService()
        self.security_service = SecurityService()
    
    def send_welcome_email(self, user):
        subject = "Welcome to our platform!"
        body = self.email_content_service.create_welcome_email_body(user.name)
        self.email_service.send_email(user.email, subject, body)
    
    def send_password_reset_email(self, user):
        reset_token = self.token_service.generate_password_reset_token()
        subject = "Password Reset Request"
        body = self.email_content_service.create_password_reset_email_body(user.name, reset_token)
        self.email_service.send_email(user.email, subject, body)
    
    def send_sms_verification(self, user):
        if user.phone_number:
            sms_code = self.token_service.generate_sms_verification_code()
            message = f"Your verification code: {sms_code}"
            self.sms_service.send_sms(user.phone_number, message)
    
    def change_password(self, user, old_password: str, new_password: str):
        auth_service = AuthenticationService()
        if not auth_service.authenticate(user, old_password):
            raise SecurityError("Current password is incorrect")
        
        if not self.validation_service.validate_password_strength(new_password):
            raise ValueError("New password does not meet strength requirements")
        
        user.set_password(self.password_service.hash_password(new_password))
        self.security_service.log_security_event("PASSWORD_CHANGED", "Password changed successfully")
        
        notification_service = NotificationService()
        notification_service.send_account_notification(user, "Your password has been changed successfully.")
    
    def upload_profile_picture(self, user, image_data: bytes, file_name: str):
        file_service = FileService("/uploads")
        
        if file_service.validate_image_file(image_data, file_name):
            profile_url = file_service.upload_file(image_data, f"profile_{user.name}_{file_name}")
            user.set_profile_picture_url(profile_url)
            self.security_service.log_activity_event("PROFILE_PICTURE_UPLOADED", "User uploaded new profile picture", user.name)
        else:
            raise ValueError("Invalid image file")
    
    def update_preference(self, user, key: str, value: str):
        old_value = user.get_preference(key)
        user.set_preference(key, value)
        self.security_service.log_preference_change(key, old_value, value)

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
        
        self._initialize_default_preferences()
    
    def _initialize_default_preferences(self):
        self.preferences.update({
            "theme": "light",
            "language": "en",
            "notifications": "enabled"
        })
    
    def add_to_login_history(self, entry: str):
        timestamped_entry = f"{datetime.datetime.now()}: {entry}"
        self.login_history.append(timestamped_entry)
        if len(self.login_history) > 100:
            self.login_history.pop(0)
    
    def add_notification(self, message: str):
        timestamped_notification = f"{datetime.datetime.now()}: {message}"
        self.notifications.append(timestamped_notification)
        if len(self.notifications) > 50:
            self.notifications.pop(0)
    
    def clear_login_history(self):
        self.login_history.clear()
    
    def clear_notifications(self):
        self.notifications.clear()
    
    def get_login_history_size(self) -> int:
        return len(self.login_history)
    
    def increment_login_attempts(self):
        self.login_attempts += 1
    
    def reset_login_attempts(self):
        self.login_attempts = 0
    
    def update_last_login(self):
        self.last_login = datetime.datetime.now()
    
    def get_preference(self, key: str) -> str:
        return self.preferences.get(key)
    
    def set_preference(self, key: str, value: str):
        self.preferences[key] = value
    
    def set_active(self, active: bool):
        self.is_active = active
    
    def set_email(self, email: str):
        self.email = email
    
    def set_password(self, password: str):
        self.password = password
    
    def set_profile_picture_url(self, url: str):
        self.profile_picture_url = url
    
    def set_email_verified(self, verified: bool):
        self.email_verified = verified

class SecurityError(Exception):
    pass