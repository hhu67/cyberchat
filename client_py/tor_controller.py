import os
import time
import signal
import subprocess
from stem.process import launch_tor_with_config
from stem.control import Controller
from stem import SocketError

class TorController:
    def __init__(self):
        self.tor_process = None
        self.control_port = 9051
        self.socks_port = 9052
        self.hidden_service_port = 9090
        self.onion_address = None
        self.torrc_config = {
            'ControlPort': str(self.control_port),
            'SOCKSPort': str(self.socks_port),
            'HiddenServiceDir': os.path.join(os.getcwd(), 'hidden_service'),
            'HiddenServiceVersion': '3',
            'HiddenServicePort': f'80 127.0.0.1:{self.hidden_service_port}',
            'Log': 'NOTICE stdout',
        }

    def start_tor(self):
        """
        Launch Tor with the specified configuration and wait for it to bootstrap.
        """
        try:
            # Kill any existing Tor processes
            subprocess.run(["pkill", "-f", "tor"], check=False)
            
            print("Starting Tor with config:", self.torrc_config)
            self.tor_process = launch_tor_with_config(
                config
                =self.torrc_config,
                take_ownership=True,
            )
            print("Tor process started. Waiting for bootstrap...")
            
            # Wait for Tor to bootstrap
            time.sleep(10)
            
            # Connect to the Tor control port
            self._connect_to_control_port()
            
            return True
        except Exception as e:
            print(f"Failed to start Tor: {e}")
            return False

    def _connect_to_control_port(self):
        """
        Connect to the Tor control port and authenticate.
        """
        try:
            with Controller.from_port(port=self.control_port) as controller:
                controller.authenticate()
                print("Authenticated with Tor control port.")
                
                # Read the onion address
                with open(os.path.join(self.torrc_config['HiddenServiceDir'], 'hostname'), 'r') as f:
                    self.onion_address = f.read().strip()
                
                print(f"Hidden service created. Onion address: {self.onion_address}")
        except SocketError as e:
            print(f"Failed to connect to Tor control port: {e}")

    def stop_tor(self):
        """
        Stop the Tor process gracefully.
        """
        if self.tor_process:
            print("Stopping Tor process...")
            self.tor_process.terminate()
            self.tor_process = None
            print("Tor process stopped.")

    def get_onion_address(self):
        """
        Return the generated onion address.
        """
        return self.onion_address

    def __del__(self):
        """
        Ensure Tor is stopped when the object is destroyed.
        """
        self.stop_tor()


if __name__ == "__main__":
    # Example usage
    tor_controller = TorController()
    if tor_controller.start_tor():
        print(f"Onion address: {tor_controller.get_onion_address()}")
        # Keep Tor running for testing
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            tor_controller.stop_tor()