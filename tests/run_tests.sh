#!/bin/bash
# Script para ejecutar todos los tests

echo "=========================================="
echo "Ejecutando tests para dsenviosaltra"
echo "=========================================="
echo ""

# Cambiar al directorio del proyecto
cd "$(dirname "$0")/.."

# Ejecutar tests con verbose
echo "Ejecutando tests de éxito..."
python3 -m unittest discover tests -v -p "test_guiones_exito.py"
echo ""

echo "Ejecutando tests de errores..."
python3 -m unittest discover tests -v -p "test_errores.py"
echo ""

echo "=========================================="
echo "Tests completados"
echo "=========================================="


