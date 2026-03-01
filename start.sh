#!/bin/bash

# Criar diretórios
mkdir -p data

# Criar arquivos JSON vazios
echo '{}' > data/tickets.json
echo '{}' > data/warnings.json
echo '{}' > data/blacklist.json
echo '{}' > data/prefixes.json

# Mostrar info de debug
echo "📦 Python version:"
python --version

echo "📦 Installed packages:"
pip list

echo "🔑 Environment variables (sem mostrar token):"
env | grep -v TOKEN

echo "🚀 Starting bot..."
python main.py