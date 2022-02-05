import argparse, sys, socket # Import all
from threading import Thread
import json
# We use threading, cuz multiprocessing is bad at passing arguments to targets
# also, we don`t need GIL unlocking.

VERSION = "v0.2"

class Client:
    def __init__(self):

        self.clients = set()
        
        self.parser()
        self.start()


    def build_msg(self, msg): # Build msg
        message = {"user": "[BRIDGE]", "msg": msg}                    
        return json.dumps(message, ensure_ascii=False).encode()


    def parser(self): 
        parser = argparse.ArgumentParser(
        prog="anonchat-compbridge",
        description = "Compability bridge messages to use older clients",
        epilog="---- Oh, hello there!") # Create parser
 
        parser.add_argument("ip", help = "IP of first anonchat-server", type=str)
        parser.add_argument("port", help = "Port of compability bridge.", type=str) # Assign all args
        parser.add_argument("nick", help = "Nickname of all users", type=str)
        
        args = parser.parse_args() # Parse args

        self.nick = args.nick

        ip = args.ip.split(":") # Split First IP
        ip.append(6969) # If port is not passed, add it to select later

        self.ip = ip[0] # Select First IP adress
        try:
            self.port = int(ip[1]) # Try to parse port
        except:
            print(f"Cannot parse port {ip[1]} as number. Aborting.")
            sys.exit()

        try:
            self.port2 = int(args.port) # Second port
        except:
            print(f"Cannot parse port {args.port} as number. Aborting.")
            sys.exit()

    def start(self):
        print(f"[BRIDGE] [GEN] [INF] Bridge version - {VERSION}")
        print(f"[BRIDGE] [GEN] [INF] Connecting Socket to IP0 - {self.ip}:{self.port}")
        self.socket_ip1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create and bind first socket to First IP
        self.socket_ip1.connect((self.ip, self.port))
        print(f"[BRIDGE] [GEN] [INF] Socket bound to IP0")

        print(f"[BRIDGE] [GEN] [INF] Creating server on port {self.port2}")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("0.0.0.0", self.port2))
        self.server.listen()
        print(f"[BRIDGE] [GEN] [INF] Server bound to port {self.port2}")

        self.socket_ip1.send(self.build_msg(f"Compability bridge bounded to this server!"))
        message_blacklist = [self.build_msg(f"Compability bridge bounded to this server!")]
        
        print(f"[BRIDGE] [GEN] [INF] Start up all processes...")
        self.prc_pipe = {"blacklist": message_blacklist, "kill": False} # Target last messages, or it will create a bunch of spam
        self.request_1 = Thread(target=self.bridge_to, args=(self.socket_ip1, self.server, self.prc_pipe), daemon=True) # Create Thread to send messages from First IP to Second
        self.request_1.start()
            
        while True:
            client, addr = self.server.accept()
            self.clients.add(client)
            Thread(target=self.client_server, args=(self.server, client, self.socket_ip1, self.prc_pipe)).start()

    def client_server(self, server, client, socket, info):
        while True:
            if info["kill"]:
                return
            # Receive new data while it's not empty
            # (it happens when the client is disconnected)
            
            try:
                data = client.recv(2048)
            except:
                data = None

            if not data:
                break

            text = str(data, "utf-8", "replace")
            text = "> ".join(text.split("> ")[1:])

            # If the text is not empty...
            if text.strip():
                # ...then broadcast it to all connected clients

                text = {"user": self.nick, "msg": text}

                text = json.dumps(text, ensure_ascii=False).encode()
                try:
                    socket.send(text)
                except:
                    pass

    # Remove client on disconnect or error
    try:
        client.close()
        self.clients.remove(client)
    except:
        pass

    def bridge_to(self, socket1, socket2, info): # First Socket (to listen from), Second Socket (to send messages), dict with last messages, num of server
        while True:
            if info["kill"]:
                return
            
            try:
                message = socket1.recv(2048) # Receive message from
            except:
                message = None
                
            if not message: # If no message, break all process
                break
            
            print(f"[BRIDGE] [IP0] [INF] Got message from IP0!")

            if not message in info["blacklist"]: # If message is was not sended in this server at last
                print(f"[BRIDGE] [IP0] [INF] Sending message to all clients.")
                
                if message.strip():
                    
                    # check if v1 or v2 and package
                    try:
                        text = json.loads(message)
                        text = f'<{text["user"]}> {text["msg"]}'
                    except:
                        print("[INFO] Got v1 package.")
                        text = message
                    
                    for c in self.clients.copy():
                        try:
                            c.sendall(text.encode("utf-8", "replace"))
                        except:
                            self.clients.remove(c)
            else:
                print(f"[BRIDGE] [IP0] [INF] Not sending message, because message is already sended or in blacklist.")

if __name__ == "__main__":
    cli = Client() # Create object if not imported
        
