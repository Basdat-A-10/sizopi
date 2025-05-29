import re
import html
from django.db import connection

def capture_trigger_messages():
    """Tangkap pesan dari trigger PostgreSQL dari log koneksi"""
    messages = []
    
    try:
        # Debug
        print(f"DEBUG - Connection object: {connection}")
        print(f"DEBUG - Connection.connection: {hasattr(connection, 'connection')}")
        
        if hasattr(connection, 'connection') and connection.connection is not None:
            print(f"DEBUG - Connection.connection exists: {connection.connection}")
            print(f"DEBUG - Has notices: {hasattr(connection.connection, 'notices')}")
            
            if hasattr(connection.connection, 'notices'):
                notices = connection.connection.notices
                print(f"DEBUG - Notices: {notices}")
                print(f"DEBUG - Notices length: {len(notices) if notices else 0}")
                
                if notices:
                    for i, notice in enumerate(notices):
                        print(f"DEBUG - Notice {i}: {repr(notice)}")
                        # Coba dua format: dengan dan tanpa 
                        if "TRIGGER_MESSAGE:" in notice:
                            message = notice.split("TRIGGER_MESSAGE:")[1].strip()
                            clean_message = html.unescape(message)
                            messages.append(clean_message)
                            print(f"DEBUG - Captured TRIGGER_MESSAGE: {clean_message}")
                        elif "SUKSES:" in notice or "ERROR:" in notice:
                            clean_message = html.unescape(notice.strip())
                            messages.append(clean_message)
                            print(f"DEBUG - Captured direct message: {clean_message}")
                
                connection.connection.notices.clear()
            else:
                print("DEBUG - No notices attribute")
        else:
            print("DEBUG - No connection or connection is None")
            
        # Alternative: messages from session variables
        if not messages:
            print("DEBUG - Trying alternative method with session variables...")
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT current_setting('custom.last_trigger_message', true)")
                    result = cursor.fetchone()
                    if result and result[0]:
                        messages.append(result[0])
                        print(f"DEBUG - Got message from session variable: {result[0]}")
                        cursor.execute("SELECT set_config('custom.last_trigger_message', '', false)")
            except Exception as e:
                print(f"DEBUG - Session variable method failed: {e}")
            
    except Exception as e:
        print(f"DEBUG - Error in capture_trigger_messages: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"DEBUG - Final messages captured: {messages}")
    return messages