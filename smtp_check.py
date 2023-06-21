import smtplib
from email.message import EmailMessage

def send_email(subject:str, message:str, to_email:str) -> str:
    sender = 'toktorovkurmanbek92@gmail.com'
    password = 'lwfwbcqvqcxrexxd'

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()

    msg = EmailMessage()
    msg.set_content(message)

    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_email

    try:
        server.login(sender, password)
        server.send_message(msg)
        return "200 OK"
    except Exception as error:
        return f"{error}"
print(send_email('Python', 'Hello From Backend Group 8', 'ktoktorov144@gmail.com'))

emails = ['toktorovkurmanbek92@gmail.com', 'ktoktorov144@gmail.com', 'toktoroveldos15@gmail.com', 'geeks@gmail.com']