import smtplib
try:
    import keyring
except ImportError:
    keyring = None

from email.mime.text import MIMEText


def send(smtp_server, from_email, to_email, subject, body,
         tls=False, auth=False):
    msg = MIMEText(body, 'plain', 'utf_8')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    if ':' in smtp_server:
        smtp_hostname, smtp_port = smtp_server.split(':')
        smtp_port = int(smtp_port)
    else:
        smtp_port = 25
        smtp_hostname = smtp_server

    s = smtplib.SMTP()
    s.connect(smtp_hostname, smtp_port)
    s.ehlo()
    if tls:
        s.starttls()
    if auth and keyring is not None:
        passwd = keyring.get_password(smtp_server, from_email)
        if passwd is None:
            raise ValueError(
                'No password available in '
                'keyring for {}, {}'.format(smtp_server, from_email))
        s.login(from_email, passwd)
    s.sendmail(from_email, [to_email], msg.as_string())
    s.quit()


def set_password(smtp_server, from_email):
    ''' Set the keyring password for the mail connection. Interactive.'''
    if keyring is None:
        raise ImportError('keyring module missing - service unsupported')
    from getpass import getpass
    keyring.set_password(smtp_server, from_email,
                         getpass(prompt='Enter password '
                                 'for {} using {}: '.format(
                                     from_email, smtp_server)))
