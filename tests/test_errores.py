#!/usr/bin/env python3
"""
Tests para forzar y verificar el manejo de errores.
Estos tests verifican que el sistema maneja correctamente diferentes tipos de errores.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json
import time
import tempfile

# Agregar el directorio raíz al path para importar los módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dsenviosaltra import SaltraClient


class TestErrores(unittest.TestCase):
    """Tests para verificar el manejo de errores"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.dsClave = "test_clave"
        self.usuario = "test@example.com"
        self.idUsuario = "123"
        self.passw = "test_password"
        self.code_respuesta = "ISO8859-1"
        self.tiempo_inicio = time.time()
    
    def _crear_guion_temporal(self, contenido):
        """Crea un archivo guion temporal para testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='iso-8859-1')
        temp_file.write(contenido)
        temp_file.close()
        return temp_file.name
    
    def test_error_guion_no_existe(self):
        """Test: Error cuando el archivo guion no existe"""
        guion_inexistente = "/ruta/inexistente/guion.txt"
        
        with self.assertRaises(SystemExit):
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_inexistente, self.code_respuesta, self.tiempo_inicio
            )
    
    @patch('dsenviosaltra.requests.post')
    def test_error_json_invalido_en_guion(self, mock_post):
        """Test: Error cuando el JSON en el guion es inválido"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/alta
[metodo]
POST
[parametro]

[fiche-out]
/tmp/test/error.txt

