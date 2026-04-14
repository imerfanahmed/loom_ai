from netmiko import ConnectHandler

device = {
    'device_type': 'cisco_ios', # Change based on your device (e.g., 'arista_eos', 'juniper_junos')
    'host': '172.16.57.137',
    'username': 'admin',
    'password': 'admin1pass',
    'port': 22, 
}

try:
    with ConnectHandler(**device) as net_connect:
        print(f"Successfully connected to: {net_connect.find_prompt()}")
except Exception as e:
    print(f"Connection failed: {e}")