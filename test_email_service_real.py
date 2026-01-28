
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Force development mode to False to test real sending, just in case .env reload is tricky in some contexts
# But since we modified .env, it should be fine. We will check it.
from services.email_service import EmailService

def test_real_email():
    print("Initializing EmailService...")
    service = EmailService()
    
    print(f"Service Configuration:")
    print(f"SMTP Server: {service.smtp_server}")
    print(f"SMTP Port: {service.smtp_port}")
    print(f"Username: {service.username}")
    print(f"Development Mode: {service.development_mode}")
    
    if service.development_mode:
        print("WARNING: Service is still in development mode! Check .env file.")
        
    to_email = "abholzwarth@gmail.com" # Using the user's email from previous context
    subject = "Teste de Envio REAL - Aracannabis SIAP"
    html_body = "<h1>Teste de Envio Real</h1><p>Se você recebeu este email, o sistema de envio real está funcionando corretamente via EmailService.</p>"
    
    print(f"Attempting to send email to {to_email}...")
    success = service.send_email(to_email, subject, html_body)
    
    if success:
        print("Email sent successfully!")
    else:
        print("Failed to send email.")

if __name__ == "__main__":
    test_real_email()
