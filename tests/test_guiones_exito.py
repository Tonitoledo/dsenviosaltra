#!/usr/bin/env python3
"""
Tests para verificar que cada guion funciona correctamente.
Cada test simula la ejecución exitosa de un guion específico.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
import os
import json
import time
from pathlib import Path

# Agregar el directorio raíz al path para importar los módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dsenviosaltra import SaltraClient


class TestGuionesExito(unittest.TestCase):
    """Tests para verificar que cada guion funciona correctamente"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.dsClave = "test_clave"
        self.usuario = "test@example.com"
        self.idUsuario = "123"
        self.passw = "test_password"
        self.code_respuesta = "ISO8859-1"
        self.tiempo_inicio = time.time()
        
        # Mock del token de autenticación
        self.mock_token = "mock_access_token_12345"
        
    def _crear_guion_temporal(self, contenido):
        """Crea un archivo guion temporal para testing"""
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='iso-8859-1')
        temp_file.write(contenido)
        temp_file.close()
        return temp_file.name
    
    def _mock_respuesta_api_exitosa(self, status_code=200, data=None):
        """Crea un mock de respuesta exitosa de la API"""
        if data is None:
            data = {"success": True, "data": {"id": "12345"}}
        
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = data
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.text = json.dumps(data)
        return mock_response
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.get')
    @patch('dsenviosaltra.requests.put')
    @patch('dsenviosaltra.requests.delete')
    @patch('dsenviosaltra.requests.request')
    def test_guion_01_alta_seg_social(self, mock_request, mock_delete, mock_put, mock_get, mock_post):
        """Test para guion_01: Alta en Seguridad Social"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/alta
[metodo]
POST
[parametro]

[fiche-out]
/tmp/test/param_0001.txt

[json envio]
{
	"certificado": "test_cert",
	"datos":
	{
		"validar_sin_enviar": "false",
		"regimen": "0111",
		"ccc": "06005271108",
		"nss": "061018619229",
		"identificacion": "1",
		"dni": "52359707T",
		"fecha_real": "2025-11-18",
		"grupo_cotizacion": "07",
		"tipo_contrato": "410",
		"cno": "4500",
		"duplicate": "1",
		"obtener_idc": "1",
		"cond_desempleado": "1"
	}
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            # Mock de login
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            # Mock de la llamada principal
            mock_request.return_value = self._mock_respuesta_api_exitosa()
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario, 
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            # Verificar que se inicializó correctamente
            self.assertEqual(client.metodo, "POST")
            self.assertIn("seg-social/alta", client.endpoint)
            self.assertEqual(client.accion_deducida, "query_avanza")
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.get')
    @patch('dsenviosaltra.requests.put')
    @patch('dsenviosaltra.requests.delete')
    @patch('dsenviosaltra.requests.request')
    def test_guion_02_baja_seg_social(self, mock_request, mock_delete, mock_put, mock_get, mock_post):
        """Test para guion_02: Baja en Seguridad Social"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/baja
[metodo]
POST
[parametro]

[fiche-out]
/tmp/test/param_0002.txt

