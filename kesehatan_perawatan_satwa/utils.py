import re
from django.db import connection

def capture_trigger_messages():
    """Tangkap pesan dari trigger PostgreSQL dari log koneksi"""
    messages = []
    
    if hasattr(connection, 'connection') and connection.connection is not None:
        if hasattr(connection.connection, 'notices') and connection.connection.notices:
            for notice in connection.connection.notices:
                match = re.search(r'TRIGGER_MESSAGE: (SUKSES: .*)', notice)
                if match:
                    messages.append(match.group(1))
            
            connection.connection.notices.clear()
    
    return messages