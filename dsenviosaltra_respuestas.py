import os
import json
import sys
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import base64

# Función helper para crear directorios
def _crear_directorio(ruta: str):
    """Crea el directorio si no existe"""
    if ruta and not os.path.exists(ruta):
        os.makedirs(ruta, exist_ok=True)

def guardar_respuesta_completa(response, fich_respuesta: str, accion_deducida: str, config: Dict[str, Any], usuario: str, endpoint: str, metodo: str, tiempo_inicio):
    try:
        if not fich_respuesta:
            return
        
        _crear_directorio(os.path.dirname(fich_respuesta))
        
        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            respuesta_data = response.json()
            with open(fich_respuesta, 'w', encoding='utf-8') as f:
                json.dump(respuesta_data, f, indent=2, ensure_ascii=False)
            
            extraer_y_guardar_respuesta(respuesta_data, response, fich_respuesta, accion_deducida, config, usuario, endpoint, metodo, tiempo_inicio)
        
        crear_archivo_fin(fich_respuesta)
                
    except Exception as e:
        print(f"Error guardando respuesta: {e}")

def extraer_y_guardar_respuesta(respuesta_data: Any, response: Any, fich_respuesta: str, accion_deducida: str, config: Dict[str, Any], usuario, endpoint, metodo, tiempo_inicio):
    """Extrae PDFs y guarda la respuesta en formato TXT"""
    base_path = Path(fich_respuesta)
    rutas_pdf = []
    
    try:
        # Obtener datos una sola vez
        data = respuesta_data.get("data", {})
        file_info = data.get("file") if "file" in data else None

        #   Obtener PDF llamamiento
        if endpoint.endswith("/llamamientos"):
            data = data.get("data", {})
            for item in data:
                if "file" in item:
                    respuesta_data = item
                    file_info = item.get("file")
                    break
        
        idc_pdf = data.get("idc") if "idc" in data else None
        total_pdfs = (1 if file_info else 0) + (1 if idc_pdf else 0)

    except Exception as e:
        crear_archivo_error(fich_respuesta, f"error : {e}", tiempo_inicio)
        crear_archivo_fin(fich_respuesta)
        sys.exit(1)
    
    txt_path = str(base_path.with_suffix('.txt'))
    _crear_directorio(os.path.dirname(txt_path))
    try:
        if file_info or idc_pdf:
            if file_info and file_info.get("contentType") == "application/pdf":
                pdf_content = file_info.get('content')
                if pdf_content:
                    pdf_path = base_path.parent / f"pdf1_1.pdf"
                    ruta_guardada = guardar_pdf(pdf_content, str(pdf_path))
                    if ruta_guardada:
                        rutas_pdf.append(ruta_guardada)
            
            if idc_pdf and idc_pdf.get("contentType") == "application/pdf":
                pdf_content = idc_pdf.get('content')
                if pdf_content:
                    pdf_path = base_path.parent / f"pdf2_1.pdf"
                    ruta_guardada = guardar_pdf(pdf_content, str(pdf_path))
                    if ruta_guardada:
                        rutas_pdf.append(ruta_guardada)
            
            # Generar archivo TXT con las rutas de los PDFs
            json_to_txt(respuesta_data, txt_path, response.status_code, config, usuario, endpoint, metodo, "", rutas_pdf)
        else:
            guardar_respuesta_sin_pdf(accion_deducida, respuesta_data, txt_path, response.status_code, config, usuario, endpoint, metodo)

    except Exception as e:
        crear_archivo_error(fich_respuesta, f"error : {e}", tiempo_inicio)
        crear_archivo_fin(fich_respuesta)
        sys.exit(1)
    
def guardar_respuesta_sin_pdf(accion_deducida, respuesta_data, txt_path, status_code, config, usuario, endpoint, metodo):
    if accion_deducida == 'certificado':
        json_certificado_to_txt(respuesta_data, txt_path, status_code, config, usuario, endpoint, metodo) 
    elif accion_deducida == 'cliente':
        json_cliente_to_txt(respuesta_data, txt_path, status_code, config, usuario, endpoint, metodo)
    else:   
        json_to_txt(respuesta_data, txt_path, status_code, config, usuario, endpoint, metodo)

