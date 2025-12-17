# Tests para dsenviosaltra

Este directorio contiene los tests para verificar el correcto funcionamiento del sistema dsenviosaltra.

## Estructura de Tests

### test_guiones_exito.py
Contiene tests individuales para cada guion, verificando que funcionan correctamente:

**Guiones de certificados:**
- `test_guion_subir_certificado`: Test para subir certificado
- `test_guion_obtener_certificados`: Test para obtener listado de certificados
- `test_guion_borrar_certificado`: Test para borrar certificado

**Guiones de clientes:**
- `test_guion_subir_clientes`: Test para subir cliente
- `test_guion_listado_clientes`: Test para listar clientes
- `test_guion_desactivar_cliente`: Test para desactivar cliente
- `test_guion_borrar_clientes`: Test para borrar cliente

**Guiones de Seguridad Social:**
- `test_guion_01_alta_seg_social`: Test para alta en Seguridad Social
- `test_guion_02_baja_seg_social`: Test para baja en Seguridad Social
- `test_guion_04_contract_coeficiente`: Test para Contract Coeficiente
- `test_guion_05_employee_situations`: Test para Employee Situations
- `test_guion_06_report_situation_ccc`: Test para Report Situation CCC
- `test_guion_07_nss_by_ipf`: Test para NSS by IPF
- `test_guion_08_duplicate_ta`: Test para Duplicate TA
- `test_guion_012_idc_info`: Test para IDC Info for NSS
- `test_guion_013_employees_enterprise`: Test para Employees in Enterprise
- `test_guion_020_category_professional`: Test para Category Professional
- `test_guion_028_occupation`: Test para Occupation
- `test_guion_062_informe_ita`: Test para Informe ITA
- `test_guion_081_life_ccc`: Test para Life CCC
- `test_guion_082_life_affiliate`: Test para Life Affiliate

**Guiones de SEPE:**
- `test_guion_101_contrata`: Test para contratos con XML
- `test_guion_101_copia_basica`: Test para Copy Basic
- `test_guion_104_llamamientos`: Test para llamamientos
- `test_guion_111_contrata_data`: Test para Contrata Data

### test_errores.py
Contiene tests para forzar y verificar el manejo de errores:
- `test_error_guion_no_existe`: Error cuando el archivo guion no existe
- `test_error_json_invalido_en_guion`: Error cuando el JSON en el guion es inválido
- `test_error_credenciales_incorrectas`: Error cuando las credenciales son incorrectas
- `test_error_respuesta_api_400`: Error cuando la API devuelve 400 Bad Request
- `test_error_respuesta_api_500`: Error cuando la API devuelve 500 Internal Server Error
- `test_error_certificado_faltante`: Error cuando falta el certificado en el JSON
- `test_error_certificado_base64_invalido`: Error cuando el certificado Base64 es inválido
- `test_error_metodo_no_soportado_certificado`: Error cuando se usa método no soportado
- `test_error_metodo_no_soportado_cliente`: Error cuando se usa método no soportado
- `test_error_xml_no_existe`: Error cuando el archivo XML no existe
- `test_error_datos_string_no_json`: Error cuando el campo 'datos' no es JSON válido
- `test_error_cliente_json_invalido`: Error cuando el JSON de cliente es inválido
- `test_error_borrar_cliente_sin_parametro`: Error al borrar cliente sin parámetro
- `test_error_timeout_conexion`: Error cuando hay timeout en la conexión
- `test_error_cond_desempleado_invalido`: Error cuando cond_desempleado es inválido

## Ejecutar los Tests

### Ejecutar todos los tests
```bash
python3 -m unittest discover tests
```

### Ejecutar solo los tests de éxito
```bash
python3 -m unittest tests.test_guiones_exito
```

### Ejecutar solo los tests de errores
```bash
python3 -m unittest tests.test_errores
```

### Ejecutar un test específico
```bash
python3 -m unittest tests.test_guiones_exito.TestGuionesExito.test_guion_01_alta_seg_social
```

### Ejecutar con verbose (más información)
```bash
python3 -m unittest discover tests -v
```

### Usar el script proporcionado
```bash
./tests/run_tests.sh
```

## Notas Importantes

1. **Los tests usan mocks**: Los tests no realizan llamadas reales a la API. Utilizan `unittest.mock` para simular las respuestas de la API.

2. **Archivos temporales**: Los tests crean archivos temporales que se eliminan automáticamente después de cada test.

3. **No se modifican archivos reales**: Los tests no modifican los guiones originales ni crean archivos de salida permanentes.

4. **Cobertura**: Los tests cubren:
   - Todos los tipos de guiones (certificados, clientes, query_avanza)
   - Todos los métodos HTTP (GET, POST, PUT, DELETE)
   - Manejo de errores comunes
   - Validación de JSON
   - Procesamiento de XML

## Requisitos

Los tests requieren las siguientes dependencias (que ya deberían estar instaladas):
- `unittest` (incluido en Python estándar)
- `unittest.mock` (incluido en Python 3.3+)
- `requests` (para las llamadas HTTP simuladas)

## Agregar Nuevos Tests

Para agregar un nuevo test:

1. Si es un test de éxito para un nuevo guion, agregarlo en `test_guiones_exito.py`
2. Si es un test de error, agregarlo en `test_errores.py`
3. Seguir el patrón de los tests existentes
4. Asegurarse de limpiar archivos temporales en el bloque `finally`




