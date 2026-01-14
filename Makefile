# =========================
# Cluster (k3d)
# =========================
cluster-create:
	sudo k3d cluster create practica3 -a 2 -p "80:80@loadbalancer" --volume "$(PWD)/imports:/imports@all"

cluster-list:
	sudo k3d cluster list

cluster-nodes:
	sudo k3d node list

cluster-start:
	sudo k3d cluster start practica3

cluster-stop:
	sudo k3d cluster stop practica3

cluster-delete:
	sudo k3d cluster delete practica3


# =========================
# Imágenes (build + import al cluster)
# =========================
build-dev:
	sudo docker build --no-cache -f dockerfile/dev_Dockerfile -t app:dev .
	sudo k3d image import app:dev -c practica3

build-pro:
	sudo docker build --no-cache -f dockerfile/pro_Dockerfile -t app:pro .
	sudo k3d image import app:pro -c practica3


# =========================
# DEV (apply/delete/secret)
# =========================
apply-dev:
	sudo kubectl apply -f dev/dev.yaml
	sudo kubectl -n dev create secret generic dev-env --from-env-file=dev/dev.env --dry-run=client -o yaml | sudo kubectl apply -f -

delete-dev:
	sudo kubectl -n dev delete secret dev-env --ignore-not-found
	sudo kubectl delete -f dev/dev.yaml


# =========================
# PRO (apply/delete/secret)
# =========================
apply-pro:
	sudo kubectl apply -f pro/pro.yaml
	sudo kubectl -n pro create secret generic pro-env --from-env-file=pro/pro.env --dry-run=client -o yaml | sudo kubectl apply -f -

delete-pro:
	sudo kubectl -n pro delete secret pro-env --ignore-not-found
	sudo kubectl delete -f pro/pro.yaml


# =========================
# Monitoring
# =========================

monitoring-install:
	sudo kubectl apply -f monitoring/namespace.yaml
	sudo kubectl -n monitoring create secret generic grafana-admin --from-env-file=monitoring/monitoring.env --dry-run=client -o yaml | sudo kubectl apply -f -
	sudo kubectl -n monitoring create secret generic alertmanager-smtp --from-env-file=monitoring/monitoring.env --dry-run=client -o yaml | sudo kubectl apply -f -
	sudo helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
	sudo helm repo update
	sudo helm upgrade --install monitoring prometheus-community/kube-prometheus-stack -n monitoring -f monitoring/values.yaml

monitoring-dev:
	sudo kubectl apply -f monitoring/dev-monitoring/dev-servicemonitor.yaml
	sudo kubectl apply -f monitoring/dev-monitoring/dev-dashboard.yaml

monitoring-pro:
	sudo kubectl apply -f monitoring/pro-monitoring/pro-servicemonitor.yaml
	sudo kubectl apply -f monitoring/pro-monitoring/pro-dashboard.yaml

monitoring-delete:
	sudo helm uninstall monitoring -n monitoring || true
	sudo kubectl delete -f monitoring/namespace.yaml || true


# =========================
# Diagnóstico general
# =========================
nodes:
	sudo kubectl get nodes -o wide


# =========================
# Diagnóstico DEV
# =========================

pods-dev:
	sudo kubectl -n dev get pods -o wide

svc-dev:
	sudo kubectl -n dev get svc

ingress-dev:
	sudo kubectl -n dev get ingress

endpoints-dev:
	sudo kubectl -n dev get endpoints

delete-pod-dev:
	sudo kubectl -n dev delete pod $(pod)

rollout-dev:
	sudo kubectl -n dev rollout restart deployment/web

scale-web-dev:
	sudo kubectl -n dev scale deploy/web --replicas=$(n)

scale-bd-dev:
	sudo kubectl -n dev scale statefulset mysql --replicas=$(n)

logs-dev:
	@if [ -z "$(pod)" ]; then echo "Uso: make logs-dev pod=<pod>"; exit 2; fi
	sudo kubectl -n dev logs $(pod)

describe-dev:
	@if [ -z "$(pod)" ]; then echo "Uso: make describe-dev pod=<pod>"; exit 2; fi
	sudo kubectl -n dev describe pod $(pod)

events-dev:
	sudo kubectl -n dev get events --sort-by=.lastTimestamp

exec-dev:
	@if [ -z "$(pod)" ]; then echo "Uso: make exec-dev pod=<pod>"; exit 2; fi
	sudo kubectl -n dev exec -it $(pod) -- sh

crash-pod-dev:
	@if [ -z "$(pod)" ]; then echo "Uso: make crash-pod-dev pod=<pod>"; exit 2; fi
	sudo kubectl -n dev exec -it $(pod) -- sh  -c 'curl http://127.0.0.1:5000/crash'

curl-dev:
	curl -I http://app.dev.localhost/

health-dev:
	curl -s http://app.dev.localhost/health; echo




# =========================
# Diagnóstico PRO
# =========================

pods-pro:
	sudo kubectl -n pro get pods -o wide

svc-pro:
	sudo kubectl -n pro get svc

