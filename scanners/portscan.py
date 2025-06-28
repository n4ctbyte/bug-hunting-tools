# Path: scanners/portscan.py

import socket

def scan_ports(target, ports=None):
    """
    Scan a list of common TCP ports on the given target.
    
    Args:
        target (str): Target hostname or IP address.
        ports (list): List of ports to scan (default: common ports).
    
    Returns:
        list: Open ports found on the target.
    """
    print(f"Scanning ports for {target}")
    if ports is None:
        ports = [21, 22, 23, 25, 53, 80, 110, 139, 143, 443, 445, 3306, 3389, 8080]

    open_ports = []
    for port in ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((target, port))
                if result == 0:
                    print(f"[+] Port {port} is open")
                    open_ports.append(port)
        except socket.error as e:
            print(f"[!] Error scanning port {port}: {e}")

    if not open_ports:
        print("[-] No open ports found.")
    return open_ports