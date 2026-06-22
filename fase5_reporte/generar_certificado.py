import datetime
import yaml
import os

print("=== INICIANDO GENERACION DE CERTIFICADO ===")

# Cargar tus variables
try:
    with open('../vars/vars_005D-02.yaml', 'r') as f:
        vars_data = yaml.safe_load(f)
    alumno = vars_data['alumno']['nombre']
    codigo = vars_data['alumno']['codigo']
    empresa = vars_data['cliente']['empresa']
except Exception as e:
    print(f"Error cargando vars_005D-02.yaml: {e}")
    alumno, codigo, empresa = "Alumno", "005D-02", "Empresa"

# Verificar reportes de Fase 3 y 4
netconf_ok = False
restconf_ok = False

if os.path.exists('../fase3_validacion_netconf/evidencias/output_validacion_netconf.txt'):
    with open('../fase3_validacion_netconf/evidencias/output_validacion_netconf.txt', 'r') as f:
        netconf_ok = "ESTADO: CONFORME" in f.read()

if os.path.exists('../fase4_validacion_restconf/evidencias/output_validacion_restconf.txt'):
    with open('../fase4_validacion_restconf/evidencias/output_validacion_restconf.txt', 'r') as f:
        restconf_ok = "ESTADO: CONFORME" in f.read()

estado_final = "CONFORME" if (netconf_ok and restconf_ok) else "NO CONFORME"

certificado = f"""==================================================
CERTIFICADO DE COMPLIANCE AUDITADO
==================================================
Fecha de emision : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Ingeniero a cargo: {alumno} ({codigo})
Cliente asignado : {empresa}
==================================================
RESULTADOS DE AUDITORIA:
[+] Verificacion NETCONF : {"CONFORME" if netconf_ok else "NO CONFORME"}
[+] Verificacion RESTCONF: {"CONFORME" if restconf_ok else "NO CONFORME"}
[+] Cambios (Genie Diff) : Detectados y registrados en evidencias/diff_{codigo}

==================================================
ESTADO FINAL DE LA IMPLEMENTACION: >>> {estado_final} <<<
==================================================
"""

print(certificado)

# Asegurar que el directorio de evidencias existe
os.makedirs("evidencias", exist_ok=True)

# Guardar el certificado
with open(f"evidencias/certificado_compliance_{codigo}.txt", "w") as f:
    f.write(certificado)

print(f"Certificado guardado con exito en: evidencias/certificado_compliance_{codigo}.txt")
