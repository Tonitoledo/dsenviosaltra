#!/usr/bin/env python3
import json
import base64
import requests
from typing import Dict, Any
from dsenviosaltra_respuestas import guardar_respuesta_completa, manejar_error_y_salir

class DsEnvioSaltraCertificado:
    def __init__(self, usuario, idUsuario, metodo, endpoint: str, config: Dict[str, Any], fich_respuesta: str, token, tiempo_inicio):
        self.usuario = usuario
        self.idUsuario = idUsuario
        self.metodo = metodo
        self.endpoint = endpoint
        self.config = config
        self.fich_respuesta = fich_respuesta
        self.token = token
        self.tiempo_inicio = tiempo_inicio


    def subir_certificado(self):
        api_url = self.endpoint
                
        try:
            data_dictionary = json.loads(self.config["json envio"])
        except json.JSONDecodeError as e:
            manejar_error_y_salir(self.fich_respuesta, f"El 'json envio' proporcionado no es un JSON válido. {e}", self.usuario, self.endpoint, self.tiempo_inicio)
    
        certificado_base64 = data_dictionary['certificado']
        password = data_dictionary['pwd']

        if not all([api_url, certificado_base64, password]):
            manejar_error_y_salir(self.fich_respuesta, "Faltan datos clave. Se necesita 'url' en el guion y 'certificado' y 'pwd' en el JSON de envío.", self.usuario, self.endpoint, self.tiempo_inicio)

        try:  
            try:
                datos_binarios_certificado = base64.b64decode(certificado_base64)
            except base64.binascii.Error as e:
                manejar_error_y_salir(self.fich_respuesta, f"El string Base64 proporcionado no es válido. Detalles: {e}", self.usuario, self.endpoint, self.tiempo_inicio)

            payload_data = {
                'password': password,
                #'clientId': int(idUsuario) 
            }

            
            payload_files = {
               'file': ("certificate.pfx", datos_binarios_certificado, 'application/pfx')
            }

            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.token}'
            }

            response = requests.post(
                api_url, 
                headers=headers, 
                data=payload_data, 
                files=payload_files
            )

            response.raise_for_status()
            guardar_respuesta_completa(response, self.fich_respuesta, "certificado", self.config, self.usuario, api_url, "POST", self.tiempo_inicio)

        except requests.exceptions.HTTPError as e:
            data_error = json.loads(e.response.text)
            mensaje_error = "error : {}".format(data_error["message"])
            manejar_error_y_salir(self.fich_respuesta, mensaje_error, self.usuario, self.endpoint, self.tiempo_inicio)
    
    def borrar_certificado(self, endpoint):
        try: 
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.token}'
            }
                    
            response = requests.delete(endpoint, headers=headers)
            response.raise_for_status()
            guardar_respuesta_completa(response, self.fich_respuesta, "certificado", self.config, self.usuario, endpoint, "DELETE", self.tiempo_inicio)
        except Exception as e:
            manejar_error_y_salir(self.fich_respuesta, f"{e}", self.usuario, self.endpoint, self.tiempo_inicio)

    def obtener_certificados(self):
        api_url = self.endpoint

        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.token}'
            }
                    
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            guardar_respuesta_completa(response, self.fich_respuesta, "certificado", self.config, self.usuario, api_url, "GET", self.tiempo_inicio)

        except Exception as e:
            manejar_error_y_salir(self.fich_respuesta, f"{e}", self.usuario, self.endpoint, self.tiempo_inicio)