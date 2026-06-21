import requests
import yaml
import urllib3
import json
import datetime
import socket

# Ignorar advertencias de certificados autofirmados
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("=== VALIDACION RESTCONF ===")
print("Script: validacion_restconf.py")
print(f"Fecha: {datetime.datetime.now()}")
print(f"Host : {socket.gethostname()}")
print("==========================\n")

# Cargar tu archivo de variables
with open('../vars/vars_005D-02.yaml', 'r') as f:
    vars_data = yaml.safe_load(f)

ip_router = '192.168.56.102'
credenciales = ('cisco', 'cisco123!')
headers = {'Accept': 'application/yang-data+json', 'Content-Type': 'application/yang-data+json'}

# Definir los 4 endpoints obligatorios
endpoints = {
    'hostname': {
        'url': f"https://{ip_router}/restconf/data/Cisco-IOS-XE-native:native/hostname",
        'file': 'get_hostname.json',
        'expected': vars_data['cliente']['hostname']
    },
    'loopback': {
        'url': f"https://{ip_router}/restconf/data/ietf-interfaces:interfaces/interface=Loopback{vars_data['router']['loopback_id']}",
        'file': 'get_loopback.json',
        'expected': vars_data['router']['loopback_ip']
    },
    'interfaces': {
        'url': f"https://{ip_router}/restconf/data/ietf-interfaces:interfaces/interface=GigabitEthernet1",
        'file': 'get_interfaces.json',
        'expected': vars_data['router']['descripcion_wan']
    },
    'ntp': {
        'url': f"https://{ip_router}/restconf/data/Cisco-IOS-XE-native:native/ntp",
        'file': 'get_ntp.json',
        'expected': vars_data['router']['ntp_server']
    }
}

real_data = {}
criterios_ok = 0

for key, data in endpoints.items():
    try:
        # Peticion GET a cada endpoint con verify=False
        response = requests.get(data['url'], auth=credenciales, headers=headers, verify=False)
        response.raise_for_status()
        json_data = response.json()

        # Guardar la respuesta cruda en JSON dentro de evidencias/responses/
        with open(f"evidencias/responses/{data['file']}", 'w') as f:
            json.dump(json_data, f, indent=4)

        # Parsear los valores según la estructura que devuelve RESTCONF
        if key == 'hostname':
            real_data[key] = json_data.get('Cisco-IOS-XE-native:hostname', 'No encontrado')
        elif key == 'loopback':
            try:
                real_data[key] = json_data['ietf-interfaces:interface']['ietf-ip:ipv4']['address'][0]['ip']
            except KeyError:
                real_data[key] = 'No encontrado'
        elif key == 'interfaces':
            real_data[key] = json_data.get('ietf-interfaces:interface', {}).get('description', 'No encontrado')
        elif key == 'ntp':
            try:
                # Aquí está la corrección:
                real_data[key] = json_data['Cisco-IOS-XE-native:ntp']['Cisco-IOS-XE-ntp:server']['server-list'][0]['ip-address']
            except KeyError:
                real_data[key] = 'No encontrado'

        # Comparar e imprimir resultado por criterio
        status = "[OK]" if data['expected'] == real_data[key] else "[FAIL]"
        if status == "[OK]":
            criterios_ok += 1

        print(f"{key.upper()}:")
        print(f"  Esperado  : {data['expected']}")
        print(f"  Encontrado: {real_data[key]} {status}\n")

    except Exception as e:
        print(f"Error procesando {key}: Fallo la consulta o extraccion de datos.")

print("--------------------------")
print("RESULTADO GLOBAL:")
if criterios_ok == 4:
    print("ESTADO: CONFORME")
else:
    print("ESTADO: NO CONFORME")