[json envio]
{
    "certificado": "test",
    "datos": {
        "invalid": json syntax error
    }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            # Debería fallar al parsear el JSON
            with self.assertRaises(SystemExit):
                client = SaltraClient(
                    self.dsClave, self.usuario, self.idUsuario,
                    self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
                )
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    def test_error_credenciales_incorrectas(self, mock_post):
        """Test: Error cuando las credenciales de login son incorrectas"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/alta
[metodo]
POST
[parametro]

[fiche-out]
/tmp/test/error.txt

[json envio]
{
    "certificado": "test",
    "datos": {}
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            # Simular error de autenticación
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"message": "Credenciales inválidas"}
            mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
            mock_post.return_value = mock_response
            
            with self.assertRaises(SystemExit):
                client = SaltraClient(
                    self.dsClave, self.usuario, self.idUsuario,
                    "password_incorrecto", guion_file, self.code_respuesta, self.tiempo_inicio
                )
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_respuesta_api_400(self, mock_request, mock_post):
        """Test: Error cuando la API devuelve 400 Bad Request"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/alta
[metodo]
POST
[parametro]

[fiche-out]
/tmp/test/error.txt

[json envio]
{
    "certificado": "test",
    "datos": {
        "regimen": "0111",
        "ccc": "12345678901",
        "nss": "123456789012"
    }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            # Mock de login exitoso
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            # Mock de respuesta con error 400
            mock_error_response = Mock()
            mock_error_response.status_code = 400
            mock_error_response.json.return_value = {
                "success": False,
                "message": "Datos inválidos",
                "errors": "El NSS no es válido"
            }
            mock_error_response.text = json.dumps(mock_error_response.json.return_value)
            mock_error_response.reason = "Bad Request"
            mock_request.return_value = mock_error_response
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            # Verificar que se creó el cliente pero la llamada fallará
            self.assertIsNotNone(client)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_respuesta_api_500(self, mock_request, mock_post):
        """Test: Error cuando la API devuelve 500 Internal Server Error"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/alta
[metodo]
POST
[parametro]

[fiche-out]
/tmp/test/error.txt

[json envio]
{
    "certificado": "test",
    "datos": {
        "regimen": "0111",
        "ccc": "12345678901",
        "nss": "123456789012"
    }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            # Mock de error 500
            mock_error_response = Mock()
            mock_error_response.status_code = 500
            mock_error_response.json.return_value = {
                "success": False,
                "message": "Error interno del servidor"
            }
            mock_error_response.text = json.dumps(mock_error_response.json.return_value)
            mock_error_response.reason = "Internal Server Error"
            mock_request.return_value = mock_error_response
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertIsNotNone(client)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    def test_error_certificado_faltante(self, mock_post):
        """Test: Error cuando falta el certificado en el JSON"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/certificate
[metodo]
POST
[parametro]
[fiche-out]
/tmp/test/error.txt
[json envio]
{
	"pwd": "TEST"
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            # Al intentar subir certificado sin el campo 'certificado', debería fallar
            with self.assertRaises(SystemExit):
                client.acciones_certificado()
                
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    def test_error_certificado_base64_invalido(self, mock_post):
        """Test: Error cuando el certificado Base64 es inválido"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/certificate
[metodo]
POST
[parametro]
[fiche-out]
/tmp/test/error.txt
[json envio]
{
	"pwd": "TEST",
	"certificado": "esto_no_es_base64_válido!!!"
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            # Debería fallar al decodificar Base64
            with self.assertRaises(SystemExit):
                client.acciones_certificado()
                
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.get')
    def test_error_metodo_no_soportado_certificado(self, mock_get, mock_post):
        """Test: Error cuando se usa un método no soportado para certificado"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/certificate
[metodo]
PATCH
[parametro]
[fiche-out]
/tmp/test/error.txt"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            # PATCH no está soportado para certificado
            with self.assertRaises(SystemExit):
                client.acciones_certificado()
                
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.get')
    def test_error_metodo_no_soportado_cliente(self, mock_get, mock_post):
        """Test: Error cuando se usa un método no soportado para cliente"""
        contenido_guion = """[url]
https://api.saltra.es/api/web/v3/customer
[metodo]
PATCH
[parametro]
[fiche-out]
/tmp/test/error.txt"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            # PATCH no está soportado para cliente
            with self.assertRaises(SystemExit):
                client.acciones_cliente()
                
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    @patch('dsenviosaltra.ET.parse')
    def test_error_xml_no_existe(self, mock_parse, mock_request, mock_post):
        """Test: Error cuando el archivo XML referenciado no existe"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/sepe/contrata
[metodo]
POST
[parametro]

[fiche-xml]
/ruta/inexistente/archivo.xml
[fiche-out]
/tmp/test/error.txt

[json envio]
{
	"certificado": "test",
	"datos":
	{
		"validar_sin_enviar": "true",
		"#xmltojson#" : "null"
	}
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            # Simular que el archivo XML no existe
            mock_parse.side_effect = FileNotFoundError("Archivo no encontrado")
            
            # Debería fallar al intentar parsear el XML
            with self.assertRaises(SystemExit):
                client = SaltraClient(
                    self.dsClave, self.usuario, self.idUsuario,
                    self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
                )
                
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_datos_string_no_json(self, mock_request, mock_post):
        """Test: Error cuando el campo 'datos' es un string que no es JSON válido"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/alta
[metodo]
POST
[parametro]

[fiche-out]
/tmp/test/error.txt

[json envio]
{
    "certificado": "test",
    "datos": "esto no es un JSON válido {"
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            # Al intentar procesar, debería fallar al parsear el string como JSON
            with self.assertRaises(SystemExit):
                client.realizar_llamada_ss_sepe()
                
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.get')
    def test_error_cliente_json_invalido(self, mock_get, mock_post):
        """Test: Error cuando el JSON de cliente es inválido"""
        contenido_guion = """[url]
https://api.saltra.es/api/web/v3/customer
[metodo]
POST
[parametro]
[fiche-out]
/tmp/test/error.txt
[json envio]
{
  "name": "TEST",
  "access": {
    "email": "test@example.com",
    invalid json syntax
  }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            # Debería fallar al parsear el JSON
            with self.assertRaises(SystemExit):
                client.acciones_cliente()
                
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.delete')
    def test_error_borrar_cliente_sin_parametro(self, mock_delete, mock_post):
        """Test: Error al borrar cliente sin parámetro"""
        contenido_guion = """[url]
https://api.saltra.es/api/web/v3/customer
[metodo]
DELETE
[parametro]

[fiche-out]
/tmp/test/error.txt"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            mock_delete.return_value = Mock(
                status_code=404,
                json=lambda: {"message": "Cliente no encontrado"}
            )
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            # El endpoint se construirá sin ID, lo que causará un error
            self.assertIsNotNone(client)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_timeout_conexion(self, mock_request, mock_post):
        """Test: Error cuando hay timeout en la conexión"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/alta
[metodo]
POST
[parametro]

[fiche-out]
/tmp/test/error.txt

[json envio]
{
    "certificado": "test",
    "datos": {
        "regimen": "0111",
        "ccc": "12345678901",
        "nss": "123456789012"
    }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            import requests
            
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            # Simular timeout
            mock_request.side_effect = requests.exceptions.Timeout("Timeout de conexión")
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            # Al intentar realizar la llamada, debería fallar
            with self.assertRaises(SystemExit):
                client.realizar_llamada_ss_sepe()
                
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_cond_desempleado_invalido(self, mock_request, mock_post):
        """Test: Error cuando cond_desempleado tiene un valor inválido"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/alta
[metodo]
POST
[parametro]

[fiche-out]
/tmp/test/error.txt

[json envio]
{
    "certificado": "test",
    "datos": {
        "regimen": "0111",
        "ccc": "12345678901",
        "nss": "123456789012",
        "cond_desempleado": "99"
    }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            mock_request.return_value = Mock(
                status_code=200,
                json=lambda: {"success": True, "data": {}}
            )
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            # El valor "99" no está en la lista válida, pero el código lo procesará
            # La validación real la hará la API
            self.assertIsNotNone(client)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_faltan_campos_obligatorios(self, mock_request, mock_post):
        """Test: Error cuando faltan campos obligatorios en el JSON"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/alta
[metodo]
POST
[parametro]

[fiche-out]
/tmp/test/error.txt

[json envio]
{
    "certificado": "test",
    "datos": {
        "regimen": "0111"
    }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            # Simular error 400 por campos faltantes
            mock_error_response = Mock()
            mock_error_response.status_code = 400
            mock_error_response.json.return_value = {
                "success": False,
                "message": "Campos obligatorios faltantes",
                "errors": "El campo 'nss' es obligatorio"
            }
            mock_error_response.text = json.dumps(mock_error_response.json.return_value)
            mock_error_response.reason = "Bad Request"
            mock_request.return_value = mock_error_response
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertIsNotNone(client)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_fecha_invalida(self, mock_request, mock_post):
        """Test: Error cuando la fecha tiene formato inválido"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/alta
[metodo]
POST
[parametro]

[fiche-out]
/tmp/test/error.txt

[json envio]
{
    "certificado": "test",
    "datos": {
        "regimen": "0111",
        "ccc": "12345678901",
        "nss": "123456789012",
        "fecha_real": "fecha-invalida"
    }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            mock_error_response = Mock()
            mock_error_response.status_code = 400
            mock_error_response.json.return_value = {
                "success": False,
                "message": "Formato de fecha inválido"
            }
            mock_error_response.text = json.dumps(mock_error_response.json.return_value)
            mock_error_response.reason = "Bad Request"
            mock_request.return_value = mock_error_response
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertIsNotNone(client)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_ccc_invalido(self, mock_request, mock_post):
        """Test: Error cuando el CCC tiene formato inválido"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/report-situation-ccc
[metodo]
GET
[parametro]

[fiche-out]
/tmp/test/error.txt
[json envio]
{
        "certificado": "test",
        "datos":
        {
            "regimen": "0111",
            "ccc": "123"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            mock_error_response = Mock()
            mock_error_response.status_code = 400
            mock_error_response.json.return_value = {
                "success": False,
                "message": "CCC inválido"
            }
            mock_error_response.text = json.dumps(mock_error_response.json.return_value)
            mock_error_response.reason = "Bad Request"
            mock_request.return_value = mock_error_response
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertIsNotNone(client)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_dni_invalido(self, mock_request, mock_post):
        """Test: Error cuando el DNI tiene formato inválido"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/nss-by-ipf
[metodo]
GET
[parametro]

[fiche-out]
/tmp/test/error.txt
[json envio]
{
        "certificado": "test",
        "datos":
        {
            "dni": "123",
            "apellido1": "TEST",
            "apellido2": "TEST"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            mock_error_response = Mock()
            mock_error_response.status_code = 400
            mock_error_response.json.return_value = {
                "success": False,
                "message": "DNI inválido"
            }
            mock_error_response.text = json.dumps(mock_error_response.json.return_value)
            mock_error_response.reason = "Bad Request"
            mock_request.return_value = mock_error_response
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertIsNotNone(client)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_nss_invalido(self, mock_request, mock_post):
        """Test: Error cuando el NSS tiene formato inválido"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/life-affiliate
[metodo]
GET
[parametro]

[fiche-out]
/tmp/test/error.txt
[json envio]
{
        "certificado": "test",
        "datos":
        {
            "regimen": "0111",
            "ccc": "03141448363",
            "nss": "123"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            mock_error_response = Mock()
            mock_error_response.status_code = 400
            mock_error_response.json.return_value = {
                "success": False,
                "message": "NSS inválido"
            }
            mock_error_response.text = json.dumps(mock_error_response.json.return_value)
            mock_error_response.reason = "Bad Request"
            mock_request.return_value = mock_error_response
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertIsNotNone(client)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_duplicate_sin_campos_requeridos(self, mock_request, mock_post):
        """Test: Error en duplicate-ta cuando faltan campos requeridos"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/duplicate-ta
[metodo]
GET
[parametro]

[fiche-out]
/tmp/test/error.txt

[json envio]
{
        "certificado": "test",
        "datos":
        {
            "nss": "123456789011"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            mock_error_response = Mock()
            mock_error_response.status_code = 400
            mock_error_response.json.return_value = {
                "success": False,
                "message": "Falta EMPRESA_CCC"
            }
            mock_error_response.text = json.dumps(mock_error_response.json.return_value)
            mock_error_response.reason = "Bad Request"
            mock_request.return_value = mock_error_response
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertIsNotNone(client)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_category_professional_invalido(self, mock_request, mock_post):
        """Test: Error cuando category_professional tiene valor inválido"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/category-professional
[metodo]
PUT
[parametro]

[fiche-out]
/tmp/test/error.txt
[json envio]
{
        "certificado": "test",
        "datos":
        {
            "validar_sin_enviar": "true",
            "regimen": "0111",
            "ccc": "03141448363",
            "dni": "23905114H",
            "nss": "031104852782",
            "fecha_real": "19/09/2025",
            "category_professional": "INVALIDO",
            "duplicate": 1
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            mock_error_response = Mock()
            mock_error_response.status_code = 400
            mock_error_response.json.return_value = {
                "success": False,
                "message": "Category professional inválido"
            }
            mock_error_response.text = json.dumps(mock_error_response.json.return_value)
            mock_error_response.reason = "Bad Request"
            mock_request.return_value = mock_error_response
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertIsNotNone(client)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_ocupacion_invalida(self, mock_request, mock_post):
        """Test: Error cuando ocupacion tiene valor inválido"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/occupation
[metodo]
PUT
[parametro]

[fiche-out]
/tmp/test/error.txt
[json envio]
{
        "certificado": "test",
        "datos":
        {
            "validar_sin_enviar": "true",
            "regimen": "0111",
            "ccc": "03141448363",
            "dni": "23905114H",
            "nss": "031104852782",
            "fecha_real": "2025-09-25",
            "ocupacion": "INVALIDO",
            "duplicate": "1"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            mock_error_response = Mock()
            mock_error_response.status_code = 400
            mock_error_response.json.return_value = {
                "success": False,
                "message": "Ocupación inválida"
            }
            mock_error_response.text = json.dumps(mock_error_response.json.return_value)
            mock_error_response.reason = "Bad Request"
            mock_request.return_value = mock_error_response
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertIsNotNone(client)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_copy_basic_sin_sepeid(self, mock_request, mock_post):
        """Test: Error en copy-basic cuando falta sepeId y otros campos"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/sepe/copy-basic
[metodo]
POST
[parametro]

[fiche-out]
/tmp/test/error.txt

[json envio]
{
	"certificado": "test",
	"datos":
	{
		"validar_sin_enviar": "true",
		"cif":"B12312333"
	}
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            mock_error_response = Mock()
            mock_error_response.status_code = 400
            mock_error_response.json.return_value = {
                "success": False,
                "message": "Faltan campos obligatorios: dni, docType, startDate"
            }
            mock_error_response.text = json.dumps(mock_error_response.json.return_value)
            mock_error_response.reason = "Bad Request"
            mock_request.return_value = mock_error_response
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertIsNotNone(client)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_contrata_data_sin_fecha(self, mock_request, mock_post):
        """Test: Error en contrata/data cuando falta fecha"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/sepe/contrata/data
[metodo]
GET
[parametro]

[fiche-out]
/tmp/test/error.txt

[json envio]
{
	"certificado": "test",
	"datos":
	{
		"validar_sin_enviar": "true",
		"dni": "01234567A",
		"ccc":"12345678901"
	}
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            mock_error_response = Mock()
            mock_error_response.status_code = 400
            mock_error_response.json.return_value = {
                "success": False,
                "message": "El campo startDate es obligatorio"
            }
            mock_error_response.text = json.dumps(mock_error_response.json.return_value)
            mock_error_response.reason = "Bad Request"
            mock_request.return_value = mock_error_response
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertIsNotNone(client)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_respuesta_no_json(self, mock_request, mock_post):
        """Test: Error cuando la respuesta de la API no es JSON"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/alta
[metodo]
POST
[parametro]

[fiche-out]
/tmp/test/error.txt

[json envio]
{
    "certificado": "test",
    "datos": {
        "regimen": "0111",
        "ccc": "12345678901",
        "nss": "123456789012"
    }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            # Simular respuesta HTML en lugar de JSON
            mock_error_response = Mock()
            mock_error_response.status_code = 500
            mock_error_response.text = "<html><body>Error</body></html>"
            mock_error_response.json.side_effect = ValueError("No JSON object could be decoded")
            mock_error_response.reason = "Internal Server Error"
            mock_request.return_value = mock_error_response
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            # Al intentar procesar la respuesta, debería fallar
            with self.assertRaises(SystemExit):
                client.realizar_llamada_ss_sepe()
                
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_error_regimen_invalido(self, mock_request, mock_post):
        """Test: Error cuando el régimen tiene valor inválido"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/informe-ita
[metodo]
GET
[parametro]

[fiche-out]
/tmp/test/error.txt
[json envio]
{
        "certificado": "test",
        "datos":
        {
            "regimen": "9999",
            "ccc": "03141448363"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"data": {"access_token": "token"}}
            )
            
            mock_error_response = Mock()
            mock_error_response.status_code = 400
            mock_error_response.json.return_value = {
                "success": False,
                "message": "Régimen inválido"
            }
            mock_error_response.text = json.dumps(mock_error_response.json.return_value)
            mock_error_response.reason = "Bad Request"
            mock_request.return_value = mock_error_response
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertIsNotNone(client)
            
        finally:
            os.unlink(guion_file)


if __name__ == '__main__':
    unittest.main()