[json envio]
{
        "certificado": "test_cert",
        "datos":
        {
                "validar_sin_enviar": "true",
                "regimen": "0111",
                "ccc": "03141448363",
                "nss": "031104852782",
                "identificacion": "1",
                "dni": "23905114H",
                "fecha_real": "2025-10-21",
                "situacion": "51",
                "duplicate": "1",
                "obtener_idc": "1"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            mock_request.return_value = self._mock_respuesta_api_exitosa()
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "POST")
            self.assertIn("seg-social/baja", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.get')
    def test_guion_subir_certificado(self, mock_get, mock_post):
        """Test para guion_subir_certificado: Subir certificado"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/certificate
[metodo]
POST
[parametro]
[fiche-out]
/tmp/test/subircert.txt
[json envio]
{
	"pwd": "TEST",
	"certificado": "MIIPJgIBAzCCDuIGCSqGSIb3DQEHAaCCDtMEgg7P"
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            # Mock para la subida del certificado
            mock_response_cert = self._mock_respuesta_api_exitosa(
                data={"data": {"cert_secret": "new_cert_secret"}}
            )
            mock_post.side_effect = [
                self._mock_respuesta_api_exitosa(data={"data": {"access_token": self.mock_token}}),
                mock_response_cert
            ]
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "POST")
            self.assertIn("certificate", client.endpoint)
            self.assertEqual(client.accion_deducida, "certificado")
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.get')
    def test_guion_obtener_certificados(self, mock_get, mock_post):
        """Test para guion_obtener_certificados: Obtener listado de certificados"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/certificate
[metodo]
GET
[parametro]

[fiche-out]
/tmp/test/listacert.txt"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_get.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"data": [{"cert_secret": "cert1"}, {"cert_secret": "cert2"}]}}
            )
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "GET")
            self.assertIn("certificate", client.endpoint)
            self.assertEqual(client.accion_deducida, "certificado")
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.delete')
    def test_guion_borrar_certificado(self, mock_delete, mock_post):
        """Test para guion_borrar_certificado: Borrar certificado"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/certificate
[metodo]
DELETE
[parametro]
test_cert_secret
[fiche-out]
/tmp/test/bajacert.txt"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_delete.return_value = self._mock_respuesta_api_exitosa(
                status_code=200,
                data={"success": True, "message": "Certificado eliminado"}
            )
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "DELETE")
            self.assertIn("certificate", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.get')
    def test_guion_subir_clientes(self, mock_get, mock_post):
        """Test para guion_subir_clientes: Subir cliente"""
        contenido_guion = """[url]
https://api.saltra.es/api/web/v3/customer
[metodo]
POST
[parametro]
[fiche-out]
/tmp/test/subircliente.txt
[json envio]
{
  "name": "TEST CLIENTE",
  "access": {
    "email": "test@example.com",
    "password": "Test123.",
    "password_confirmation": "Test123."
  },
  "profile": {
    "dni": "A12345678",
    "razon_social": "TEST S.A.",
    "account": [
      {
        "regimen": "0111",
        "cuenta": "12345678901",
        "alias": "Test"
      }]
  }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.side_effect = [
                self._mock_respuesta_api_exitosa(data={"data": {"access_token": self.mock_token}}),
                self._mock_respuesta_api_exitosa(data={"data": {"id": "123", "name": "TEST CLIENTE"}})
            ]
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "POST")
            self.assertIn("customer", client.endpoint)
            self.assertEqual(client.accion_deducida, "cliente")
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.get')
    def test_guion_listado_clientes(self, mock_get, mock_post):
        """Test para guion_listado_clientes: Listar clientes"""
        contenido_guion = """[url]
https://api.saltra.es/api/web/v3/customer
[metodo]
GET
[parametro]
[fiche-out]
/tmp/test/listaclientes.txt"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_get.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"data": [{"id": "1", "name": "Cliente 1"}, {"id": "2", "name": "Cliente 2"}]}}
            )
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "GET")
            self.assertIn("customer", client.endpoint)
            self.assertEqual(client.accion_deducida, "cliente")
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.put')
    def test_guion_desactivar_cliente(self, mock_put, mock_post):
        """Test para guion_desactivar_cliente: Desactivar cliente"""
        contenido_guion = """[url]
