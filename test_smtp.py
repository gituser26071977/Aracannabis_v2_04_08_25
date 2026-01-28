
import smtplib
import os
import sys

smtp_server = "smtp.hostinger.com"
smtp_port = 465
username = "contato@arapath.com.br"
password = "S@iArapath12345S@i"

try:
    print(f"Connecting to {smtp_server}:{smtp_port}...")
    server = smtplib.SMTP_SSL(smtp_server, smtp_port)
    print("Connected. Logging in...")
    server.login(username, password)
    print("Login success!")
    server.quit()
    print("SMTP Check Passed")
except Exception as e:
    print(f"SMTP Check Failed: {e}")
