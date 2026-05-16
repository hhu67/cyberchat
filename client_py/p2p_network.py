import os
import socket
import threading
import json
import random
import string
from crypto_module import sign_data, verify_signature, load_or_generate_keys
import socks

class P2PNetwork:
    def __init__(self, onion_address):
        self.onion_address = onion_address
        self.host = "127.0.0.1"
        self.port = 9090
        self.server_socket = None
        self.authenticated_peers = {}
        self.whitelist_file = "whitelist.txt"
        self.private_key, self.public_key = load_or_generate_keys()

    def start_server(self):
        """
        Start the TCP server to accept incoming connections.
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}")
        
        # Start a thread to accept incoming connections
        accept_thread = threading.Thread(target=self._accept_connections)
        accept_thread.daemon = True
        accept_thread.start()

    def _accept_connections(self):
        """
        Accept incoming connections and handle authentication.
        """
        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"New connection from {addr}")
                
                # Handle authentication in a separate thread
                auth_thread = threading.Thread(
                    target=self._handle_authentication,
                    args=(client_socket,)
                )
                auth_thread.daemon = True
                auth_thread.start()
            except Exception as e:
                print(f"Error accepting connection: {e}")
                break

    def _handle_authentication(self, client_socket):
        """
        Perform cryptographic handshake with the connecting peer.
        """
        try:
            # Generate a random challenge
            challenge = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            client_socket.send(challenge.encode("utf-8"))
            
            # Receive the signature and public key
            data = client_socket.recv(4096)
            if not data:
                client_socket.close()
                return
            
            received_data = json.loads(data.decode("utf-8"))
            peer_public_key_pem = received_data["public_key"]
            signature = received_data["signature"]
            
            # Load the peer's public key
            peer_public_key = serialization.load_pem_public_key(
                peer_public_key_pem.encode("utf-8")
            )
            
            # Verify the signature
            if verify_signature(peer_public_key, signature, challenge):
                # Check if the peer's public key is in the whitelist
                if self._is_whitelisted(peer_public_key_pem):
                    print(f"Peer authenticated and whitelisted.")
                    self.authenticated_peers[client_socket] = peer_public_key_pem
                    
                    # Start a thread to handle messages
                    message_thread = threading.Thread(
                        target=self._handle_messages,
                        args=(client_socket,)
                    )
                    message_thread.daemon = True
                    message_thread.start()
                else:
                    print(f"Peer not whitelisted.")
                    client_socket.close()
            else:
                print(f"Signature verification failed.")
                client_socket.close()
        except Exception as e:
            print(f"Error during authentication: {e}")
            client_socket.close()

    def _is_whitelisted(self, public_key_pem):
        """
        Check if the peer's public key is in the whitelist.
        """
        if not os.path.exists(self.whitelist_file):
            return False
        
        with open(self.whitelist_file, "r") as f:
            whitelist = f.read().splitlines()
            return public_key_pem in whitelist

    def _handle_messages(self, client_socket):
        """
        Handle incoming messages from the authenticated peer.
        """
        try:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                message = data.decode("utf-8")
                print(f"Received message: {message}")
                
                # Echo the message back for demonstration
                client_socket.send(f"Ack: {message}".encode("utf-8"))
        except Exception as e:
            print(f"Error handling messages: {e}")
        finally:
            client_socket.close()
            if client_socket in self.authenticated_peers:
                del self.authenticated_peers[client_socket]

    def connect_to_peer(self, peer_onion_address):
        """
        Connect to a peer's onion service.
        """
        try:
            # Use socks to route the connection through Tor
            socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
            socket.socket = socks.socksocket
            
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((peer_onion_address, 80))
            
            # Perform the handshake
            self._perform_handshake(peer_socket)
            
            # Start a thread to handle messages
            message_thread = threading.Thread(
                target=self._handle_messages,
                args=(peer_socket,)
            )
            message_thread.daemon = True
            message_thread.start()
            
            return peer_socket
        except Exception as e:
            print(f"Error connecting to peer: {e}")
            return None

    def _perform_handshake(self, peer_socket):
        """
        Perform the cryptographic handshake with the peer.
        """
        try:
            # Receive the challenge
            challenge = peer_socket.recv(4096).decode("utf-8")
            
            # Sign the challenge
            signature = sign_data(self.private_key, challenge)
            
            # Send the signature and public key
            response = {
                "public_key": self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                ).decode("utf-8"),
                "signature": signature.hex(),
            }
            peer_socket.send(json.dumps(response).encode("utf-8"))
        except Exception as e:
            print(f"Error during handshake: {e}")
            peer_socket.close()

    def send_message(self, peer_socket, message):
        """
        Send a message to the peer.
        """
        try:
            peer_socket.send(message.encode("utf-8"))
        except Exception as e:
            print(f"Error sending message: {e}")


if __name__ == "__main__":
    # Example usage
    from tor_controller import TorController
    
    tor_controller = TorController()
    if tor_controller.start_tor():
        onion_address = tor_controller.get_onion_address()
        p2p_network = P2PNetwork(onion_address)
        p2p_network.start_server()
        
        # Example: Connect to a peer
        # peer_socket = p2p_network.connect_to_peer("example.onion")
        # p2p_network.send_message(peer_socket, "Hello, peer!")
        
        # Keep the server running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            tor_controller.stop_tor()