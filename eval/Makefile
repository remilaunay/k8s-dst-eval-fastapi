SHELL := /bin/bash
.DEFAULT_GOAL := help

IMAGE := docker.io/remilaunay/k8s-dst-eval-fastapi:latest
MYSQL_DATA_PATH ?= $(abspath data/mysql)
FASTAPI_APP_PATH ?= $(abspath test/app)

.PHONY: help prepare render namespace secrets pv mysql build push test-pod test-logs remove-test deploy verify archive

help: ## Affiche les commandes disponibles
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-14s %s\n", $$1, $$2}'

prepare: ## Crée les répertoires et copie les modèles de Secrets locaux
	@mkdir -p data/mysql
	@test -f mysql/mysql-root-password.env || cp mysql/mysql-root-password.env.example mysql/mysql-root-password.env
	@test -f mysql/mysql-user.env || cp mysql/mysql-user.env.example mysql/mysql-user.env
	@echo "Modèles copiés. Remplace les valeurs replace-with dans mysql/*.env avant make secrets."

render: ## Génère les manifestes hostPath depuis l’emplacement du projet
	MYSQL_DATA_PATH="$(MYSQL_DATA_PATH)" FASTAPI_APP_PATH="$(FASTAPI_APP_PATH)" python3 render-manifests.py

namespace: ## Crée ou met à jour le namespace eval
	kubectl apply -f namespace.yaml

secrets: namespace ## Crée les deux Secrets Kubernetes depuis les fichiers locaux ignorés par Git
	@test -f mysql/mysql-root-password.env || (echo "Lance make prepare puis renseigne mysql/mysql-root-password.env"; exit 1)
	@test -f mysql/mysql-user.env || (echo "Lance make prepare puis renseigne mysql/mysql-user.env"; exit 1)
	@if grep -q 'replace-with' mysql/mysql-root-password.env mysql/mysql-user.env; then echo "Remplace les valeurs de démonstration dans mysql/*.env"; exit 1; fi
	kubectl -n eval create secret generic mysql-root-password --from-env-file=mysql/mysql-root-password.env --dry-run=client -o yaml | kubectl apply -f -
	kubectl -n eval create secret generic mysql-user --from-env-file=mysql/mysql-user.env --dry-run=client -o yaml | kubectl apply -f -

pv: namespace render ## Crée le volume persistant statique MySQL
	@mkdir -p data/mysql
	kubectl apply -f mysql/mysql-local-data-folder-pv.yaml

mysql: secrets pv ## Déploie MySQL et attend le StatefulSet
	kubectl apply -f mysql/mysql-service.yaml
	kubectl apply -f mysql/mysql-statefulset.yaml
	kubectl -n eval rollout status statefulset/mysql --timeout=10m
	kubectl -n eval get pod,pvc,service -l app=mysql -o wide

build: ## Construit et tague l'image FastAPI
	docker build --pull -t $(IMAGE) test

push: build ## Publie l'image FastAPI sur Docker Hub (docker login préalable)
	docker push $(IMAGE)

test-pod: mysql push render ## Lance le pod FastAPI de test avec --reload et le montage hostPath
	kubectl apply -f test/fastapi-pod.yaml
	kubectl -n eval wait --for=condition=Ready pod/fastapi --timeout=5m

test-logs: ## Suit les logs du pod FastAPI de test
	kubectl -n eval logs -f pod/fastapi

remove-test: ## Supprime uniquement le pod de test FastAPI
	kubectl -n eval delete pod fastapi --ignore-not-found

deploy: mysql push ## Déploie les 3 replicas FastAPI et le service NodePort 30000
	kubectl apply -f fastapi/deployment.yaml
	kubectl apply -f fastapi/service.yaml
	kubectl -n eval rollout restart deployment/fastapi
	kubectl -n eval rollout status deployment/fastapi --timeout=5m
	kubectl -n eval get deployment,pods,service -l app=fastapi -o wide

verify: namespace render ## Vérifie la syntaxe et les schémas des manifestes Kubernetes côté API
	kubectl apply --dry-run=server -f namespace.yaml
	kubectl apply --dry-run=server -f mysql/mysql-local-data-folder-pv.yaml
	kubectl apply --dry-run=server -f mysql/mysql-service.yaml
	kubectl apply --dry-run=server -f mysql/mysql-statefulset.yaml
	kubectl apply --dry-run=server -f test/fastapi-pod.yaml
	kubectl apply --dry-run=server -f fastapi/deployment.yaml
	kubectl apply --dry-run=server -f fastapi/service.yaml
	python3 -m compileall -q test/app/main.py
	python3 -c 'from pathlib import Path; compile(Path("render-manifests.py").read_text(), "render-manifests.py", "exec")'

archive: render ## Crée ../eval-submission.tar.gz sans données MySQL ni fichiers de Secrets locaux
	rm -f ../eval-submission.tar.gz
	tar --exclude='eval/data/mysql/*' --exclude='eval/mysql/*.env' --exclude='eval/__pycache__' --exclude='eval/test/app/__pycache__' -czf ../eval-submission.tar.gz -C .. eval
