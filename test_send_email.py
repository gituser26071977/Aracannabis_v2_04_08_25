
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

smtp_server = "smtp.hostinger.com"
smtp_port = 465
username = "contato@arapath.com.br"
password = "S@iArapath12345S@i"
email_from = "aracannabis@arapath.com.br"
email_to = "abholzwarth@gmail.com" # Assuming this is the user's email based on previous files

msg = MIMEMultipart()
msg['From'] = f"Aracannabis Test <{email_from}>"
msg['To'] = email_to
msg['Subject'] = "Teste de Envio SMTP - Aracannabis"

body = "Este é um teste de envio real para verificar se o alias está funcionando."
msg.attach(MIMEText(body, 'plain'))

try:
    print(f"Connecting to {smtp_server}:{smtp_port}...")
    server = smtplib.SMTP_SSL(smtp_server, smtp_port)
    print("Connected. Logging in...")
    server.login(username, password)
    print("Login success. Sending email...")
    server.sendmail(email_from, email_to, msg.as_string())
    server.quit()
    print("Email sent successfully!")
except Exception as e:
    print(f"Failed to send email: {e}")