https://api.saltra.es/api/web/v3/customer/123/activate
[metodo]
PUT
[parametro]
[fiche-out]
/tmp/test/desactivar_cliente.txt
[json envio]
{
    "active": "false"
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_put.return_value = self._mock_respuesta_api_exitosa(
                data={"success": True, "message": "Cliente desactivado"}
            )
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "PUT")
            self.assertIn("customer", client.endpoint)
            self.assertEqual(client.accion_deducida, "cliente")
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.delete')
    def test_guion_borrar_clientes(self, mock_delete, mock_post):
        """Test para guion_borrar_clientes: Borrar cliente"""
        contenido_guion = """[url]
https://api.saltra.es/api/web/v3/customer
[metodo]
DELETE
[parametro]
123
[fiche-out]
/tmp/test/borrarcliente.txt"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_delete.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"id": "123", "name": "Cliente eliminado"}}
            )
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "DELETE")
            self.assertIn("customer", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    @patch('dsenviosaltra.ET.parse')
    def test_guion_101_contrata(self, mock_parse, mock_request, mock_post):
        """Test para guion_101: Contrata con XML"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/sepe/contrata
[metodo]
POST
[parametro]

[fiche-xml]
/tmp/test/CONTR402.xml
[fiche-out]
/tmp/test/param_0101.txt

