#!/usr/bin/env bash
# ai-process-pack installer (POSIX paridade do install.ps1).
#
# Copia o build (dist/) deste repo-mae para o layout final do consumidor:
#
#   <target>/
#     .ai-process/
#       .claude-plugin/         <- dist/.claude-plugin/
#       bin/                    <- dist/bin/
#       skills/                 <- dist/skills/
#     .agents/skills/ai-*/      <- dist/.agents/skills/ai-*/
#     .githooks/commit-msg      <- dist/templates/.githooks/commit-msg     (preserva se existe)
#     features/registry.yaml    <- dist/templates/features/registry.yaml   (preserva se existe)
#     features/lock-ignore.txt  <- dist/templates/features/lock-ignore.txt (preserva se existe)
#
# Depois roda `ai init` para semear .ai/ e FEATURES.md.
#
# Idempotente: re-rodar substitui .ai-process/ e .agents/skills/ pelo build atual,
# preserva templates ja customizados (use --force pra sobrescrever) e nao toca
# em .ai/ ja inicializada.
#
# Uso:
#   ./install.sh                      # instala no diretorio atual
#   ./install.sh --target /path       # instala num projeto especifico
#   ./install.sh --dry-run            # previa sem escrever
#   ./install.sh --force              # sobrescreve templates do consumidor
#   ./install.sh --skip-init          # nao chamar `ai init` no final

set -euo pipefail

TARGET="$(pwd)"
DRY_RUN=0
FORCE=0
SKIP_INIT=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target)
            TARGET="$2"
            shift 2
            ;;
        --target=*)
            TARGET="${1#--target=}"
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --force)
            FORCE=1
            shift
            ;;
        --skip-init)
            SKIP_INIT=1
            shift
            ;;
        -h|--help)
            sed -n '2,30p' "$0"
            exit 0
            ;;
        *)
            echo "Opcao desconhecida: $1" >&2
            exit 2
            ;;
    esac
done

REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DIST_ROOT="$REPO_ROOT/dist"

if [[ ! -d "$DIST_ROOT" ]]; then
    echo "dist/ nao encontrado em $REPO_ROOT. Rode 'python core/build/render-skills.py' antes." >&2
    exit 1
fi

# Resolve target para absoluto (mkdir -p garante que exista pra cd dentro).
mkdir -p "$TARGET"
TARGET_ROOT="$( cd "$TARGET" && pwd )"

echo ""
echo "ai-process-pack installer"
echo "  origem:  $DIST_ROOT"
echo "  destino: $TARGET_ROOT"
if [[ $DRY_RUN -eq 1 ]]; then
    echo "  modo:    DRY-RUN (nada sera escrito)"
fi
echo ""

copy_plugin_tree() {
    local source="$1"
    local destination="$2"
    local label="$3"

    if [[ ! -d "$source" ]]; then
        echo "  skip $label (origem $source nao existe)"
        return
    fi

    echo "  $label"
    echo "    $source"
    echo "      -> $destination"

    if [[ $DRY_RUN -eq 1 ]]; then
        return
    fi

    rm -rf "$destination"
    mkdir -p "$(dirname "$destination")"
    cp -R "$source" "$destination"
}

copy_template_file() {
    local source="$1"
    local destination="$2"
    local label="$3"

    if [[ ! -f "$source" ]]; then
        echo "  skip $label (origem $source nao existe)"
        return
    fi

    local verb="create"
    if [[ -e "$destination" ]]; then
        if [[ $FORCE -eq 0 ]]; then
            echo "  keep $label (ja existe em $destination; use --force para sobrescrever)"
            return
        fi
        verb="overwrite"
    fi

    echo "  $verb $label"
    echo "    $source"
    echo "      -> $destination"

    if [[ $DRY_RUN -eq 1 ]]; then
        return
    fi

    mkdir -p "$(dirname "$destination")"
    cp -f "$source" "$destination"

    # Hook do git precisa de bit executavel.
    case "$destination" in
        */.githooks/*) chmod +x "$destination" ;;
    esac
}

echo "1) Plugin Claude (.ai-process/)"
plugin_root="$TARGET_ROOT/.ai-process"
copy_plugin_tree "$DIST_ROOT/.claude-plugin" "$plugin_root/.claude-plugin" ".claude-plugin"
copy_plugin_tree "$DIST_ROOT/skills"          "$plugin_root/skills"          "skills"
copy_plugin_tree "$DIST_ROOT/bin"             "$plugin_root/bin"             "bin"

# Bit executavel para o shim POSIX e o motor.
if [[ $DRY_RUN -eq 0 ]]; then
    [[ -f "$plugin_root/bin/ai" ]]    && chmod +x "$plugin_root/bin/ai"
    [[ -f "$plugin_root/bin/ai.py" ]] && chmod +x "$plugin_root/bin/ai.py"
fi

echo ""
echo "2) Cross-tool (.agents/skills/)"
copy_plugin_tree "$DIST_ROOT/.agents/skills" "$TARGET_ROOT/.agents/skills" ".agents/skills"

echo ""
echo "3) Templates (preserva customizacao do consumidor)"
copy_template_file "$DIST_ROOT/templates/.githooks/commit-msg"    "$TARGET_ROOT/.githooks/commit-msg"     ".githooks/commit-msg"
copy_template_file "$DIST_ROOT/templates/features/registry.yaml"  "$TARGET_ROOT/features/registry.yaml"   "features/registry.yaml"
copy_template_file "$DIST_ROOT/templates/features/lock-ignore.txt" "$TARGET_ROOT/features/lock-ignore.txt" "features/lock-ignore.txt"

if [[ $SKIP_INIT -eq 1 ]]; then
    echo ""
    echo "4) ai init: SKIPPED (use sem --skip-init ou rode manualmente)"
else
    echo ""
    echo "4) ai init (semeia .ai/ e FEATURES.md)"
    engine_path="$plugin_root/bin/ai.py"
    if [[ ! -f "$engine_path" ]]; then
        echo "  skip (motor nao encontrado em $engine_path; rode manualmente apos investigar)"
    elif [[ $DRY_RUN -eq 1 ]]; then
        echo "  would run: python3 $engine_path init (cwd=$TARGET_ROOT)"
    else
        (cd "$TARGET_ROOT" && python3 "$engine_path" init) || \
            echo "  ai init retornou erro - investigue manualmente"
    fi
fi

echo ""
echo "Done."
if [[ $DRY_RUN -eq 1 ]]; then
    echo "Nada foi escrito. Re-rode sem --dry-run para aplicar."
else
    echo "Proximos passos no consumidor:"
    echo "  - Abrir o projeto em Claude Code: o plugin em .ai-process/.claude-plugin/ sera detectado."
    echo "  - Configurar githooks: git config core.hooksPath .githooks"
    echo "  - Rodar 'python3 .ai-process/bin/ai.py doctor' para verificar."
fi
