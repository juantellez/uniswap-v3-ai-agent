#!/bin/bash

echo "🦄 Uniswap V3 AI Agent Setup"
echo "============================"

# Verificar n8n
if ! command -v n8n &> /dev/null; then
    echo "⚠️  n8n no encontrado. Instala con:"
    echo "npm install n8n -g"
    exit 1
fi

# Crear config desde template
if [[ ! -f config.env ]]; then
    cp config.example.env config.env
    echo "✅ config.env creado desde template"
fi

echo ""
echo "📋 Próximos pasos:"
echo "1. Edita config.env con tus API keys"
echo "2. Crea Google Sheet usando examples/google-sheets-template.csv"
echo "3. Importa workflows/Uniswap-Monitor-V3.V1.json en n8n"
echo "4. Configura credenciales en n8n"
echo ""
echo "🦄 ¡Happy LPing!"