[json envio]
{
	"certificado": "test_cert",
	"datos":
	{
		"validar_sin_enviar": "true",
		"#xmltojson#" : "null"
	}
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            # Mock del XML
            mock_root = Mock()
            mock_root.tag = "CONTRATOS"
            mock_contrato = Mock()
            mock_contrato.tag = "CONTRATO_402"
            mock_root.__iter__ = Mock(return_value=iter([mock_contrato]))
            mock_tree = Mock()
            mock_tree.getroot.return_value = mock_root
            mock_parse.return_value = mock_tree
            
            # Mock de obtener_texto_nodo
            def mock_obtener_texto_nodo(nodo, ruta, default=""):
                return "test_value"
            
            mock_request.return_value = self._mock_respuesta_api_exitosa()
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "POST")
            self.assertIn("contrata", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    @patch('dsenviosaltra.ET.parse')
    def test_guion_104_llamamientos(self, mock_parse, mock_request, mock_post):
        """Test para guion_104: Llamamientos"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/sepe/llamamientos
[parametro]

[fiche-xml]
/tmp/test/llamamiento.xml
[metodo]
POST
[fiche-out]
/tmp/test/param_0104.txt

[json envio]
{
        "certificado": "test_cert",
        "datos":
        {
                "validar_sin_enviar": "false",
                "#xmltojson#": "null"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            # Mock del XML para llamamiento
            mock_root = Mock()
            mock_root.tag = "LLAMAMIENTO"
            mock_llamamiento = Mock()
            mock_root.find.return_value = mock_llamamiento
            mock_tree = Mock()
            mock_tree.getroot.return_value = mock_root
            mock_parse.return_value = mock_tree
            
            mock_request.return_value = self._mock_respuesta_api_exitosa()
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "POST")
            self.assertIn("llamamientos", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_guion_012_idc_info(self, mock_request, mock_post):
        """Test para guion_012: IDC Info for NSS"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/idc-info-for-nss
[parametro]

[metodo]
GET
[fiche-out]
/tmp/test/param_0012.txt

[json envio]
{
        "certificado": "test_cert",
        "datos":
        {
            "regimen": "0111",
            "ccc": "08208093015",
            "nss": "081079806389"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_request.return_value = self._mock_respuesta_api_exitosa()
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "GET")
            self.assertIn("idc-info-for-nss", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_guion_013_employees_enterprise(self, mock_request, mock_post):
        """Test para guion_013: Employees in Enterprise"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/employees-in-enterprise
[parametro]

[metodo]
GET
[fiche-out]
/tmp/test/param_0013.txt

[json envio]
{
        "certificado": "test_cert",
        "datos":
        {
            "regimen": "0111",
            "ccc": "46146472731",
            "options": "3"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_request.return_value = self._mock_respuesta_api_exitosa(
                data={"success": True, "data": {"employees": []}}
            )
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "GET")
            self.assertIn("employees-in-enterprise", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_guion_04_contract_coeficiente(self, mock_request, mock_post):
        """Test para guion_04: Contract Coeficiente"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/contract-coeficiente
[metodo]
PUT
[parametro]

[fiche-out]
/tmp/test/param_0004.txt
[json envio]
{
        "certificado": "test_cert",
        "datos":
        {
                "validar_sin_enviar": "true",
                "regimen": "0111",
                "ccc": "03141448363",
                "dni": "23905114H",
                "nss": "031104852782",
                "startDate": "2024-06-24",
                "contractType": "100",
                "coeficiente": "200"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_request.return_value = self._mock_respuesta_api_exitosa()
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "PUT")
            self.assertIn("contract-coeficiente", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_guion_05_employee_situations(self, mock_request, mock_post):
        """Test para guion_05: Employee Situations"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/employee-situations
[metodo]
GET
[parametro]

[fiche-out]
/tmp/test/param_0005.txt
[json envio]
{
        "certificado": "test_cert",
        "datos":
        {
                "regimen": "0111",
                "ccc": "03141448363",
                "dni": "23905114H"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_request.return_value = self._mock_respuesta_api_exitosa()
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "GET")
            self.assertIn("employee-situations", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_guion_081_life_ccc(self, mock_request, mock_post):
        """Test para guion_081: Life CCC"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/life-ccc
[parametro]

[metodo]
GET
[fiche-out]
/tmp/test/param_0081.txt

[json envio]
{
        "certificado": "test_cert",
        "datos":
        {
                "regimen":"0111",
                "ccc":"46146472731",
                "startDate": "2025-01-01",
                "endDate": "2025-09-12"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_request.return_value = self._mock_respuesta_api_exitosa()
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "GET")
            self.assertIn("life-ccc", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_guion_06_report_situation_ccc(self, mock_request, mock_post):
        """Test para guion_06: Report Situation CCC"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/report-situation-ccc
[metodo]
GET
[parametro]

[fiche-out]
/tmp/test/param_0006.txt
[json envio]
{
        "certificado": "test_cert",
        "datos":
        {
                                "regimen": "0111",
                                "ccc": "46146472731"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_request.return_value = self._mock_respuesta_api_exitosa()
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "GET")
            self.assertIn("report-situation-ccc", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_guion_07_nss_by_ipf(self, mock_request, mock_post):
        """Test para guion_07: NSS by IPF"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/nss-by-ipf
[metodo]
GET
[parametro]

[fiche-out]
/tmp/test/param_0007.txt
[json envio]
{
        "certificado": "test_cert",
        "datos":
        {
                                "dni": "23905114H",
                                "apellido1": "PULIDO",
                                "apellido2": "OSTIO"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_request.return_value = self._mock_respuesta_api_exitosa()
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "GET")
            self.assertIn("nss-by-ipf", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_guion_08_duplicate_ta(self, mock_request, mock_post):
        """Test para guion_08: Duplicate TA"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/duplicate-ta
[parametro]

[metodo]
GET
[fiche-out]
/tmp/test/param_0008.txt

[json envio]
{
        "certificado": "test_cert",
        "datos":
        {
            "EMPRESA_CCC": "011146146472731",
            "nss": "123456789011",
            "DESDE": "2025-01-01",
            "movType": "ALTA"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_request.return_value = self._mock_respuesta_api_exitosa()
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "GET")
            self.assertIn("duplicate-ta", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_guion_020_category_professional(self, mock_request, mock_post):
        """Test para guion_020: Category Professional"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/category-professional
[metodo]
PUT
[parametro]

[fiche-out]
/tmp/test/param_0020.txt
[json envio]
{
        "certificado": "test_cert",
        "datos":
        {
                                "validar_sin_enviar": "true",
                                "regimen": "0111",
                                "ccc": "03141448363",
                                "dni": "23905114H",
                                "nss": "031104852782",
                                "fecha_real": "19/09/2025",
                                "category_professional": "6100517",
                                "duplicate": 1
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_request.return_value = self._mock_respuesta_api_exitosa()
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "PUT")
            self.assertIn("category-professional", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_guion_028_occupation(self, mock_request, mock_post):
        """Test para guion_028: Occupation"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/occupation
[metodo]
PUT
[parametro]

[fiche-out]
/tmp/test/param_0028.txt
[json envio]
{
        "certificado": "test_cert",
        "datos":
        {
                "validar_sin_enviar": "true",
                "regimen": "0111",
                "ccc": "03141448363",
                "dni": "23905114H",
                "nss": "031104852782",
                "fecha_real": "2025-09-25",
                "ocupacion": "z",
                "duplicate": "1"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_request.return_value = self._mock_respuesta_api_exitosa()
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "PUT")
            self.assertIn("occupation", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_guion_062_informe_ita(self, mock_request, mock_post):
        """Test para guion_062: Informe ITA"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/informe-ita
[metodo]
GET
[parametro]

[fiche-out]
/tmp/test/param_0062.txt
[json envio]
{
        "certificado": "test_cert",
        "datos":
        {
                                "regimen": "0111",
                                "ccc": "03141448363"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_request.return_value = self._mock_respuesta_api_exitosa()
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "GET")
            self.assertIn("informe-ita", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_guion_082_life_affiliate(self, mock_request, mock_post):
        """Test para guion_082: Life Affiliate"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/seg-social/life-affiliate
[metodo]
GET
[parametro]

[fiche-out]
/tmp/test/param_0082.txt
[json envio]
{
        "certificado": "test_cert",
        "datos":
        {
                "regimen": "0111",
                "ccc": "03141448363",
                "nss": "031104852782"
        }
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_request.return_value = self._mock_respuesta_api_exitosa()
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "GET")
            self.assertIn("life-affiliate", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_guion_101_copia_basica(self, mock_request, mock_post):
        """Test para guion_101_copia_basica: Copy Basic"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/sepe/copy-basic
[metodo]
POST
[parametro]

[fiche-out]
/tmp/test/param_0101.txt

[json envio]
{
	"certificado": "test_cert",
	"datos":
	{
			"validar_sin_enviar": "true",
			"cif":"B12312333",
			"docType": "D",
			"dni": "12345678A",
			"sepeId": "",
			"TIPO_FIRMA": 1,
			"startDate": "2023-11-01",
			"TEXTO_COPIABASICA": "Texto de la copia básica",
			"DOMIC_CENTRO_TRABAJO":"CENTRO DE TRABAJO",
			"duplicate": 1
	}
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_request.return_value = self._mock_respuesta_api_exitosa(
                data={"success": True, "data": {"id": "123", "file": {"content": "base64pdf"}}}
            )
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "POST")
            self.assertIn("copy-basic", client.endpoint)
            
        finally:
            os.unlink(guion_file)
    
    @patch('dsenviosaltra.requests.post')
    @patch('dsenviosaltra.requests.request')
    def test_guion_111_contrata_data(self, mock_request, mock_post):
        """Test para guion_111: Contrata Data"""
        contenido_guion = """[url]
https://api.saltra.es/api/v4/sepe/contrata/data
[metodo]
GET
[parametro]

[fiche-out]
/tmp/test/param_0111.txt

[json envio]
{
	"certificado": "test_cert",
	"datos":
	{
		"validar_sin_enviar": "true",
		"dni": "01234567A",
		"ccc":"12345678901",
		"startDate": "2025-01-01"
	}
}"""
        
        guion_file = self._crear_guion_temporal(contenido_guion)
        
        try:
            mock_post.return_value = self._mock_respuesta_api_exitosa(
                data={"data": {"access_token": self.mock_token}}
            )
            
            mock_request.return_value = self._mock_respuesta_api_exitosa()
            
            client = SaltraClient(
                self.dsClave, self.usuario, self.idUsuario,
                self.passw, guion_file, self.code_respuesta, self.tiempo_inicio
            )
            
            self.assertEqual(client.metodo, "GET")
            self.assertIn("contrata/data", client.endpoint)
            
        finally:
            os.unlink(guion_file)


if __name__ == '__main__':
    unittest.main()
