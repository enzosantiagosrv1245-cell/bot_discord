cat > start.sh << 'EOF'
#!/bin/bash

# Criar diretórios necessários
mkdir -p data

# Criar arquivos JSON se não existirem
for file in tickets.json warnings.json blacklist.json prefixes.json; do
    if [ ! -f "data/$file" ]; then
        echo "{}" > "data/$file"
    fi
done

# Iniciar o bot
python main.py
EOF

# Dar permissão de execução
chmod +x start.sh