
import smtplib
from email.mime.text import MIMEText

def send(smtp_server, from_email, to_email, subject, body):
    msg = MIMEText(body, 'plain', 'utf_8')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    s = smtplib.SMTP()
    s.connect(smtp_server, 25)
    s.sendmail(from_email, [to_email], msg.as_string())
    s.quit()

