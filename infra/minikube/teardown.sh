#!/usr/bin/env bash
#
# Remove a plataforma do Minikube.
#
#   infra/minikube/teardown.sh             # remove apenas a aplicacao
#   DELETE_CLUSTER=1 ... teardown.sh       # apaga o cluster inteiro
set -euo pipefail

PROFILE="${MINIKUBE_PROFILE:-order-management}"
NAMESPACE="${NAMESPACE:-order-management}"
DELETE_CLUSTER="${DELETE_CLUSTER:-0}"

log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }

if [[ "$DELETE_CLUSTER" == "1" ]]; then
  log "Apagando o cluster '$PROFILE'..."
  minikube delete --profile "$PROFILE"
  exit 0
fi

log "Removendo o release da aplicacao..."
helm uninstall order-management --namespace "$NAMESPACE" 2>/dev/null || true

log "Removendo o namespace '$NAMESPACE'..."
# Apaga tambem o PVC do Postgres: o ambiente local comeca limpo na proxima vez.
kubectl delete namespace "$NAMESPACE" --ignore-not-found

log "Pronto. O cluster continua no ar (use DELETE_CLUSTER=1 para apaga-lo)."
