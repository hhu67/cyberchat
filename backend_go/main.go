package main

import (
	"flag"
	"fmt"
	"io"
	"log"
	"math/rand"
	"net"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"
)

func findAvailablePort() int {
	// Generate a random starting port
	rand.Seed(time.Now().UnixNano())
	startPort := 1024 + rand.Intn(64511) // Random port between 1024 and 65535

	for port := startPort; port < 65535; port++ {
		addr := fmt.Sprintf("127.0.0.1:%d", port)
		conn, err := net.Listen("tcp", addr)
		if err == nil {
			conn.Close()
			return port
		}
	}

	// If no port found in the first range, try from 1024 again
	for port := 1024; port < startPort; port++ {
		addr := fmt.Sprintf("127.0.0.1:%d", port)
		conn, err := net.Listen("tcp", addr)
		if err == nil {
			conn.Close()
			return port
		}
	}

	return -1
}

func main() {
	// Parse command-line arguments for DPI bypass
	fragmentationArgs := flag.String("fragment", "", "Fragmentation scenario for DPI bypass")
	flag.Parse()

	// Start SOCKS5 proxy
	proxyServer := &SOCKS5Proxy{
		fragmentationArgs: *fragmentationArgs,
	}

	// Find an available port
	availablePort := findAvailablePort()

	if availablePort == -1 {
		log.Fatal("Не удалось найти свободный порт.")
	}

	// Print the selected port to stdout
	fmt.Printf("PROXY_PORT:%d\n", availablePort)

	// Listen on the available port
	addr := fmt.Sprintf("127.0.0.1:%d", availablePort)
	listener, err := net.Listen("tcp", addr)
	if err != nil {
		log.Fatalf("Failed to listen on %s: %v", addr, err)
	}
	defer listener.Close()

	log.Printf("SOCKS5 proxy listening on %s", listener.Addr().String())

	// Handle graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigChan
		log.Println("Shutting down SOCKS5 proxy...")
		os.Exit(0)
	}()

	// Accept incoming connections
	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Printf("Failed to accept connection: %v", err)
			continue
		}
		go proxyServer.handleConnection(conn)
	}
}

type SOCKS5Proxy struct {
	fragmentationArgs string
}

func (p *SOCKS5Proxy) handleConnection(conn net.Conn) {
	defer conn.Close()

	// Perform SOCKS5 handshake
	socksConn, err := p.performSOCKS5Handshake(conn)
	if err != nil {
		log.Printf("SOCKS5 handshake failed: %v", err)
		return
	}

	// Handle the connection based on the fragmentation args
	p.handleProxyConnection(socksConn)
}

func (p *SOCKS5Proxy) performSOCKS5Handshake(conn net.Conn) (net.Conn, error) {
	// Implement SOCKS5 handshake logic here
	// For simplicity, assume handshake is successful
	return conn, nil
}

func (p *SOCKS5Proxy) handleProxyConnection(conn net.Conn) {
	// Apply fragmentation based on the provided arguments
	if p.fragmentationArgs != "" {
		p.applyFragmentation(conn)
	}

	// Proxy the connection to the target
	targetConn, err := net.Dial("tcp", "example.com:80")
	if err != nil {
		log.Printf("Failed to dial target: %v", err)
		return
	}
	defer targetConn.Close()

	// Copy data between connections
	go func() {
		_, err := io.Copy(targetConn, conn)
		if err != nil {
			log.Printf("Failed to copy data from target to client: %v", err)
		}
	}()

	_, err = io.Copy(conn, targetConn)
	if err != nil {
		log.Printf("Failed to copy data from client to target: %v", err)
	}
}

func (p *SOCKS5Proxy) applyFragmentation(conn net.Conn) {
	// Parse fragmentation arguments
	args := strings.Split(p.fragmentationArgs, " ")
	for _, arg := range args {
		if strings.HasPrefix(arg, "-d") || strings.HasPrefix(arg, "-s") {
			// Apply delay or split logic
			time.Sleep(100 * time.Millisecond)
		}
	}
}