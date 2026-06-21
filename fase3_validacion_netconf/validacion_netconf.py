import yaml
import datetime
import socket
from ncclient import manager
import xml.etree.ElementTree as ET
import xml.dom.minidom

# Imprimir metadatos obligatorios
print("=== VALIDACION NETCONF ===")
print("Script: validacion_netconf.py")
print(f"Fecha: {datetime.datetime.now()}")
print(f"Host : {socket.gethostname()}")
print("==========================\n")

# Cargar tu archivo de variables
with open('../vars/vars_005D-02.yaml', 'r') as f:
    vars_data = yaml.safe_load(f)

esperado = {
    'hostname': vars_data['cliente']['hostname'],
    'loopback_ip': vars_data['router']['loopback_ip'],
    'loopback_mask': vars_data['router']['loopback_mask'],
    'descripcion_wan': vars_data['router']['descripcion_wan'],
    'ntp_server': vars_data['router']['ntp_server']
}

# Filtro para obtener solo el modelo nativo de IOS-XE
filtro = '''<filter>
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native"/>
</filter>'''

try:
    print("Obteniendo configuracion via NETCONF...\n")
    # Conectarse via ncclient desactivando llaves y agentes
    with manager.connect(host='192.168.56.102', port=830, username='cisco', password='cisco123!', hostkey_verify=False, allow_agent=False, look_for_keys=False) as m:
        reply = m.get_config(source='running', filter=filtro)
        xml_crudo = reply.xml

        # Guardar XML crudo en la carpeta de evidencias
        with open('evidencias/rpc_reply_raw.xml', 'w') as f:
            f.write(xml.dom.minidom.parseString(xml_crudo).toprettyxml())

        # Procesar XML (remover namespaces para facilitar busqueda)
        root = ET.fromstring(xml_crudo)
        for elem in root.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]

        # Diccionario para almacenar los valores que extraemos del router
        real = {'hostname': 'No encontrado', 'loopback_ip': 'No encontrado', 'loopback_mask': 'No encontrado', 'descripcion_wan': 'No encontrado', 'ntp_server': 'No encontrado'}

        # 1. Extraer Hostname
        hn = root.find('.//hostname')
        if hn is not None: real['hostname'] = hn.text

        # 2. Extraer Descripcion WAN (GigabitEthernet1)
        for intf in root.findall('.//interface/GigabitEthernet'):
            if intf.find('name') is not None and intf.find('name').text == '1':
                desc = intf.find('description')
                if desc is not None: real['descripcion_wan'] = desc.text

        # 3 y 4. Extraer Loopback 10 IP y Mascara
        for loop in root.findall('.//interface/Loopback'):
            if loop.find('name') is not None and loop.find('name').text == str(vars_data['router']['loopback_id']):
                ip_node = loop.find('.//ip/address/primary/address')
                mask_node = loop.find('.//ip/address/primary/mask')
                if ip_node is not None: real['loopback_ip'] = ip_node.text
                if mask_node is not None: real['loopback_mask'] = mask_node.text

        # 5. Extraer Servidor NTP
        ntp_node = root.find('.//ntp//ip-address')
        if ntp_node is not None: 
            real['ntp_server'] = ntp_node.text

        # Comparar y Reportar
        criterios_ok = 0
        for clave in esperado:
            status = "[OK]" if esperado[clave] == real[clave] else "[FAIL]"
            if status == "[OK]": criterios_ok += 1
            print(f"{clave.upper()}:")
            print(f"  Esperado  : {esperado[clave]}")
            print(f"  Encontrado: {real[clave]} {status}\n")

        print("--------------------------")
        print("RESULTADO GLOBAL:")
        if criterios_ok == 5:
            print("ESTADO: CONFORME")
        else:
            print("ESTADO: NO CONFORME")

except Exception as e:
    print(f"Error de conexion o parseo: {e}")
