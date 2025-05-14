"""
Test SMTP connection to Outlook server
"""
import socket
import ssl
import sys

def test_smtp_connection(server, port):
    print(f"Testing connection to {server}:{port}...")
    
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        # Connect to the server
        result = sock.connect_ex((server, port))
        
        if result == 0:
            print(f"✅ Successfully connected to {server}:{port}")
            
            # Test if it's an SMTP server by sending initial greeting
            try:
                data = sock.recv(1024)
                print(f"Server response: {data.decode('utf-8', errors='replace')}")
                
                # Try TLS upgrade
                print("\nTesting TLS upgrade...")
                sock.send(b'EHLO example.com\r\n')
                data = sock.recv(1024)
                print(f"EHLO response: {data.decode('utf-8', errors='replace')}")
                
                sock.send(b'STARTTLS\r\n')
                data = sock.recv(1024)
                print(f"STARTTLS response: {data.decode('utf-8', errors='replace')}")
                
            except Exception as e:
                print(f"Error during SMTP communication: {str(e)}")
        else:
            print(f"❌ Failed to connect to {server}:{port} (Result: {result})")
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
    finally:
        try:
            sock.close()
        except:
            pass

if __name__ == "__main__":
    # Test Outlook SMTP server
    test_smtp_connection("smtp-mail.outlook.com", 587)
    
    # Test Gmail SMTP server for comparison
    print("\n" + "-" * 50 + "\n")
    test_smtp_connection("smtp.gmail.com", 587)
