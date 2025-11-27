#!/usr/bin/env python3
"""
Script cliente para API CONECTASS - Réplica exacta del sistema VB.NET
Uso: python conectass_client.py archivo.xml [config.ini]
"""
import json
import requests
import sys
from typing import Dict, Any
from dsenviosaltra_respuestas import guardar_respuesta_completa, crear_archivo_error,crear_archivo_fin

class DsEnvioSaltraCliente:
    def __init__(self, usuario, metodo, config: Dict[str, Any], fich_respuesta: str, token, tiempo_inicio):
        self.usuario = usuario
        self.metodo = metodo
        self.config = config
        self.fich_respuesta = fich_respuesta
        self.token = token
        self.tiempo_inicio = tiempo_inicio
        
    def subir_cliente(self, api_url):
        try: 
            try:
                data_dictionary = json.loads(self.config["json envio"])
            except json.JSONDecodeError as e:
                crear_archivo_error(self.fich_respuesta, f"error : El 'json envio' proporcionado no es un JSON válido. {e}", self.tiempo_inicio)
                crear_archivo_fin(self.fich_respuesta)
                sys.exit(1)
            
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {self.token}'
                }

                response = requests.post(api_url, headers=headers, json=data_dictionary)
                response.raise_for_status()
                guardar_respuesta_completa(response, self.fich_respuesta, "cliente", self.config, self.usuario, api_url, "POST", self.tiempo_inicio)

            except requests.exceptions.HTTPError as e:
                data_error = json.loads(e.response.text)
                mensaje_error = "error : {}".format(data_error["message"])
                crear_archivo_error(self.fich_respuesta, mensaje_error, self.tiempo_inicio)
                crear_archivo_fin(self.fich_respuesta)
                sys.exit(1) 
                
        except Exception as e:
            crear_archivo_error(self.fich_respuesta, f"error : {e}", self.tiempo_inicio)
            crear_archivo_fin(self.fich_respuesta)
            sys.exit(1)

    def borrar_cliente(self, api_url):
        try: 
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.token}'
            }
            response = requests.delete(api_url, headers=headers)
            response.raise_for_status()
            guardar_respuesta_completa(response, self.fich_respuesta, "cliente", self.config, self.usuario, api_url, "DELETE", self.tiempo_inicio)
        except Exception as e:
            crear_archivo_error(self.fich_respuesta, f"error : {e}", self.tiempo_inicio)
            crear_archivo_fin(self.fich_respuesta)
            sys.exit(1)
        
    def obtener_clientes(self, api_url):
        try:
 
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.token}'
            }

            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            guardar_respuesta_completa(response, self.fich_respuesta, "cliente", self.config, self.usuario, api_url, "GET", self.tiempo_inicio)

        except Exception as e:
            crear_archivo_error(self.fich_respuesta, f"error : {e}", self.tiempo_inicio)
            crear_archivo_fin(self.fich_respuesta)
            sys.exit(1)
    
    def desactivar_cliente(self, api_url):
        try: 
            try:
                data_dictionary = json.loads(self.config["json envio"])
                datos_originales = data_dictionary.copy()
            except json.JSONDecodeError as e:
                crear_archivo_error(self.fich_respuesta, f"error : El 'json envio' proporcionado no es un JSON válido. {e}", self.tiempo_inicio)
                crear_archivo_fin(self.fich_respuesta)
                sys.exit(1)
            
            if "active" in data_dictionary:
                active = True if data_dictionary.get("active") == "true" or data_dictionary.get("active") == "True"  else False
                datos_originales.pop("active")
                datos_originales = {"active":active}
            
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {self.token}'
                }

                response = requests.put(api_url, headers=headers, json=datos_originales)
                response.raise_for_status()
                guardar_respuesta_completa(response, self.fich_respuesta, "cliente", self.config, self.usuario, api_url, "PUT", self.tiempo_inicio)

            except requests.exceptions.HTTPError as e:
                data_error = json.loads(e.response.text)
                mensaje_error = "error : {}".format(data_error["message"])
                crear_archivo_error(self.fich_respuesta, mensaje_error, self.tiempo_inicio)
                crear_archivo_fin(self.fich_respuesta)
                sys.exit(1) 
                
        except Exception as e:
            crear_archivo_error(self.fich_respuesta, f"error : {e}", self.tiempo_inicio)
            crear_archivo_fin(self.fich_respuesta)
            sys.exit(1)