def _procesar_pdf_contrato(data: Dict, base_path: Path, numero_contrato: int, campo: str, pdf_num: int) -> Optional[str]:
    """Procesa y guarda un PDF de contrato si existe"""
    if campo in data and data[campo]:
        info = data[campo]
        if info.get("contentType") == "application/pdf":
            pdf_content = info.get("content")
            if pdf_content:
                pdf_path = base_path.parent / f"pdf_{numero_contrato}_{pdf_num}.pdf"
                return guardar_pdf(pdf_content, str(pdf_path))
    return None

def guardar_respuestas_contratos(respuestas_contratos: List[Dict], fich_respuesta: str, config: Dict[str, Any], usuario: str, endpoint: str, metodo: str, tiempo_inicio):
    """Guarda todas las respuestas de contratos en un Ãºnico archivo TXT con mÃºltiples registros"""
    try:
        if not fich_respuesta:
            return
        
        _crear_directorio(os.path.dirname(fich_respuesta))
        
        response_dict = ""
        base_path = Path(fich_respuesta)
        txt_path = str(base_path.with_suffix('.txt'))
        
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        parametro = config.get("parametro", "")
        texto_salida = ""
        status = "ok"
        for item in respuestas_contratos:
            response_dict = item['response']
            if response_dict.get("status") != 200:
                status = "ko"
                break
            
        texto_salida = f"""PETICION
  FECHA {fecha_actual}
  USUARIO {usuario}
  URL {endpoint}{parametro}
  STATUS {status}
  
  OPERACIONES SS/SEPE/CERTIFICA"""

        for item in respuestas_contratos:
            response_dict = item['response']
            numero_contrato = item['numero']
            resultado = "ACEPTADO" if response_dict.get("success") == True else "RECHAZADO"

            texto_salida += f"""
      Registro-{numero_contrato}
        Resultado {resultado}"""
            
            if response_dict.get("status") != 200:
                mensaje = response_dict.get("message", "")
                error = response_dict.get("errors", "")
                texto_salida += """
      FinRegistro
"""
                texto_salida +=f"""
      Errores
        mensaje : {mensaje} {error}\n"""
            else:
                # Guardar el JSON de respuesta individual
                #json_path = base_path.parent / f"{base_path.stem}_CONTRATO{numero_contrato}.json"
                #
                #content_type = response.headers.get('content-type', '')
                #if 'application/json' in content_type:
                #    with open(json_path, 'w', encoding='utf-8') as f:
                #        json.dump(respuesta_data, f, indent=2, ensure_ascii=False) 

                data = response_dict.get("data", {})
                mensaje = data.get("id", "") if "id" in data else ""
                dni_trabajador = data.get("doc", "") if "doc" in data else ""

                texto_salida += f"""
        mensaje {mensaje}
        DNITRABA : {dni_trabajador}"""
                
                # Procesar los PDF en 'file'
                ruta_pdf1 = _procesar_pdf_contrato(data, base_path, numero_contrato, "file1", 1)
                if ruta_pdf1:
                    texto_salida += f"""
        Pdf1 {ruta_pdf1}"""
                
                if "file2" in data:
                    ruta_pdf2 = _procesar_pdf_contrato(data, base_path, numero_contrato, "file2", 2)
                    if ruta_pdf2:
                        texto_salida += f"""
        Pdf2 {ruta_pdf2}"""
                        
                texto_salida += """
      FinRegistro
"""
        
        texto_salida += "\n\nFIN"
        
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(texto_salida)
        
        # Crear archivo .fin
        crear_archivo_fin(fich_respuesta)
        
        print(f"Respuestas de {len(respuestas_contratos)} contratos guardadas en {txt_path}")
        
    except Exception as e:
        print(f"Error guardando respuestas de contratos: {e}")
        crear_archivo_error(fich_respuesta, f"error : {e}", tiempo_inicio)
        crear_archivo_fin(fich_respuesta)
        sys.exit(1)

