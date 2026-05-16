import json
import os
import subprocess
import threading
import time
from tor_controller import TorController
from p2p_network import P2PNetwork
from strategy_checker import StrategyChecker
from crypto_module import load_or_generate_keys

class CyberChat:
    def __init__(self):
        self.config_file = "config.json"
        self.go_proxy_path = "../backend_go/main.go"
        self.proxy_process = None
        self.tor_controller = None
        self.p2p_network = None
        self.active_chat_socket = None
        self.chat_active = False
        self.dpi_mode = False
        self.proxy_port = 1080  # Default port

    def load_config(self):
        """
        Load the configuration from config.json.
        """
        if not os.path.exists(self.config_file):
            return None

        with open(self.config_file, "r") as f:
            return json.load(f)

    def start_go_proxy(self, scenario):
        """
        Start the Go proxy with the specified scenario.
        """
        print("Starting Go proxy...")
        self.proxy_process = subprocess.Popen(
            ["go", "run", self.go_proxy_path, f"--fragment={scenario}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait for the proxy to start and print the port
        time.sleep(2)

        # Read the selected port from stdout
        if self.proxy_process.stdout:
            output = self.proxy_process.stdout.readline()
            if output.startswith("PROXY_PORT:"):
                self.proxy_port = int(output.split(":")[1].strip())
                print(f"Go proxy started on port {self.proxy_port}.")
            else:
                print("Go proxy started (port not found in output).")
        else:
            print("Go proxy started (no output).")

    def stop_go_proxy(self):
        """
        Stop the Go proxy.
        """
        if self.proxy_process:
            print("Stopping Go proxy...")
            self.proxy_process.terminate()
            self.proxy_process.wait()
            self.proxy_process = None
            print("Go proxy stopped.")

    def start_tor(self):
        """
        Start the Tor controller and P2P network.
        """
        try:
            print("Starting Tor...")
            self.tor_controller = TorController()
            if self.tor_controller.start_tor():
                onion_address = self.tor_controller.get_onion_address()
                print(f"Tor started. Your UUID: {onion_address}")
                self.p2p_network = P2PNetwork(onion_address)
                self.p2p_network.start_server()
                return onion_address
            else:
                print("Failed to start Tor.")
        except Exception as e:
            print(f"Failed to start Tor: {e}")
        return None

    def stop_tor(self):
        """
        Stop the Tor controller.
        """
        if self.tor_controller:
            print("Stopping Tor...")
            self.tor_controller.stop_tor()
            self.tor_controller = None
            print("Tor stopped.")

    def show_menu(self):
        """
        Display the main menu.
        """
        print("\nCyberChat Main Menu:")
        print("[1] Show My UUID (.onion address)")
        print("[2] Connect to Peer (/include <onion_address>)")
        print("[3] Pending Connection Requests")
        print("[4] View Whitelist / Trusted Peers")
        print("[5] Run DPI Bypass Strategy Tester & Optimizer")
        print("[6] Toggle DPI Mode (Current: " + ("ON" if self.dpi_mode else "OFF") + ")")
        print("[7] Exit Application")

    def handle_menu_input(self, choice):
        """
        Handle user input from the menu.
        """
        if choice == "1":
            if self.tor_controller and self.tor_controller.get_onion_address():
                print(f"\nYour UUID: {self.tor_controller.get_onion_address()}")
            else:
                print("Tor is not running or onion address not generated yet.")
                print("Please wait for Tor to start or check Tor logs.")
        elif choice == "2":
            peer_address = input("Enter the peer's onion address: ")
            if self.p2p_network:
                peer_socket = self.p2p_network.connect_to_peer(peer_address)
                if peer_socket:
                    self.active_chat_socket = peer_socket
                    self.chat_active = True
                    self.start_chat(peer_socket)
            else:
                print("P2P network is not running. Please wait for Tor to start.")
        elif choice == "3":
            print("Pending connection requests (not implemented yet).")
        elif choice == "4":
            print("View whitelist / trusted peers (not implemented yet).")
        elif choice == "5":
            checker = StrategyChecker()
            checker.run_strategy_test()
        elif choice == "6":
            self.dpi_mode = not self.dpi_mode
            print(f"DPI Mode {'enabled' if self.dpi_mode else 'disabled'}.")
            if self.dpi_mode:
                config = self.load_config()
                if config and "selected_scenario" in config:
                    self.start_go_proxy(config["selected_scenario"])
                else:
                    print("No saved strategy found. Run the strategy tester first.")
            else:
                self.stop_go_proxy()
        elif choice == "7":
            self.exit_application()
        else:
            print("Invalid choice. Please try again.")

    def start_chat(self, peer_socket):
        """
        Start a chat session with the peer.
        """
        print("\nChat started. Type '/exit' to end the chat.")

        # Start a thread to handle incoming messages
        receive_thread = threading.Thread(
            target=self._receive_messages,
            args=(peer_socket,)
        )
        receive_thread.daemon = True
        receive_thread.start()

        # Handle user input
        while self.chat_active:
            message = input("")
            if message.lower() == "/exit":
                self.chat_active = False
                peer_socket.close()
                self.active_chat_socket = None
                print("Chat ended.")
                break
            else:
                self.p2p_network.send_message(peer_socket, message)

    def _receive_messages(self, peer_socket):
        """
        Handle incoming messages from the peer.
        """
        while self.chat_active:
            try:
                data = peer_socket.recv(4096)
                if not data:
                    break

                message = data.decode("utf-8")
                print(f"\nPeer: {message}")

                # Echo the message back for demonstration
                peer_socket.send(f"Ack: {message}".encode("utf-8"))
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def exit_application(self):
        """
        Clean up resources and exit the application.
        """
        print("\nExiting CyberChat...")
        self.stop_go_proxy()
        self.stop_tor()
        if self.p2p_network and self.active_chat_socket:
            self.active_chat_socket.close()
        print("Goodbye!")
        exit(0)

    def run(self):
        """
        Run the CyberChat application.
        """
        print("Starting CyberChat...")

        # Load or generate cryptographic keys
        print("Loading or generating cryptographic keys...")
        load_or_generate_keys()
        print("Keys loaded.")

        # Load configuration
        config = self.load_config()
        if config and "selected_scenario" in config:
            self.dpi_mode = True
            self.start_go_proxy(config["selected_scenario"])

        # Start Tor and P2P network in background
        print("Starting Tor in background...")
        threading.Thread(target=self.start_tor, daemon=True).start()

        # Main loop
        while True:
            self.show_menu()
            choice = input("Enter your choice: ")
            self.handle_menu_input(choice)

if __name__ == "__main__":
    cyberchat = CyberChat()
    cyberchat.run()