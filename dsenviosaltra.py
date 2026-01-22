#!/usr/bin/env python3
"""
Script cliente para API SALTRA
Uso: python dsenviosaltra.py archivo.xml [config.ini]
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
from dsenviosaltra_respuestas import guardar_respuesta_completa, manejar_error_y_salir, guardar_respuestas_contratos

# Desactivar warning de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SaltraClient:
    # Constantes para códigos de contrato
    CONTRATOS_REAL_DECRETO = [402, 407, 502, 507]
    CONTRATOS_HORAS_FORMACION = [421, 521]
    TIEMPO_PARCIAL = [200, 209, 230, 239, 250, 289, 500, 502, 503, 506, 507, 508, 510, 511, 513, 518, 520, 521, 520, 540, 541, 550, 552]
    COND_DESEMPLEADO_VALIDOS = ("1", "2", "3", "4", "5", "6", "7", "9")
    
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

    def _validar_json(self, json_str: str, contexto: str = "") -> Dict:
        """Valida y parsea un string JSON"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            mensaje = f"{contexto}El JSON proporcionado no es válido. {e}" if contexto else f"El JSON proporcionado no es válido. {e}"
            manejar_error_y_salir(self.fich_respuesta, mensaje, self.usuario, self.endpoint, self.tiempo_inicio)

    def _formatear_fecha(self, fecha_str: str) -> str:
        """Formatea una fecha de formato YYYYMMDD a YYYY-MM-DD"""
        if not fecha_str or len(fecha_str) < 8:
            return None
        return f"{fecha_str[:4]}-{fecha_str[4:6]}-{fecha_str[6:8]}"

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
                
                if 'parametro' in config:
                    self.parametro = config['parametro']
                    
                if 'metodo' in config:
                    self.metodo = config['metodo']
                
                if 'url' in config:
                    self.endpoint = config['url']
                
                if 'json envio' in config:
                    self._validar_json(config['json envio'], "El 'json envio' ")
                
                if 'fiche-xml' in config:
                    try:
                        json_guion = config['json envio']
                        json_objecto = json.loads(json_guion)
                        
                        if "nss" in json_objecto['datos']:
                            self.parametro = str(json_objecto['datos']['nss'])

                        path_xml = self.obtener_path(config['fiche-xml'].strip())
                        json_data = self.xml_a_json(path_xml)

                        if "#xmltojson#" in config['json envio']:
                            json_guion = config['json envio']
                            json_objecto = json.loads(json_guion)

                            del json_objecto['datos']['#xmltojson#'] # Elimina la clave marcadora si existe
                            
                            json_objecto['datos']['json_data'] = json_data
                            config['json envio'] = json.dumps(json_objecto)

                    except json.JSONDecodeError as e:
                        manejar_error_y_salir(self.fich_respuesta, f"{e}", self.usuario, self.endpoint, self.tiempo_inicio)
                    
            return config

        except Exception as e:
            manejar_error_y_salir(self.fich_respuesta, f"{e}", self.usuario, self.endpoint, self.tiempo_inicio)

    def acciones_cliente(self):
        try:
            acciones = {
                'POST': lambda: self.api_cliente.subir_cliente(self.endpoint),
                'GET': lambda: self.api_cliente.obtener_clientes(self.endpoint),
                'PUT': lambda: self.api_cliente.desactivar_cliente(self.endpoint),
                'DELETE': lambda: self._ejecutar_delete_cliente()
            }
            metodo = self.metodo.upper()
            if metodo in acciones:
                return acciones[metodo]()
            else:
                manejar_error_y_salir(self.fich_respuesta, f"Método {self.metodo} no soportado para acción cliente.", self.usuario, self.endpoint, self.tiempo_inicio)
        except Exception as e:
            manejar_error_y_salir(self.fich_respuesta, f"{e}", self.usuario, self.endpoint, self.tiempo_inicio)

    def _ejecutar_delete_cliente(self):
        self.endpoint = f"{self.endpoint}/{self.config['parametro']}"
        return self.api_cliente.borrar_cliente(self.endpoint)
        
    def acciones_certificado(self):
        try:
            acciones = {
                'POST': lambda: self.api_certificado.subir_certificado(),
                'GET': lambda: self.api_certificado.obtener_certificados(),
                'DELETE': lambda: self._ejecutar_delete()
            }
            
            metodo = self.metodo.upper()
            
            if metodo in acciones:
                return acciones[metodo]()
            else:
                manejar_error_y_salir(self.fich_respuesta, f"error: Método {metodo} no soportado para acción certificado.", self.usuario, self.endpoint, self.tiempo_inicio)        
        except Exception as e:
            manejar_error_y_salir(self.fich_respuesta, f"{e}", self.usuario, self.endpoint, self.tiempo_inicio)
    
    def _ejecutar_delete(self):
        self.endpoint = f"{self.endpoint}/{self.config['parametro']}"
        return self.api_certificado.borrar_certificado(self.endpoint)

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
                    manejar_error_y_salir(self.fich_respuesta, f"El campo 'datos' contiene un string que no es un JSON válido. {e}", self.usuario, self.endpoint, self.tiempo_inicio)

            datos_originales = data_json.copy()

            test = data_json.get("validar_sin_enviar")

            if "validar_sin_enviar" in data_json:
                testing = 1 if test == "true" or test == "True" else 0
                datos_originales.pop("validar_sin_enviar")
                if testing == 1:
                    datos_originales = {"test":testing, **datos_originales}

            if "cond_desempleado" in data_json:
                data_cond_desempleado = data_json.get("cond_desempleado")
                if data_cond_desempleado != "" and data_cond_desempleado in self.COND_DESEMPLEADO_VALIDOS:
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
            manejar_error_y_salir(self.fich_respuesta, f"El 'json envio' proporcionado no es un JSON válido. {e}", self.usuario, self.endpoint, self.tiempo_inicio)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.token}',
            'X-Cert-Secret': certificado
        }
        
        response = []
        
        try:
            if self.endpoint.rstrip('/').endswith('/contrata'):
                
                if self.metodo == 'DELETE':
                    response = requests.request(
                        method=self.metodo,
                        url=self.endpoint,
                        headers=headers,
                        json=datos_originales
                    )
                    if response.status_code == 200:
                        print("Contrato eliminado correctamente.")
                    #guardar_respuesta_completa(response, self.fich_respuesta, "query_avanza",  self.config, self.usuario, self.endpoint, self.metodo, self.tiempo_inicio)
                else:
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
            
            manejar_error_y_salir(self.fich_respuesta, error_message, self.usuario, self.endpoint, self.tiempo_inicio)

        except Exception as e:
            manejar_error_y_salir(self.fich_respuesta, f"{e}", self.usuario, self.endpoint, self.tiempo_inicio)

    def obtener_copia_basica(self, test, contrato, headers, response):      

        copia_basica_json ={}
        if test == 1:
            copia_basica_json["test"] = test
        
        
        copia_basica_json["cif"] = contrato.get("cif", "")
        copia_basica_json["dni"] = contrato.get("dni", "")
        copia_basica_json["startDate"] = contrato.get("startDate", "")

        reponse_copia_basica = requests.request(
            method="GET",
            url = "https://api.saltra.es/api/v4/sepe/copy-basic",
            headers=headers,
            json=copia_basica_json
        )
                
        try:
            dict1 = json.loads(response.text)
            dict2 = json.loads(reponse_copia_basica.text)
        except json.JSONDecodeError as e:
            manejar_error_y_salir(self.fich_respuesta, f"Error al decodificar JSON: {e}", self.usuario, self.endpoint, self.tiempo_inicio)

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

                    fecha_nacimiento = self._formatear_fecha(self.obtener_texto_nodo(contrato_node, 'DATOS_TRABAJADOR/FECHA_NACIMIENTO'))
                    
                    nacionalidad = int(self.obtener_texto_nodo(contrato_node, 'DATOS_TRABAJADOR/NACIONALIDAD', '0'))
                    municipio = int(self.obtener_texto_nodo(contrato_node, 'DATOS_TRABAJADOR/MUNICIPIO_RESIDENCIA', '0'))
                    pais_residencia = int(self.obtener_texto_nodo(contrato_node, 'DATOS_TRABAJADOR/PAIS_RESIDENCIA', '0'))

                    nss = self.obtener_texto_nodo(contrato_node, 'DATOS_TRABAJADOR/NUMERO_SEGURIDAD_SOCIAL')
                    # Asegura que el NSS tenga 12 dígitos, rellenando con ceros a la izquierda si es necesario
                    if nss:
                        nss = nss.zfill(12)
                    else:
                        nss = 0 
                    
                    nivel_formativo = int(self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/NIVEL_FORMATIVO', '0'))
                    ocupacion = self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/CODIGO_OCUPACION')
                    nacionalidad_contrato = int(self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/NACIONALIDAD_CT', '0'))
                    municipio_contrato = int(self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/MUNICIPIO_CT', '0'))
                    
                    real_decreto_1435_1985 = ""
                    if cod_contrato in self.CONTRATOS_REAL_DECRETO:
                        real_decreto_1435_1985 = self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/REAL_DECRETO_1435_1985')

                    collectiveAgreement = self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/IND_CONVENIO_COLECTIVO')

                    fecha_inicio = self._formatear_fecha(self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/FECHA_INICIO'))
                    
                    indicativo_prtr = self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/INDICATIVO_PRTR')
                    causa_sustitucion_str = self.obtener_texto_nodo(contrato_node, 'DATOS_CONTRATO_SUSTITUCION/CAUSA_SUSTITUCION')
                    causa_sustitucion = causa_sustitucion_str if causa_sustitucion_str is not None else None

                    horas_formacion = 0
                    minutos_formacion = 0
                    indicador_ere = None

                    if cod_contrato in self.CONTRATOS_HORAS_FORMACION:
                        horas_formacion_str = self.obtener_texto_nodo(contrato_node, 'DATOS_CONTRATO_TIEMPO_PARCIAL/HORAS_FORMACION', '0')
                        horas_formacion = int(horas_formacion_str)
                        minutos_formacion = 1
                        
                    # IND_ERE no existe en el XML, asumimos "N" (No)
                    indicador_ere = self.obtener_texto_nodo(contrato_node, 'DATOS_PRESTACIONES/IND_ERE', 'N')
                    fecha_fin = self._formatear_fecha(self.obtener_texto_nodo(contrato_node, 'DATOS_GENERALES_CONTRATO/FECHA_TERMINO'))

                    tipo_firma = self.obtener_texto_nodo(contrato_node, 'DATOS_COMUNICA_COPIA_BASICA/TIPO_FIRMA')
                    texto_copia_basica = self.obtener_texto_nodo(contrato_node, 'DATOS_COMUNICA_COPIA_BASICA/TEXTO_COPIABASICA')
                    texto_copia_basica = self.normalizar_texto(texto_copia_basica)                   

                    workplace = self.obtener_texto_nodo(contrato_node, 'DATOS_COMUNICA_COPIA_BASICA/DOMIC_CENTRO_TRABAJO')

                    if cod_contrato in self.TIEMPO_PARCIAL:
                        tipo_jornada = self.obtener_texto_nodo(contrato_node, 'DATOS_CONTRATO_TIEMPO_PARCIAL/TIPO_JORNADA')
                        horas_jornada = self.obtener_texto_nodo(contrato_node, 'DATOS_CONTRATO_TIEMPO_PARCIAL/HORAS_JORNADA')
                        minutos_jornada = 0

                    payload_api = {
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
                        "copyBasic": {
                            "TIPO_FIRMA": tipo_firma,
                            "TEXTO_COPIABASICA": texto_copia_basica,
                            "DOMIC_CENTRO_TRABAJO": workplace
                        },
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

                    if cod_contrato in self.TIEMPO_PARCIAL:
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

                fecha_nacimiento = self._formatear_fecha(self.obtener_texto_nodo(llamamiento_node, 'DATOS_TRABAJADOR/FECHA_NACIMIENTO'))
                
                nacionalidad = int(self.obtener_texto_nodo(llamamiento_node, 'DATOS_TRABAJADOR/NACIONALIDAD', '0'))
                municipio = int(self.obtener_texto_nodo(llamamiento_node, 'DATOS_TRABAJADOR/MUNICIPIO_RESIDENCIA', '0'))
                pais_residencia = int(self.obtener_texto_nodo(llamamiento_node, 'DATOS_TRABAJADOR/PAIS_RESIDENCIA', '0'))
                nss = self.obtener_texto_nodo(llamamiento_node, 'DATOS_TRABAJADOR/NUMERO_SEGURIDAD_SOCIAL', '0')
                if nss:
                    nss = nss.zfill(12)
                else:
                    nss = 0                

                fecha_inicio = self._formatear_fecha(self.obtener_texto_nodo(llamamiento_node, 'DATOS_LLAMAMIENTO/FECHA_INICIO'))

                fecha_fin = self._formatear_fecha(self.obtener_texto_nodo(llamamiento_node, 'DATOS_LLAMAMIENTO/FECHA_FIN'))
                
                nivel_formativo = int(self.obtener_texto_nodo(llamamiento_node, 'DATOS_LLAMAMIENTO/NIVEL_FORMATIVO', '0'))
                ocupacion = int(self.obtener_texto_nodo(llamamiento_node, 'DATOS_LLAMAMIENTO/CODIGO_OCUPACION', '0'))
                question = self.obtener_texto_nodo(llamamiento_node, 'DATOS_LLAMAMIENTO/IND_INCORPORA_ACTIVIDAD')

                sepeId = self.obtener_texto_nodo(llamamiento_node, 'DATOS_LLAMAMIENTO/CLAVE_CONTRATO_TRANS')
                sepeId = self.tratar_sepeId(sepeId)

                payload_api = {
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

    def normalizar_texto(self, texto: str) -> str:
        if not texto:
            return ""

        try:
            bytes_texto = texto.encode('iso-8859-1')
            texto = bytes_texto.decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass

        texto = re.sub(r'\s+', ' ', texto)

        # Quita espacios al inicio y final
        return texto.strip()

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
            manejar_error_y_salir(self.fich_respuesta, f"{e}", self.usuario, self.endpoint, self.tiempo_inicio)

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