def extraer_pdf(respuesta: Any) -> Any:
    if not isinstance(respuesta, dict):
        return None
    
    pdf_keys = ['pdf', 'PDF', 'pdf_base64', 'archivo_pdf', 'documento', 'file', 'content']
    for key in pdf_keys:
        if key in respuesta:
            data = respuesta[key]
            if data and data != "null":
                return data
    
    for key, value in respuesta.items():
        if isinstance(value, dict):
            result = extraer_pdf(value)
            if result:
                return result
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    result = extraer_pdf(item)
                    if result:
                        return result
    
    return None

def guardar_pdf(pdf_data: Any, ruta_pdf: str):
    try:
        pdf_bytes = base64.b64decode(pdf_data)

        if pdf_bytes.startswith(b'%PDF-'):
            with open(ruta_pdf, 'wb') as f:
                f.write(pdf_bytes)
            print(f"PDF guardado exitosamente en: {ruta_pdf}")
            return ruta_pdf
        else:
            print("Error: Los datos decodificados no parecen ser un archivo PDF válido.")

    except base64.binascii.Error as e:
        print(f"Error al decodificar Base64: {e}. La cadena de entrada podría estar corrupta.")
    except Exception as e:
        print(f"Error inesperado al guardar el PDF: {e}")

def crear_archivo_fin(fich_respuesta: str):
    if not fich_respuesta:
        return
    
    try:
        base_path = Path(fich_respuesta)
        fin_path = base_path.with_suffix('.fin')
        _crear_directorio(fin_path.parent)
        
        with open(fin_path, 'a', encoding='iso-8859-1') as f:
            f.write("FIN\n")
    except Exception as e:
        print(f"Error creando archivo FIN: {e}")

def crear_archivo_error(fich_respuesta: str, resultado: str, tiempo_inicio):
    """Crea archivo de error con información del fallo"""
    try:
        _crear_directorio(os.path.dirname(fich_respuesta))

        total_time = round(time.time() - tiempo_inicio)
        contenido = f"  STATUS ko\n{resultado}\nTiempo transcurrido: {total_time} segundos"
        
        with open(fich_respuesta, 'w', encoding='utf-8') as f:
            f.write(contenido)

    except Exception as e:
        print(f"Error creando archivo de error: {e}")

def convertir_formato_fecha(fecha_str: str,  formato_out='%d/%m/%Y %H:%M:%S') -> str:
    if not fecha_str:
        return None
    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
        return fecha_obj.strftime(formato_out)
    except (ValueError, TypeError):
        return f"Advertencia: No se pudo convertir la fecha '{fecha_str}'"
    
