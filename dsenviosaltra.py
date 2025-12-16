#!/usr/bin/env python3
"""
Script cliente para API CONECTASS - Réplica exacta del sistema VB.NET
Uso: python conectass_client.py archivo.xml [config.ini]
"""
import os
from pathlib import Path
import re
import sys
import json
import requests
import urllib3
import time
import xml.etree.ElementTree as ET
from typing import Dict
from dsenviosaltra_certificado import DsEnvioSaltraCertificado
from dsenviosaltra_cliente import DsEnvioSaltraCliente
from dsenviosaltra_respuestas import guardar_respuesta_completa, crear_archivo_fin, crear_archivo_error, json_to_txt, guardar_respuestas_contratos

# Desactivar warning de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SaltraClient:
    def __init__(self, dsClave: str, usuario: str, idUsuario:str, passw: str, guion_file: str, code_respuesta: str, tiempo_inicio):
        self.dsClave = dsClave
        self.usuario = usuario
        self.idUsuario = idUsuario
        self.passw = passw
        self.guion_file = guion_file
        self.tiempo_inicio = tiempo_inicio

        if code_respuesta == "ISO8859-1":
            self.code_respuesta = 'iso-8859-1'

        self.servicio = ""
        self.metodo = ""
        self.endpoint = ""
        self.parametro = ""
        self.output_path = ""
        self.fich_respuesta = ""

        self.config = self.leer_guion(guion_file)
        self.accion_deducida = self.deducir_accion_por_url()
        self.token = self.obtener_token()

        self.api_certificado = DsEnvioSaltraCertificado(self.usuario, self.idUsuario, self.metodo, self.endpoint, self.config, self.fich_respuesta, self.token, self.tiempo_inicio)
        self.api_cliente = DsEnvioSaltraCliente(self.usuario, self.metodo, self.config, self.fich_respuesta, self.token, self.tiempo_inicio)

    def deducir_accion_por_url(self):
        if not self.endpoint:
            return 'accion_desconocida'
        
        if self.endpoint.rstrip('/').endswith('/certificate'):
            return 'certificado'
        elif self.endpoint.rstrip('/').endswith('/customer') or 'customer' in self.endpoint:
            return 'cliente'
        else:
            return 'query_avanza'
        
    def leer_guion(self, guion_file: str) -> Dict[str, str]:
        """Leer archivo guion.txt"""
        config = {}
        current_section = None
        section_content = []

        try:
            with open(guion_file, 'r', encoding= "iso-8859-1") as f:
                lineas = f.readlines()
                
                for linea in lineas:
                    linea = linea.strip()    

                    if not linea:
                        if current_section and section_content:
                            config[current_section] = '\n'.join(section_content).strip()
                            section_content = []
                        continue
                    
                    if linea.startswith('[') and linea.endswith(']'):
                        if current_section and section_content:
                            config[current_section] = '\n'.join(section_content).strip()
                        
                        current_section = linea[1:-1]
                        section_content = []
                    else:
                        if current_section is not None:
                            section_content.append(linea)
                    
                if current_section and section_content:
                    config[current_section] = '\n'.join(section_content).strip()
                
                if 'fiche-out' in config:
                    self.output_path = self.obtener_path(config['fiche-out'].strip())
                    
                    self.fich_respuesta = self.output_path

                    # Crear directorio si no existe
                    output_dir = os.path.dirname(self.output_path)
                    if output_dir and not os.path.exists(output_dir):
                        os.makedirs(output_dir, exist_ok=True)
                
                if 'metodo' in config:
                    try:
                        self.metodo = config['metodo']
                    except json.JSONDecodeError as e:
                        crear_archivo_error(self.fich_respuesta, f"error : {e}", self.tiempo_inicio)
                        crear_archivo_fin(self.fich_respuesta)
                        sys.exit(1)
                
                if 'url' in config:
                    try:
                        self.endpoint = config['url']
                    except json.JSONDecodeError as e:
                        crear_archivo_error(self.fich_respuesta, f"error : {e}", self.tiempo_inicio)
                        crear_archivo_fin(self.fich_respuesta)
                        sys.exit(1)
                
                if 'json envio' in config:
                    try:
                        json.loads(config['json envio'])

                    except json.JSONDecodeError as e:
                        crear_archivo_error(self.fich_respuesta, f"error : {e}", self.tiempo_inicio)
                        crear_archivo_fin(self.fich_respuesta)
                        sys.exit(1)
                
                if 'fiche-xml' in config:
                    try:
                        json_guion = config['json envio']
                        json_objecto = json.loads(json_guion)
                        
                        if "nss" in json_objecto['datos']:
                            self.parametro = str(json_objecto['datos']['nss'])

                        path_xml = self.obtener_path(config['fiche-xml'].strip())
                        json_data = self.xml_a_json(path_xml)

                        if isinstance(json, str):
                            json_data = json.loads(json_data)

                        if "#xmltojson#" in config['json envio']:
                            json_guion = config['json envio']
                            json_objecto = json.loads(json_guion)

                            del json_objecto['datos']['#xmltojson#'] # Elimina la clave marcadora si existe
                            
                            json_objecto['datos']['json_data'] = json_data
                            config['json envio'] = json.dumps(json_objecto)

                    except json.JSONDecodeError as e:
                        crear_archivo_error(self.fich_respuesta, f"error : {e}", self.tiempo_inicio)
                        crear_archivo_fin(self.fich_respuesta)
                        sys.exit(1)
                
                    
            return config

        except Exception as e:
            print(f"Error al leer {guion_file}: {e}")
            sys.exit(1)

    def acciones_cliente(self):
        if self.metodo.upper() == 'POST':
            return self.api_cliente.subir_cliente(self.endpoint)
        elif self.metodo.upper() == 'GET':
            return self.api_cliente.obtener_clientes(self.endpoint)
        elif self.metodo.upper() == 'PUT':
            return self.api_cliente.desactivar_cliente(self.endpoint)
        elif self.metodo.upper() == 'DELETE':
            self.endpoint = f"{self.endpoint}/{self.config['parametro']}"
            return self.api_cliente.borrar_cliente(self.endpoint)
        else:
            crear_archivo_error(self.fich_respuesta, f"error : Método {self.metodo} no soportado para acción cliente.", self.tiempo_inicio)
            crear_archivo_fin(self.fich_respuesta)
            sys.exit(1)
        
    def acciones_certificado(self):
        try:
            if self.metodo.upper() == 'POST':
                return self.api_certificado.subir_certificado()
            elif self.metodo.upper() == 'GET':
                return self.api_certificado.obtener_certificados()
            elif self.metodo.upper() == 'DELETE':
                self.endpoint = f"{self.endpoint}/{self.config['parametro']}"
                return self.api_certificado.borrar_certificado(self.endpoint)
            else:
                
                crear_archivo_error(self.fich_respuesta, f"error : Método {self.metodo} no soportado para acción certificado.", self.tiempo_inicio)
                crear_archivo_fin(self.fich_respuesta)
                sys.exit(1)   
        except Exception as e:
            crear_archivo_error(self.fich_respuesta, f"error : {e}", self.tiempo_inicio)
            crear_archivo_fin(self.fich_respuesta)
            sys.exit(1) 
        
    def realizar_llamada_ss_sepe(self) -> str:
        data_json = ""
        try:
            data = self.config["json envio"]
            data_dictionary = json.loads(data)
            certificado = data_dictionary.get("certificado")
            data_json = data_dictionary.get("datos")

            if isinstance(data_json, str):
                try:
                    # Si es un string, lo convertimos en un diccionario
                    data_json = json.loads(data_json)
                    
                except json.JSONDecodeError as e:
                    crear_archivo_error(self.fich_respuesta, f"error : El campo 'datos' contiene un string que no es un JSON válido. {e}", self.tiempo_inicio)
                    crear_archivo_fin(self.fich_respuesta)
                    sys.exit(1)

            datos_originales = data_json.copy()

            test = data_json.get("validar_sin_enviar")

            if "validar_sin_enviar" in data_json:
                testing = 1 if test == "true" or test == "True" else 0
                datos_originales.pop("validar_sin_enviar")
                if testing == 1:
                    datos_originales = {"test":testing, **datos_originales}

            if "cond_desempleado" in data_json:
                data_cond_desempleado = data_json.get("cond_desempleado")
                if data_cond_desempleado != "" and data_cond_desempleado in ("1", "2", "3", "4", "5", "6", "7", "9"):
                    cond_desempleado = int(data_cond_desempleado)
                    datos_originales.pop("cond_desempleado")
                    datos_originales["cond_desempleado"] = cond_desempleado
            
            if "options" in data_json:
                option = int(data_json.get("options"))
                datos_originales["options"] = option
            
            if "duplicate" in data_json:
                duplicate = int(data_json.get("duplicate"))
                datos_originales["duplicate"] = duplicate
            
            if "obtener_idc" in data_json:
                obtener_idc = int(data_json.get("obtener_idc"))
                datos_originales["obtener_idc"] = obtener_idc
        
        except json.JSONDecodeError as e:
            crear_archivo_error(self.fich_respuesta, f"error : El 'json envio' proporcionado no es un JSON válido. {e}", self.tiempo_inicio)
            crear_archivo_fin(self.fich_respuesta)
            sys.exit(1)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.token}',
            'X-Cert-Secret': certificado
        }
        
        response = []
        
        try:
            if self.endpoint.rstrip('/').endswith('/contrata'):
                
                test = datos_originales.get('test')
                json_string = datos_originales["json_data"]
                contratos_a_procesar = json.loads(json_string)
                respuestas_contratos = []
                for i, contrato in enumerate(contratos_a_procesar):
                    if test == 1:
                        contrato["test"] = test
                        
                    response = requests.request(
                        method=self.metodo,
                        url=self.endpoint,
                        headers=headers,
                        json=contrato
                    )

                    if response.status_code == 200:
                        response = self.obtener_copia_basica(test, contrato, headers, response)
                    else:
                        response = response.json()
                        
                    # Acumular las respuestas en una lista
                    respuestas_contratos.append({
                        'response': response,
                        'numero': i + 1
                    })

                guardar_respuestas_contratos(
                    respuestas_contratos,
                    self.fich_respuesta,
                    self.config,
                    self.usuario,
                    self.endpoint,
                    self.metodo,
                    self.tiempo_inicio
                )
            elif self.endpoint.rstrip('/').endswith('/llamamientos'):
                test = datos_originales.get('test')
                json_string = datos_originales["json_data"]
                llamada_json = json.loads(json_string)

                if test == 1:
                    llamada_json["test"] = test
                    
                response = requests.request(
                    method=self.metodo,
                    url=self.endpoint,
                    headers=headers,
                    json=llamada_json
                )
                guardar_respuesta_completa(response, self.fich_respuesta, "query_avanza",  self.config, self.usuario, self.endpoint, self.metodo, self.tiempo_inicio)

            else:
                response = requests.request(
                    method=self.metodo,
                    url=self.endpoint,
                    headers=headers,
                    json=datos_originales
                )

                guardar_respuesta_completa(response, self.fich_respuesta, "query_avanza",  self.config, self.usuario, self.endpoint, self.metodo, self.tiempo_inicio)

        except requests.exceptions.HTTPError as e:
            data_error = json.loads(e.response.text)
            plantilla_error = ("{}= {}\n")

            error_message = plantilla_error.format(
                e.response.reason,
                data_error["message"]
            )
            base_path = Path(self.fich_respuesta)
            txt_path = str(base_path.with_suffix('.txt'))
            respuesta_data = response.json()
            json_to_txt(respuesta_data, txt_path,"ko",self.config, self.usuario, self.endpoint, self.metodo, error_message, "")
            crear_archivo_fin(self.fich_respuesta)
            sys.exit(1)

        except Exception as e:
            crear_archivo_error(self.fich_respuesta, f"error : {e}", self.tiempo_inicio)
            crear_archivo_fin(self.fich_respuesta)
            sys.exit(1)

    def obtener_copia_basica(self, test, contrato, headers, response):
        
        try:
            response_data = response.json()
        except Exception as e:
            crear_archivo_error(self.fich_respuesta, f"error : {e}", self.tiempo_inicio)
            crear_archivo_fin(self.fich_respuesta)
            sys.exit(1)

        copia_basica_json ={}
        if test == 1:
            copia_basica_json["test"] = test
        
        copia_basica_json["cif"] = contrato.get("cif", "")
        copia_basica_json["docType"] = contrato.get("docType", "")
        copia_basica_json["dni"] = contrato.get("dni", "")
        copia_basica_json["sepeId"] = response_data.get("data", {}).get("id", "")
        copia_basica_json["TIPO_FIRMA"] = contrato.get("signatureType", "")
        copia_basica_json["startDate"] = contrato.get("startDate", "")
        copia_basica_json["TEXTO_COPIABASICA"] = contrato.get("copyBasicText", "")
        copia_basica_json["DOMIC_CENTRO_TRABAJO"] = contrato.get("workplace", "")
        copia_basica_json["duplicate"] = 1

        reponse_copia_basica = requests.request(
            method="POST",
            url = "https://api.saltra.es/api/v4/sepe/copy-basic",
            headers=headers,
            json=copia_basica_json
        )
                
        try:
            dict1 = json.loads(response.text)
            dict2 = json.loads(reponse_copia_basica.text)
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON: {e}")
            exit()

        if reponse_copia_basica.status_code == 200:
            # Verificar que ambas respuestas tengan success=true y la estructura de datos correcta
            if (dict1.get('success') == True and isinstance(dict1.get('data'), dict) and 'file' in dict1['data'] and
                dict2.get('success') == True and isinstance(dict2.get('data'), dict) and 'file' in dict2['data']):
                
                primer_fichero = dict1['data']['file']
                segundo_fichero = dict2['data']['file']
                dict1['data']['file1'] = primer_fichero
                del dict1['data']['file']
                dict1['data']['file2'] = segundo_fichero
                return dict1
            else:
                # Si alguna respuesta falló (success=false) o no tiene la estructura esperada,
                # devolver la respuesta de copia básica que contiene el error
                return dict2
        else:
            return dict2
                        
    def obtener_path(self, path):
        if '\\' in path or 'C:' in path:
            linux_path = path.replace('\\', '/')
            if linux_path.startswith('C:/'):
                linux_path = linux_path[2:]  # Quitar "C
            linux_path = os.path.join('/tmp', linux_path.lstrip('/'))
            path = linux_path
        else:
            path = os.path.abspath(path)
        
        return path

    def xml_a_json(self, path_xml):
        tiempo_parcial = [200,209,230,239,250,289,500,502,503,506,507,508,510,511,513,518,520,521,520,540,541,550,552]
        try:
            # Parsea el archivo XML
            tree = ET.parse(path_xml)
            root = tree.getroot()
            payload_api = {}
            esContrato = False
            if root.tag == "CONTRATOS":
                esContrato = True
            
            if esContrato:
                json_dict = []
                for contrato_node in root:
                    cod_contrato = int(contrato_node.tag.split('_')[1])
                    cif_empresa = self.obtener_texto_nodo(contrato_node, 'DATOS_EMPRESA/CIF_NIF_EMPRESA/CIF_NIF')
                    ccc_completo = self.obtener_texto_nodo(contrato_node, 'DATOS_EMPRESA/CODIGO_CUENTA_COTIZACION')
                    
                    regimen_empresa = ccc_completo[:4]
                    ccc_empresa = ccc_completo[4:]
                    
                    identificador = self.obtener_texto_nodo(contrato_node, 'DATOS_TRABAJADOR/IDENTIFICADORPFISICA')
                    tipo_documento = identificador[0] if identificador else ""
                    numero_documento = identificador[1:] if identificador else ""
                    
                    nombre = self.obtener_texto_nodo(contrato_node, 'DATOS_TRABAJADOR/NOMBRE_APELLIDOS/NOMBRE')
                    apellido1 = self.obtener_texto_nodo(contrato_node, 'DATOS_TRABAJADOR/NOMBRE_APELLIDOS/PRIMER_APELLIDO')
                    apellido2 = self.obtener_texto_nodo(contrato_node, 'DATOS_TRABAJADOR/NOMBRE_APELLIDOS/SEGUNDO_APELLIDO')
                    sexo = int(self.obtener_texto_nodo(contrato_node, 'DATOS_TRABAJADOR/SEXO', '0'))

                    fecha_nac_str = self.obtener_texto_nodo(contrato_node, 'DATOS_TRABAJADOR/FECHA_NACIMIENTO')
                    fecha_nacimiento = f"{fecha_nac_str[:4]}-{fecha_nac_str[4:6]}-{fecha_nac_str[6:8]}" if fecha_nac_str else None
                    
                    nacionalidad = int(self.obtener_texto_nodo(contrato_node, 'DATOS_TRABAJADOR/NACIONALIDAD', '0'))
                    municipio = int(self.obtener_texto_nodo(contrato_node, 'DATOS_TRABAJADOR/MUNICIPIO_RESIDENCIA', '0'))
                    pais_residencia = int(self.obtener_texto_nodo(contrato_node, 'DATOS_TRABAJADOR/PAIS_RESIDENCIA', '0'))

                    nss = self.obtener_texto_nodo(contrato_node, 'DATOS_TRABAJADOR/NUMERO_SEGURIDAD_SOCIAL')
                    # Asegura que el NSS tenga 12 dígitos, rellenando con ceros a la izquierda si es necesario
                    nss = nss.zfill(12)  
                    
                    nivel_formativo = int(self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/NIVEL_FORMATIVO', '0'))
                    ocupacion = self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/CODIGO_OCUPACION')
                    nacionalidad_contrato = int(self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/NACIONALIDAD_CT', '0'))
                    municipio_contrato = int(self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/MUNICIPIO_CT', '0'))
                    
                    real_decreto_1435_1985 = ""
                    if cod_contrato in [402, 407, 502, 507]:
                        real_decreto_1435_1985 = self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/REAL_DECRETO_1435_1985')

                    collectiveAgreement = self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/IND_CONVENIO_COLECTIVO')

                    fecha_ini_str = self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/FECHA_INICIO')
                    fecha_inicio = f"{fecha_ini_str[:4]}-{fecha_ini_str[4:6]}-{fecha_ini_str[6:8]}" if fecha_ini_str else None
                    
                    indicativo_prtr = self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/INDICATIVO_PRTR')
                    causa_sustitucion_str = self.obtener_texto_nodo(contrato_node, 'DATOS_CONTRATO_SUSTITUCION/CAUSA_SUSTITUCION')
                    causa_sustitucion = causa_sustitucion_str if causa_sustitucion_str is not None else None

                    horas_formacion = 0
                    minutos_formacion = 0
                    indicador_ere = None

                    if cod_contrato in [421, 521]:
                        horas_formacion_str = self.obtener_texto_nodo(contrato_node, 'DATOS_CONTRATO_TIEMPO_PARCIAL/HORAS_FORMACION', '0')
                        horas_formacion = int(horas_formacion_str)
                        minutos_formacion = 1
                        
                    # IND_ERE no existe en el XML, asumimos "N" (No)
                    indicador_ere = self.obtener_texto_nodo(contrato_node, 'DATOS_PRESTACIONES/IND_ERE', 'N')
                    fecha_fin_str = self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/FECHA_TERMINO')
                    fecha_fin = f"{fecha_fin_str[:4]}-{fecha_fin_str[4:6]}-{fecha_fin_str[6:8]}" if fecha_fin_str else None

                    tipo_firma = self.obtener_texto_nodo(contrato_node, 'DATOS_COMUNICA_COPIA_BASICA/TIPO_FIRMA')
                    texto_copia_basica = self.obtener_texto_nodo(contrato_node, 'DATOS_COMUNICA_COPIA_BASICA/TEXTO_COPIABASICA')
                    workplace = self.obtener_texto_nodo(contrato_node, 'DATOS_COMUNICA_COPIA_BASICA/DOMIC_CENTRO_TRABAJO')

                    if cod_contrato in tiempo_parcial:
                        tipo_jornada = self.obtener_texto_nodo(contrato_node, 'DATOS_CONTRATO_TIEMPO_PARCIAL/TIPO_JORNADA')
                        horas_jornada = self.obtener_texto_nodo(contrato_node, 'DATOS_CONTRATO_TIEMPO_PARCIAL/HORAS_JORNADA')
                        minutos_jornada = 0

                    payload_api = {
                        #"test": 1,
                        "cif": cif_empresa,
                        "regimen": regimen_empresa,
                        "ccc": ccc_empresa,
                        "docType": tipo_documento,
                        "dni": numero_documento,
                        "name": nombre,
                        "surname": apellido1,
                        "lastSurname": apellido2,
                        "sex": sexo,
                        "dateOfBirth": fecha_nacimiento,
                        "nationality": nacionalidad,
                        "municipality": municipio,
                        "PAIS_RESIDENCIA": pais_residencia,
                        "nss": nss,
                        "nivelFormativo": nivel_formativo,
                        "occupation": ocupacion,
                        "nationalityContract": nacionalidad_contrato,
                        "municipalityContract": municipio_contrato,
                        "codContract": cod_contrato,
                        "startDate": fecha_inicio,
                        "INDICATIVO_PRTR": indicativo_prtr,
                        "signatureType": tipo_firma,
                        "copyBasicText": texto_copia_basica,
                        "workplace": workplace,
                        "copia": 1,
                        "duplicate": 1
                    }
                    if real_decreto_1435_1985 and real_decreto_1435_1985 != "":
                        payload_api["REAL_DECRETO_1435_1985"] = real_decreto_1435_1985

                    if collectiveAgreement and collectiveAgreement != "":
                        payload_api["collectiveAgreement"] = collectiveAgreement

                    if horas_formacion > 0:
                        payload_api["HORAS_FORMACION"] = horas_formacion

                    if minutos_formacion > 0:
                        payload_api["jornadaFormativaMin"] = minutos_formacion
                    
                    if indicador_ere is not None:
                        payload_api["IND_ERE"] = indicador_ere

                    if causa_sustitucion:
                        payload_api["sustitucion"] = causa_sustitucion
                    
                    if fecha_fin:
                        payload_api["endDate"] = fecha_fin

                    if cod_contrato in tiempo_parcial:
                        payload_api["jornadaType"] = tipo_jornada[2:]
                        payload_api["jornadaHour"] = horas_jornada[2:]
                        payload_api["jornadaMin"] = minutos_jornada
                    
                    json_dict.append(payload_api)

                return json.dumps(json_dict)
            else:
                llamamiento_node = root.find('LLAMAMIENTO_TIPO')
                cif_empresa = self.obtener_texto_nodo(llamamiento_node, 'DATOS_EMPRESA/CIF_NIF_EMPRESA/CIF_NIF')
                ccc_completo = self.obtener_texto_nodo(llamamiento_node, 'DATOS_EMPRESA/CCC')
                
                regimen_empresa = ccc_completo[:4]
                ccc_empresa = ccc_completo[4:]
                
                identificador = self.obtener_texto_nodo(llamamiento_node, 'DATOS_TRABAJADOR/IDENTIFICADORPFISICA')
                tipo_documento = identificador[0] if identificador else ""
                numero_documento = identificador[1:] if identificador else ""
                
                nombre = self.obtener_texto_nodo(llamamiento_node, 'DATOS_TRABAJADOR/NOMBRE_APELLIDOS/NOMBRE')
                apellido1 = self.obtener_texto_nodo(llamamiento_node, 'DATOS_TRABAJADOR/NOMBRE_APELLIDOS/PRIMER_APELLIDO')
                apellido2 = self.obtener_texto_nodo(llamamiento_node, 'DATOS_TRABAJADOR/NOMBRE_APELLIDOS/SEGUNDO_APELLIDO')
                sexo = int(self.obtener_texto_nodo(llamamiento_node, 'DATOS_TRABAJADOR/SEXO', '0'))

                fecha_nac_str = self.obtener_texto_nodo(llamamiento_node, 'DATOS_TRABAJADOR/FECHA_NACIMIENTO')
                fecha_nacimiento = f"{fecha_nac_str[:4]}-{fecha_nac_str[4:6]}-{fecha_nac_str[6:8]}" if fecha_nac_str else None
                
                nacionalidad = int(self.obtener_texto_nodo(llamamiento_node, 'DATOS_TRABAJADOR/NACIONALIDAD', '0'))
                municipio = int(self.obtener_texto_nodo(llamamiento_node, 'DATOS_TRABAJADOR/MUNICIPIO_RESIDENCIA', '0'))
                pais_residencia = int(self.obtener_texto_nodo(llamamiento_node, 'DATOS_TRABAJADOR/PAIS_RESIDENCIA', '0'))
                nss = self.obtener_texto_nodo(llamamiento_node, 'DATOS_TRABAJADOR/NUMERO_SEGURIDAD_SOCIAL')
                # Asegura que el NSS tenga 12 dígitos, rellenando con ceros a la izquierda si es necesario
                nss = nss.zfill(12)

                fecha_ini_str = self.obtener_texto_nodo(llamamiento_node, 'DATOS_LLAMAMIENTO/FECHA_INICIO')
                fecha_inicio = f"{fecha_ini_str[:4]}-{fecha_ini_str[4:6]}-{fecha_ini_str[6:8]}" if fecha_ini_str else None

                fecha_fin_str = self.obtener_texto_nodo(llamamiento_node, 'DATOS_LLAMAMIENTO/FECHA_FIN')
                fecha_fin = f"{fecha_fin_str[:4]}-{fecha_fin_str[4:6]}-{fecha_fin_str[6:8]}" if fecha_fin_str else None
                
                nivel_formativo = int(self.obtener_texto_nodo(llamamiento_node, 'DATOS_LLAMAMIENTO/NIVEL_FORMATIVO', '0'))
                ocupacion = int(self.obtener_texto_nodo(llamamiento_node, 'DATOS_LLAMAMIENTO/CODIGO_OCUPACION', '0'))
                question = self.obtener_texto_nodo(llamamiento_node, 'DATOS_LLAMAMIENTO/IND_INCORPORA_ACTIVIDAD')

                sepeId = self.obtener_texto_nodo(llamamiento_node, 'DATOS_LLAMAMIENTO/CLAVE_CONTRATO_TRANS')
                sepeId = self.tratar_sepeId(sepeId)

                payload_api = {
                    #"test": 1,
                    "cif": cif_empresa,
                    "regimen": regimen_empresa,
                    "ccc": ccc_empresa,
                    "duplicate": 1,
                    "employees": [
                        {
                            "doc": numero_documento,
                            "docType": tipo_documento,
                            "name": nombre,
                            "surname": apellido1,
                            "lastSurname": apellido2,
                            "nss": nss,
                            "sex": sexo,
                            "dateOfBirth": fecha_nacimiento,
                            "nationality": nacionalidad,
                            "municipality": municipio,
                            "country": pais_residencia,
                            "startDate": fecha_inicio,
                            "endDate": fecha_fin,
                            "nivelFormativo": nivel_formativo,
                            "question": question,
                            "occupation": ocupacion,
                            "sepeId": sepeId
                        }
                    ]
                }
                return json.dumps(payload_api)
                    
        except FileNotFoundError:
            print(f"Error: El archivo '{path_xml}' no fue encontrado.")
            return None
        except Exception as e:
            print(f"Ha ocurrido un error al procesar el XML: {e}")
            return None
    
    def tratar_sepeId(self, sepeId):
        if not sepeId:
            return ""
        
        sepeId = sepeId.strip()

        if re.fullmatch(r"E-\d{2}-\d{4}-\d{7}", sepeId) or re.fullmatch(r"E-\d{2}-\d{4}-\d{6}", sepeId):
            return sepeId
        
        
        solo_numeros = re.sub(r"\D", "", sepeId)
        
        if not sepeId.startswith("E-"):
            return f"E-{solo_numeros[0:2]}-{solo_numeros[2:6]}-{solo_numeros[6:]}"
        else:
            return ""

    def obtener_texto_nodo(self, nodo_padre, ruta, valor_defecto=""):
        """
        Busca un nodo hijo a partir de una ruta y devuelve su texto.
        Si el nodo no existe o está vacío, devuelve un valor por defecto.
        """
        nodo_hijo = nodo_padre.find(ruta)
        
        if nodo_hijo is not None and nodo_hijo.text:
            return nodo_hijo.text.strip()
        return valor_defecto

    def obtener_token(self):
        try:
            headers = {'Content-Type': 'application/json'}

            payload = {
                "email": self.usuario,
                "password": self.passw
            }

            response = requests.post("https://api.saltra.es/api/v4/auth/login", headers=headers, json=payload)
            response_data = response.json()

            return response_data.get('data', {}).get('access_token')
        except Exception as e:
            crear_archivo_error(self.fich_respuesta, f"error : {e}", self.tiempo_inicio)
            crear_archivo_fin(self.fich_respuesta)
            sys.exit(1)

def main():
    start_time = time.time()

    dsClave = sys.argv[1]
    partesArgs = sys.argv[2].split("PK:")
    usuario = partesArgs[0]
    idUsuario = partesArgs[1]
    passw = sys.argv[3]
    guion_file = sys.argv[4]
    code_respuesta = sys.argv[5]
    
    if not os.path.exists(guion_file):
        print(f"Error: Archivo {guion_file} no encontrado")
        sys.exit(1)

    client = SaltraClient(dsClave, usuario, idUsuario, passw, guion_file, code_respuesta, start_time)
    if client.accion_deducida == 'certificado':
        resultado = client.acciones_certificado()
    elif client.accion_deducida == 'cliente':
        resultado = client.acciones_cliente()
    elif client.accion_deducida == 'query_avanza':    
        resultado = client.realizar_llamada_ss_sepe()
    else:
        print(f"Acción desconocida: {client.accion_deducida}")
        sys.exit(1)

    if resultado:  
        
        sys.exit(1)
    else:
        if client.fich_respuesta:
            print("Respuesta guardada")
            
            end_time = time.time()
            total_time = round(end_time-start_time)
            with open(client.fich_respuesta, "a") as fichero:
                fichero.write("\nTiempo transcurrido: "+str(total_time)+" segundos")

        sys.exit(0)

if __name__ == "__main__":
    main()