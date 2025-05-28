import re
import html
from django.db import connection

def capture_trigger_messages():
    """Tangkap pesan dari trigger PostgreSQL dari log koneksi"""
    messages = []
    
    if hasattr(connection, 'connection') and connection.connection is not None:
        if hasattr(connection.connection, 'notices') and connection.connection.notices:
            for notice in connection.connection.notices:
                if "TRIGGER_MESSAGE:" in notice:
                    message = notice.split("TRIGGER_MESSAGE:")[1].strip()
                    clean_message = html.unescape(message)
                    messages.append(clean_message)
            
            connection.connection.notices.clear()
    
    return messages