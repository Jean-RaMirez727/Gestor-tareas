#!/usr/bin/env bash
# Copia a la rama actual SOLO los archivos que le corresponden a un integrante.
# No hace commit: cada integrante revisa y confirma con su propia identidad de git.
#
# Uso (desde la raíz de tu clon, ya sobre `develop`):
#   scripts/ramas.sh a  /ruta/al/proyecto_completo     # Integrante A - dominio
#   scripts/ramas.sh b  /ruta/al/proyecto_completo     # Integrante B - persistencia y shell
#   scripts/ramas.sh c  /ruta/al/proyecto_completo     # Integrante C - consultas e interfaz
set -euo pipefail

ROL="${1:?Indica a, b o c}"
ORIGEN="${2:?Indica la ruta del proyecto completo}"

case "$ROL" in
  a) RAMA="feature/dominio-core"
     ARCHIVOS=(gestor/core.py tests/test_core.py tests/test_architecture.py) ;;
  b) RAMA="feature/persistencia-shell"
     ARCHIVOS=(gestor/decorators.py gestor/db.py main.py tests/test_db.py tests/test_decorators.py) ;;
  c) RAMA="feature/consultas-ui"
     ARCHIVOS=(gestor/queries.py gestor/ui.py tests/test_queries.py) ;;
  *) echo "Rol inválido: usa a, b o c" >&2; exit 1 ;;
esac

git checkout -b "$RAMA"
for f in "${ARCHIVOS[@]}"; do
  mkdir -p "$(dirname "$f")"
  cp "$ORIGEN/$f" "$f"
done
git add "${ARCHIVOS[@]}"
echo "Rama $RAMA lista con ${#ARCHIVOS[@]} archivos en staging. Revísalos, entiende cada línea y haz commit."