def json_cliente_to_txt(json_data: str, txt_path: str, response_status: int, config: Dict[str, Any], usuario, endpoint, metodo):
    status = "ok" if response_status == 200 else "error"
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    parametro = config.get("parametro", "")

    texto_salida_encabezado = f"""PETICION
  FECHA {fecha_actual}
  USUARIO {usuario}
  URL {endpoint}{parametro}
  STATUS {status}"""
    texto_salida_cuerpo = ""

    if metodo.upper() == 'POST':
        data = json_data.get("data", {})
        profile = json_data.get("data",{}).get("profile", {})
        pk = data.get("id", "")
        email = data.get("access").get("email", "")
        nombre = data.get("name") if data.get("name") is not None else ""
        activo = data.get("active") if data.get("active") is not None else ""
        dni = profile.get("dni") if profile.get("dni") is not None else ""
        razon_social = profile.get("razon_social") if profile.get("razon_social") is not None else ""
        alias = profile.get("account")[0].get("alias") if profile.get("account")[0].get("alias") is not None else ""
        regimen = profile.get("account")[0].get("regimen") if profile.get("account")[0].get("regimen") is not None else ""
        cuenta = profile.get("account")[0].get("cuenta") if profile.get("account")[0].get("cuenta") is not None else ""



        texto_salida_cuerpo += f"""
  pk : {pk}
  email: {email}
  nombre: {nombre}
  active: {activo}
  dni: {dni}
  razon_social: {razon_social}
  alias: {alias}
  regimen: {regimen}
  cuenta: {cuenta}\n"""
    
    elif metodo.upper() == 'GET':
        total_certificados = json_data.get("data", {}).get("data",{})
        for certificado in total_certificados:
            profile = certificado.get("profile", {})
            pk = certificado.get("id", "")
            email = certificado.get("access").get("email", "")
            nombre = certificado.get("name") if certificado.get("name") is not None else ""
            activo = certificado.get("active") if certificado.get("active") is not None else ""
            dni = profile.get("dni") if profile.get("dni") is not None else ""
            razon_social = profile.get("razon_social") if profile.get("razon_social") is not None else ""
            alias = profile.get("account")[0].get("alias") if profile.get("account")[0].get("alias") is not None else ""
            regimen = profile.get("account")[0].get("regimen") if profile.get("account")[0].get("regimen") is not None else ""
            cuenta = profile.get("account")[0].get("cuenta") if profile.get("account")[0].get("cuenta") is not None else ""

            texto_salida_cuerpo += f"""
  pk : {pk}
  email: {email}
  nombre: {nombre}
  active: {activo}
  dni: {dni}
  razon_social: {razon_social}
  alias: {alias}
  regimen: {regimen}
  cuenta: {cuenta}\n"""
    
    elif metodo.upper() == 'DELETE':
        data = json_data.get("data", {})
        pk = data.get("id", "")
        email = data.get("access", {}).get("email", "")
        nombre = data.get("name", "")
        texto_salida_cuerpo += f"""
  pk : {pk}
  email: {email}
  nombre: {nombre}\n"""
    
    elif metodo.upper() == 'PUT':
        mensaje = json_data.get("message", "")
        texto_salida_cuerpo += f"""
  mensaje : {mensaje}\n"""
    else:
        return f"Error: Método {metodo} no soportado para acción cliente."
    
    texto_salida = texto_salida_encabezado + texto_salida_cuerpo + "\n\nFIN" if texto_salida_cuerpo else texto_salida_encabezado + "\n\nFIN" 
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(texto_salida)
    except Exception as e:
        return f"Error al escribir el archivo TXT en {txt_path}: {e}"
        
def json_certificado_to_txt(json_data: str, txt_path: str, response_status: int, config: Dict[str, Any], usuario, endpoint, metodo):
    status = "ok" if response_status == 200 else "error"
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    parametro = config.get("parametro", "")

    texto_salida_encabezado = f"""PETICION
  FECHA {fecha_actual}
  USUARIO {usuario}
  URL {endpoint}{parametro}
  STATUS {status}"""
    texto_salida_cuerpo = ""

    if metodo.upper() == 'POST':
        data = json_data.get("data", {})
        cert_secret = data.get("cert_secret", "")

        texto_salida_cuerpo += f"""
  cert_secret : {cert_secret}\n"""
        
    elif metodo.upper() == 'GET':
        total_certificados = json_data.get("data", {}).get("data",{})
        for certificado in total_certificados:
            pk = certificado.get("cert_secret", "")
            desde = convertir_formato_fecha(certificado.get("desde", ""))
            hasta = convertir_formato_fecha(certificado.get("expired", ""))
            nombre_cert = certificado.get("typeText") if certificado.get("typeText") is not None else ""
            nombre = certificado.get("gn") if certificado.get("gn") is not None else ""
            apellidos = certificado.get("sn") if certificado.get("sn") is not None else ""
            nombre_completo = certificado.get("fullName") if certificado.get("fullName") is not None else ""
            dni = certificado.get("dni") if certificado.get("dni") is not None else ""
            tipo = certificado.get("type") if certificado.get("type") is not None else ""
            activo = certificado.get("active") if certificado.get("active") is not None else ""
            issuer_cn = certificado.get("issuer_cn") if certificado.get("issuer_cn") is not None else ""

            texto_salida_cuerpo += f"""
  pk : {pk}
  numero_serie: {pk}
  id_certificado: {pk}
  inicio_validez: {desde}
  fin_validez: {hasta}
  nombre_certificado: {nombre_cert}
  gn: {nombre}
  sn: {apellidos}
  nombre_completo: {nombre_completo}
  dni: {dni}
  type: {tipo}
  active: {activo}
  issuer: {issuer_cn}\n"""
            
            
    elif metodo.upper() == 'DELETE':
        pass  # No hay datos específicos para mostrar
    else:
        return f"Error: Método {metodo} no soportado para acción certificado."
    
    texto_salida = texto_salida_encabezado + texto_salida_cuerpo + "\n\nFIN" if texto_salida_cuerpo else texto_salida_encabezado + "\n\nFIN"
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(texto_salida)
    except Exception as e:
        print(f"Error al escribir el archivo TXT en {txt_path}: {e}")