ingress-pro:
	sudo kubectl -n pro get ingress

delete-pod-pro:
	sudo kubectl -n pro delete pod $(pod)

endpoints-pro:
	sudo kubectl -n pro get endpoints

rollout-pro:
	sudo kubectl -n pro rollout restart deployment/web

scale-web-pro:
	sudo kubectl -n pro scale deploy/web --replicas=$(n)

scale-bd-pro:
	sudo kubectl -n pro scale statefulset mysql --replicas=$(n)

scale-redis-pro:
	sudo kubectl -n pro scale statefulset redis --replicas=$(n)

logs-pro:
	@if [ -z "$(pod)" ]; then echo "Uso: make logs-pro pod=<pod>"; exit 2; fi
	sudo kubectl -n pro logs $(pod)

describe-pro:
	@if [ -z "$(pod)" ]; then echo "Uso: make describe-pro pod=<pod>"; exit 2; fi
	sudo kubectl -n pro describe pod $(pod)

events-pro:
	sudo kubectl -n pro get events --sort-by=.lastTimestamp

exec-pro:
	@if [ -z "$(pod)" ]; then echo "Uso: make exec-pro pod=<pod>"; exit 2; fi
	sudo kubectl -n pro exec -it $(pod) -- sh

crash-pod-pro:
	@if [ -z "$(pod)" ]; then echo "Uso: make crash-pod-pro pod=<pod>"; exit 2; fi
	sudo kubectl -n pro exec -it $(pod) -- sh  -c 'curl http://127.0.0.1:5000/crash'


curl-pro:
	curl -I http://app.pro.localhost/

health-pro:
	curl -s http://app.pro.localhost/health; echo

# =========================
# Diagnóstico MONITORING
# =========================

pods-monitoring:
	sudo kubectl -n monitoring get pods -o wide

svc-monitoring:
	sudo kubectl -n monitoring get svc

ingress-monitoring:
	sudo kubectl -n monitoring get ingress

endpoints-monitoring:
	sudo kubectl -n monitoring get endpoints

events-monitoring:
	sudo kubectl -n monitoring get events --sort-by=.lastTimestamp

describe-monitoring:
	@if [ -z "$(pod)" ]; then echo "Uso: make describe-monitoring pod=<pod>"; exit 2; fi
	sudo kubectl -n monitoring describe pod $(pod)

logs-monitoring:
	@if [ -z "$(pod)" ]; then echo "Uso: make logs-monitoring pod=<pod>"; exit 2; fi
	sudo kubectl -n monitoring logs $(pod)

exec-monitoring:
	@if [ -z "$(pod)" ]; then echo "Uso: make exec-monitoring pod=<pod>"; exit 2; fi
	sudo kubectl -n monitoring exec -it $(pod) -- sh
pf-prom:
	sudo kubectl -n monitoring port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090

pf-alertmanager:
	sudo kubectl -n monitoring port-forward svc/monitoring-kube-prometheus-alertmanager 9093:9093


# =========================
# Tests locales (tu script)
# =========================
test-local-dev:
	./test/local/test-web.py dev http://app.dev.localhost

test-local-pro:
	./test/local/test-web.py pro http://app.pro.localhost

# =========================
# Deploy simulado completo
# =========================
deploy-simulated-all:
	@echo "=== Deploy del proyecto ==="
	@echo "-1 Requisitos:"
	@echo " 	Configurar:"
	@echo "   	- /etc/hosts: 127.0.0.1 app.dev.localhost"
	@echo "   	- /etc/hosts: 127.0.0.1 app.pro.localhost"
	@echo "   	- /etc/hosts: 127.0.0.1 monitoring.localhost"
	@echo "   	- Crear archivos dev/dev.env, pro/pro.env y monitoring/monitoring.env con las variables de entorno necesarias"
	@echo ""
	@echo "-2 Creat el cluster:"
	@echo "   make cluster-create"
	@echo ""
	@echo "-3 Crear e importar las imágenes:"
	@echo "   make build-dev"
	@echo "   make build-pro"
	@echo ""
	@echo "-4 Deploy de los entornos:"
	@echo "   make apply-dev"
	@echo "   make apply-pro"
	@echo ""
	@echo "-5 Deploy del monitoring:"
	@echo "   make monitoring-install"
	@echo "   make monitoring-dev"
	@echo "   make monitoring-pro"
	@echo ""
	@echo "-6 Checks:"
	@echo "   make health-dev"
	@echo "   make health-pro"
	@echo ""
	@echo "-7 Help:"
	@echo "   make help"
	@echo ""


