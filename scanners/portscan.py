
# Path: BugHunterPro/scanners/portscan.py

def scan_ports(target):
    print(f"Scanning ports for {target}")
    # Port scanning logic here
    pass




import socket

def scan_ports(target, ports=None):
    print(f"Scanning ports for {target}")
    if ports is None:
        ports = [21, 22, 23, 25, 53, 80, 110, 139, 443, 445, 3389, 8080]

    open_ports = []
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((target, port))
        if result == 0:
            print(f"[+] Port {port} is open")
            open_ports.append(port)
        sock.close()
    if not open_ports:
        print("[-] No open ports found.")
    return open_ports


