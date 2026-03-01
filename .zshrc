# Verificar antes de commit
git-safe-commit() {
    if git diff --cached --name-only | grep -E "config\.json|\.env"; then
        echo "⚠️  ATENÇÃO: Você está tentando commitar arquivos sensíveis!"
        echo "Arquivos:"
        git diff --cached --name-only | grep -E "config\.json|\.env"
        echo ""
        read -p "Tem certeza? (y/N): " confirm
        if [ "$confirm" != "y" ]; then
            echo "❌ Commit cancelado!"
            return 1
        fi
    fi
    git commit "$@"
}

alias gcommit='git-safe-commit'
//a