def json_to_txt(json_data, txt_path: str=None, response_status=None, config: Dict[str, Any]=None, usuario=None, endpoint=None, metodo=None, mensaje_error=None, rutas_pdf=None):
    success = json_data.get("success", False)
    resultado = "ACEPTADO" if success else "RECHAZADO"
    lista = success and len(json_data.get("data", [])) > 0
    status = "ok" if response_status == 200 else "ko"
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    mensaje_error = json_data.get("errors", "") if mensaje_error is None else mensaje_error
    parametro = config.get("parametro", "")

    employees = 1
    pdfs = 0

    texto_salida_encabezado = f"""PETICION
  FECHA {fecha_actual}
  USUARIO {usuario}
  URL {endpoint}{parametro}
  STATUS {status}
  
  OPERACIONES SS/SEPE/CERTIFICA
      Registro-1
        Resultado {resultado}"""
    
    texto_salida_cuerpo = ""
    cuerpo_pdf = ""

    if status == "ko":
        texto_salida_cuerpo +=f"""
  Errores
    mensaje : {mensaje_error}\n"""

    if rutas_pdf:
        if endpoint.endswith("/llamamientos"):
            texto_salida_cuerpo += f"""
        Mensaje {json_data.get("id")}"""
        for ruta in rutas_pdf:
            pdfs += 1
            texto_salida_cuerpo += f"""
        Pdf{pdfs} {ruta}"""
        
        texto_salida_cuerpo += """
      FinRegistro
"""
        lista = False
    
    if lista:
        texto_salida_cuerpo +=f"""
        Extra
          facturable : {employees}"""
        if "employees" in json_data.get("data"):
            for employee in json_data.get("data").get("employees"):
                texto_salida_cuerpo +=f"""
          Tabla"""
                for clave, valor in employee.items():
                    texto_salida_cuerpo +=f"""
            {clave} : {valor}"""
            employees += 1

        # Comprueba si "data" es una lista de diccionarios 
        elif (isinstance(json_data.get("data"), list)):
            for registro in json_data.get("data"):
                texto_salida_cuerpo +=f"""
          Tabla"""
                for clave, valor in registro.items():
                    texto_salida_cuerpo +=f"""
            {clave} : {valor}"""
            employees += 1
            
        else:
            texto_salida_cuerpo +=f"""
          Tabla"""
            for registro in json_data.get("data"):
                texto_salida_cuerpo +=f"""
            {registro} : {json_data.get("data").get(registro)}"""
            employees += 1
    
    

    texto_salida = texto_salida_encabezado + "\n\nFIN" if texto_salida_cuerpo == "" else texto_salida_encabezado + texto_salida_cuerpo + "\n\nFIN" 
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(texto_salida)
    except Exception as e:
        print(f"Error al escribir el archivo TXT en {txt_path}: {e}")