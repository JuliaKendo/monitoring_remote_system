import os
import smtplib
import sys
from configparser import ConfigParser
 
 
def send_email(subject, to_addr, body_text):
    """
    Send an email
    """
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, "mailing.ini")
    
    if os.path.exists(config_path):
        cfg = ConfigParser()
        cfg.read(config_path)
    else:
        print("Config not found! Exiting!")
        sys.exit(1)
 
    host      = cfg.get("smtp", "server")
    from_addr = cfg.get("smtp", "from_addr")
    username  = cfg.get("auth", "username")
    password  = cfg.get("auth", "password")

    BODY = "\r\n".join((
        "From: %s" % from_addr,
        "To: %s" % to_addr,
        "Subject: %s" % subject ,
        "",
        body_text
    ))
    
    server = smtplib.SMTP_SSL(host)
    server.login(username, password)
    server.sendmail(from_addr, [to_addr], BODY)
    server.quit()
 
 
if __name__ == "__main__":
    subject = "Test email from Python"
    to_addr = "ghumoe@mailto.plus"
    body_text = "Python rules them all!"
    send_email(subject, to_addr, body_text)