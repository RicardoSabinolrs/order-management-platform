#!/usr/bin/env bash
#
# Sobe a plataforma inteira em um Minikube local.
#
#   infra/minikube/bootstrap.sh              # cluster + postgres + aplicacao
#   WITH_OBSERVABILITY=1 ... bootstrap.sh    # inclui Prometheus, Grafana e Loki
#
# As imagens sao construidas dentro do daemon do proprio Minikube, entao nao ha
# registro envolvido e nada precisa ser publicado.
set -euo pipefail

PROFILE="${MINIKUBE_PROFILE:-order-management}"
NAMESPACE="${NAMESPACE:-order-management}"
IMAGE_TAG="${IMAGE_TAG:-local}"
CPUS="${MINIKUBE_CPUS:-4}"
MEMORY="${MINIKUBE_MEMORY:-6144}"
WITH_OBSERVABILITY="${WITH_OBSERVABILITY:-0}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHART_DIR="$REPO_ROOT/infra/helm/order-management"

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31mxx\033[0m %s\n' "$*" >&2; exit 1; }

# --------------------------------------------------------------------------
# Pre-requisitos
# --------------------------------------------------------------------------
for binary in minikube kubectl helm docker; do
  command -v "$binary" >/dev/null 2>&1 || die "'$binary' nao encontrado. Instale com: brew install $binary"
done
docker info >/dev/null 2>&1 || die "O daemon do Docker nao esta rodando. Inicie o Docker Desktop e tente de novo."

# --------------------------------------------------------------------------
# Cluster
# --------------------------------------------------------------------------
if minikube status --profile "$PROFILE" >/dev/null 2>&1; then
  log "Cluster '$PROFILE' ja esta no ar."
else
  log "Criando o cluster '$PROFILE' (${CPUS} CPUs, ${MEMORY}MB)..."
  minikube start --profile "$PROFILE" --cpus "$CPUS" --memory "$MEMORY" --driver docker
fi

log "Habilitando addons (ingress, metrics-server, storage)..."
minikube addons enable ingress        --profile "$PROFILE" >/dev/null
minikube addons enable metrics-server --profile "$PROFILE" >/dev/null
minikube addons enable storage-provisioner --profile "$PROFILE" >/dev/null

kubectl config use-context "$PROFILE" >/dev/null

# --------------------------------------------------------------------------
# Imagens, construidas dentro do Minikube
# --------------------------------------------------------------------------
log "Apontando o Docker para o daemon do Minikube..."
eval "$(minikube -p "$PROFILE" docker-env)"

log "Construindo order-management-api:$IMAGE_TAG..."
docker build -t "order-management-api:$IMAGE_TAG" "$REPO_ROOT/apps/api"

log "Construindo order-management-web:$IMAGE_TAG..."
docker build -t "order-management-web:$IMAGE_TAG" -f "$REPO_ROOT/apps/web/Dockerfile" "$REPO_ROOT"

# --------------------------------------------------------------------------
# Namespace e banco
# --------------------------------------------------------------------------
log "Preparando o namespace '$NAMESPACE'..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f - >/dev/null

log "Aplicando o Postgres..."
kubectl apply -n "$NAMESPACE" -f "$REPO_ROOT/infra/minikube/postgres.yaml"
kubectl rollout status statefulset/postgres -n "$NAMESPACE" --timeout=300s

# --------------------------------------------------------------------------
# Observabilidade (opcional)
# --------------------------------------------------------------------------
SERVICE_MONITOR_ENABLED=false
if [[ "$WITH_OBSERVABILITY" == "1" ]]; then
  log "Instalando a stack de observabilidade..."
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
  helm repo add grafana https://grafana.github.io/helm-charts >/dev/null
  helm repo update >/dev/null

  helm upgrade --install kube-prometheus prometheus-community/kube-prometheus-stack \
    --namespace observability --create-namespace \
    --set grafana.adminPassword=admin \
    --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
    --wait --timeout 10m

  helm upgrade --install loki grafana/loki-stack \
    --namespace observability \
    --set promtail.enabled=true \
    --wait --timeout 10m

  SERVICE_MONITOR_ENABLED=true
fi

# --------------------------------------------------------------------------
# Aplicacao
# --------------------------------------------------------------------------
log "Instalando o chart da aplicacao..."
helm upgrade --install order-management "$CHART_DIR" \
  --namespace "$NAMESPACE" \
  --values "$CHART_DIR/values.yaml" \
  --values "$CHART_DIR/values-local.yaml" \
  --set "image.tag=$IMAGE_TAG" \
  --set "serviceMonitor.enabled=$SERVICE_MONITOR_ENABLED" \
  --wait --timeout 10m

# --------------------------------------------------------------------------
# Acesso
# --------------------------------------------------------------------------
CLUSTER_IP="$(minikube ip --profile "$PROFILE")"
HOSTNAME="order-management.local"

echo
log "Plataforma no ar."
echo
if ! grep -q "$HOSTNAME" /etc/hosts 2>/dev/null; then
  warn "Falta mapear o host. Rode uma vez:"
  echo "    echo '$CLUSTER_IP  $HOSTNAME' | sudo tee -a /etc/hosts"
  echo
fi
echo "  Aplicacao : http://$HOSTNAME"
echo "  API       : http://$HOSTNAME/api/v1  (health em /health/live)"
if [[ "$WITH_OBSERVABILITY" == "1" ]]; then
  echo "  Grafana   : kubectl -n observability port-forward svc/kube-prometheus-grafana 3000:80"
  echo "              usuario admin / senha admin"
fi
echo
echo "  kubectl -n $NAMESPACE get pods"
echo "  kubectl -n $NAMESPACE logs -l app.kubernetes.io/component=api -f"
