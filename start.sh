#!/bin/bash

# Criar diretórios necessários
mkdir -p data

# Criar arquivos JSON vazios se não existirem
for file in tickets.json warnings.json blacklist.json prefixes.json; do
    if [ ! -f "data/$file" ]; then
        echo '{}' > "data/$file"
    fi
done

# Debug info
echo "🐍 Python version: $(python --version)"
echo "📦 Pip version: $(pip --version)"
echo "🔑 Checking environment variables..."
echo "   BOT_PREFIX: ${BOT_PREFIX:-not set}"
echo "   OWNER_IDS: ${OWNER_IDS:-not set}"
echo "   PORT: ${PORT:-not set}"

# Iniciar bot
echo "🚀 Starting bot..."
exec python main.py