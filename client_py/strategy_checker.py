import json
import subprocess
import socket
import time
import urllib.request
import urllib.error
from tabulate import tabulate

class StrategyChecker:
    def __init__(self):
        self.proxy_list = []
        self.config_file = "config.json"
        self.go_proxy_path = "../backend_go/main.go"
        self.tor_directory_authorities = [
            ("171.25.193.9", 443),
            ("128.31.0.39", 9131),
            ("193.23.244.244", 443),
        ]

    def load_proxy_list(self):
        """
        Load the list of DPI bypass strategies from proxy_list.json.
        """
        with open("../proxy_list.json", "r") as f:
            self.proxy_list = json.load(f)

    def test_strategy(self, scenario):
        """
        Test a single DPI bypass strategy.

        Args:
            scenario: The scenario string to test.

        Returns:
            success_rate: Percentage of successful connections.
            avg_latency: Average latency in milliseconds.
        """
        success_count = 0
        total_latency = 0

        # Terminate any running Go proxy
        self._terminate_go_proxy()

        # Start the Go proxy with the current scenario
        print(f"Testing scenario: {scenario[:50]}...")
        proxy_process = subprocess.Popen(
            ["go", "run", self.go_proxy_path, f"--fragment={scenario}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for the proxy to start
        time.sleep(2)

        # Test each Tor directory authority
        for host, port in self.tor_directory_authorities:
            try:
                # Configure the socket to use the SOCKS5 proxy
                socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 1080)
                socket.socket = socks.socksocket

                # Start the timer
                start_time = time.perf_counter()

                # Attempt the connection
                with socket.create_connection((host, port), timeout=3) as sock:
                    # Measure latency
                    latency = (time.perf_counter() - start_time) * 1000  # Convert to milliseconds
                    total_latency += latency
                    success_count += 1
                    print(f"  ✓ Connected to {host}:{port} (latency: {latency:.2f} ms)")
            except (socket.timeout, ConnectionRefusedError, urllib.error.URLError) as e:
                print(f"  ✗ Failed to connect to {host}:{port}: {e}")

        # Terminate the Go proxy
        proxy_process.terminate()
        proxy_process.wait()

        # Calculate success rate and average latency
        success_rate = (success_count / len(self.tor_directory_authorities)) * 100
        avg_latency = total_latency / success_count if success_count > 0 else 0

        print(f"  Success rate: {success_rate:.2f}%, Avg latency: {avg_latency:.2f} ms")
        return success_rate, avg_latency

    def _terminate_go_proxy(self):
        """
        Terminate any running Go proxy process.
        """
        try:
            subprocess.run(["pkill", "-f", self.go_proxy_path], check=False)
        except subprocess.CalledProcessError:
            pass

    def run_strategy_test(self):
        """
        Test all strategies and display the top 5.
        """
        self.load_proxy_list()
        results = []

        print("Starting DPI Bypass Strategy Test...")
        print("This may take a few minutes. Please wait...\n")

        for strategy in self.proxy_list:
            strategy_id = strategy["id"]
            scenario = strategy["scenario"]

            print(f"\nTesting strategy {strategy_id}...")
            success_rate, avg_latency = self.test_strategy(scenario)

            results.append({
                "id": strategy_id,
                "success_rate": success_rate,
                "avg_latency": avg_latency,
            })

        # Sort results by success rate (descending) and latency (ascending)
        results.sort(key=lambda x: (-x["success_rate"], x["avg_latency"]))

        # Display the top 5 results
        top_results = results[:5]
        headers = ["Strategy ID", "Success Rate (%)", "Avg Latency (ms)"]
        table_data = [
            [result["id"], f"{result['success_rate']:.2f}", f"{result['avg_latency']:.2f}"]
            for result in top_results
        ]

        print("\nTop 5 Strategies:")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

        # Prompt the user to select a strategy
        selected_id = input("\nEnter the ID of the strategy to save (or 'q' to quit): ")
        if selected_id.lower() == 'q':
            return

        # Save the selected strategy to config.json
        selected_strategy = next(
            (strategy for strategy in self.proxy_list if strategy["id"] == int(selected_id)),
            None,
        )
        if selected_strategy:
            with open(self.config_file, "w") as f:
                json.dump({"selected_scenario": selected_strategy["scenario"]}, f)
            print(f"Strategy {selected_id} saved to config.json.")
        else:
            print("Invalid strategy ID.")

if __name__ == "__main__":
    checker = StrategyChecker()
    checker.run_strategy_test()