# =========================
# Ayuda
# =========================
help:
	@echo ""
	@echo "Comandos disponibles:"
	@echo ""
	@echo "Cluster:"
	@echo "  make cluster-create              - Crea el cluster practica3 (2 agents), LB en puerto :80 y monta ./imports en /imports"
	@echo "  make cluster-list                - Lista clusters"
	@echo "  make cluster-nodes               - Lista nodos del cluster"
	@echo "  make cluster-start               - Inicia cluster"
	@echo "  make cluster-stop                - Para cluster"
	@echo "  make cluster-delete              - Borra cluster"
	@echo ""
	@echo "Build y import:"
	@echo "  make build-dev                   - Build app:dev y import al cluster"
	@echo "  make build-pro                   - Build app:pro y import al cluster"
	@echo ""
	@echo "Deploy por entorno:"
	@echo "  make apply-dev                   - Aplica manifests DEV y crea el secret dev-env"
	@echo "  make delete-dev                  - Elimina recursos DEV"
	@echo "  make apply-pro                   - Aplica manifests PRO y crea el secret pro-env"
	@echo "  make delete-pro                  - Elimina recursos PRO"
	@echo ""
	@echo "Monitoring:"
	@echo "  make monitoring-install          - Crea con helm el namespace y secrets y despliega el stack de monitoring"
	@echo "  make monitoring-dev              - Aplica ServiceMonitor+Dashboard para DEV"
	@echo "  make monitoring-pro              - Aplica ServiceMonitor+Dashboard para PRO"
	@echo "  make monitoring-delete           - Desinstala el stack de monitoring y borra el namespace"
	@echo ""
	@echo "Diagnostico general:"
	@echo "  make nodes                       - Lista nodos del cluster con IP y roles"
	@echo ""
	@echo "Diagnostico DEV:"
	@echo "  make pods-dev                    - Lista pods DEV"
	@echo "  make svc-dev                     - Lista Services DEV"
	@echo "  make ingress-dev                 - Lista Ingress DEV"
	@echo "  make endpoints-dev               - Lista Endpoints DEV"
	@echo "  make delete-pod-dev pod=<pod>    - Elimina un pod DEV"
	@echo "  make rollout-dev                 - Reinicia deployment/web DEV para forzar nueva imagen"
	@echo "  make scale-web-dev n=<num>       - Escala web en DEV"
	@echo "  make scale-bd-dev  n=<num>       - Escala mysql en DEV"
	@echo "  make logs-dev pod=<pod>          - Muestra logs de un pod DEV"
	@echo "  make describe-dev pod=<pod>      - Describe un pod DEV"
	@echo "  make events-dev                  - Muestra eventos del namespace dev"
	@echo "  make exec-dev pod=<pod>          - Entra en un pod DEV por sh"
	@echo "  make crash-pod-dev pod=<pod>     - Provoca crash en un pod DEV"
	@echo "  make curl-dev                    - Curl al host app.dev.localhost"
	@echo "  make health-dev                  - GET /health en DEV"
	@echo ""
	@echo "Diagnostico PRO:"
	@echo "  make pods-pro                    - Lista pods PRO"
	@echo "  make svc-pro                     - Lista Services PRO"
	@echo "  make ingress-pro                 - Lista Ingress PRO"
	@echo "  make endpoints-pro               - Lista Endpoints PRO"
	@echo "  make delete-pod-pro pod=<pod>    - Elimina un pod PRO"
	@echo "  make rollout-pro                 - Reinicia deployment/web PRO para forzar nueva imagen"
	@echo "  make scale-web-pro  n=<num>      - Escala web en PRO"
	@echo "  make scale-bd-pro   n=<num>      - Escala mysql en PRO"
	@echo "  make scale-redis-pro n=<num>     - Escala redis en PRO"
	@echo "  make logs-pro pod=<pod>          - Muestra logs de un pod PRO"
	@echo "  make describe-pro pod=<pod>      - Describe un pod PRO"
	@echo "  make events-pro                  - Muestra eventos del namespace pro"
	@echo "  make exec-pro pod=<pod>          - Entra en un pod PRO por sh"
	@echo "  make crash-pod-pro pod=<pod>     - Provoca crash en un pod PRO"
	@echo "  make curl-pro                    - Curl al host app.pro.localhost"
	@echo "  make health-pro                  - GET /health en PRO"
	@echo ""
	@echo "Diagnóstico MONITORING:"
	@echo "  make pods-monitoring             - Lista pods de monitoring"
	@echo "  make svc-monitoring              - Lista servicios de monitoring"
	@echo "  make ingress-monitoring          - Lista ingress de monitoring"
	@echo "  make endpoints-monitoring        - Lista endpoints de monitoring"
	@echo "  make events-monitoring           - Lista eventos del namespace monitoring"
	@echo "  make logs-monitoring pod=<pod>   - Logs de un pod de monitoring"
	@echo "  make describe-monitoring pod=<pod> - Describe un pod de monitoring"
	@echo "  make exec-monitoring pod=<pod>   - Entra en un pod de monitoring sh"
	@echo "  make pf-prom                     - Port-forward Prometheus a localhost:9090"
	@echo "  make pf-alertmanager             - Port-forward Alertmanager a localhost:9093"
	@echo ""
	@echo "Tests locales:"
	@echo "  make test-local-dev              - Ejecuta tests locales contra app.dev.localhost"
	@echo "  make test-local-pro              - Ejecuta tests locales contra app.pro.localhost"
	@echo ""