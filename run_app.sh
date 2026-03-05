#!/bin/bash
# Script para cargar variables de entorno y ejecutar la aplicación

# Cargar variables desde .env si existe
if [ -f .env ]; then
    echo "📋 Cargando configuración desde .env..."
    export $(grep -v '^#' .env | xargs)
    echo "✅ Variables de entorno cargadas"
else
    echo "⚠️  Archivo .env no encontrado"
    echo "Copia .env.example a .env y configura tu OPENAI_API_KEY"
    exit 1
fi

# Verificar si OPENAI_API_KEY está configurada
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-key-here" ]; then
    echo "⚠️  OPENAI_API_KEY no configurada"
    echo "Edita .env y agrega tu clave de OpenAI"
    echo "Sistema usará fallback local de reglas"
fi

# Ejecutar la aplicación
echo "🚀 Iniciando Structural Health Engine..."
streamlit run engine/app.py --server.port 8501 --server.headless true
