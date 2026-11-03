# Évaluation Kubernetes : MySQL et FastAPI

Ce dossier contient le rendu de l’examen : un StatefulSet MySQL 8.4 avec stockage persistant local, un pod de test FastAPI avec `--reload`, puis un Deployment FastAPI de trois replicas exposé par un NodePort.

## Prérequis

- Un cluster Kubernetes accessible avec `kubectl`, un StorageClass `local-path` et un NodePort libre.
- Docker Engine démarré et un compte Docker Hub public nommé `remilaunay`.
- `make`, `curl` et Python 3.

Les manifestes de stockage et de montage de code utilisent les chemins de cette VM : `/home/ubuntu/eval/eval/data/mysql` et `/home/ubuntu/eval/eval/test/app`. Si le dossier est déplacé, modifie ces deux chemins absolus dans les manifestes correspondants.

## Préparation de la VM

Le cache de paquets UV occupait 3,0 Gio ; il a été vidé avant le déploiement. Pour ne laisser tourner que les workloads nécessaires à l’examen, les Deployments, StatefulSets et ReplicaSets applicatifs des namespaces `airflow`, `datascientest`, `default` et `sales` ont été mis à zéro. Leurs manifestes et PVC sont conservés ; aucun volume de données n’a été supprimé. Les composants système K3s, MySQL et FastAPI restent actifs.

## Configuration locale

Depuis le dossier `eval` :

```bash
make prepare
```

Remplace les valeurs `replace-with-...` dans `mysql/mysql-root-password.env` et `mysql/mysql-user.env`. Ces deux fichiers contiennent des secrets locaux, sont ignorés par Git et ne sont pas inclus dans l’archive de rendu. Les fichiers `.env.example` suivis par Git ne contiennent que des exemples.

Connecte Docker au compte avant la publication :

```bash
docker login
```

## Étapes de déploiement

1. Crée les Secrets Kubernetes, le namespace, le PV et le stockage MySQL ; attends que le StatefulSet soit prêt :

   ```bash
   make mysql
   kubectl -n eval get pod,pvc,service -o wide
   ```

   Le service `mysql` utilise l’IP `10.43.0.42`, reçoit sur le port `3307` et transmet au port MySQL `3306`. Le StatefulSet génère le PVC `mysql-data-mysql-0`, prélié au PV statique `mysql-local-data-folder-pv` de 2 Gio.

2. Construis et publie l’image publique `docker.io/remilaunay/k8s-dst-eval-fastapi:latest`, puis lance le pod de test monté sur le code local :

   ```bash
   make test-pod
   make test-logs
   ```

   Modifie `test/app/main.py` au besoin. Le montage `hostPath` et `uvicorn --reload` rendent les changements visibles dans le pod. Les logs indiquent l’hôte, le port, la base et l’utilisateur ; le mot de passe est masqué.

3. Après validation, retire le pod de test, reconstruis et republie l’image modifiée, puis déploie les trois replicas :

   ```bash
   make remove-test
   make push
   make deploy
   ```

   Le Deployment utilise l’image publiée, les variables du Secret `mysql-user` et n’active pas `--reload`. Le service NodePort expose l’application sur le port 30000 du nœud.

   **Conflit de port rencontré sur cette VM :** `default/monservicenodeport` utilisait déjà le NodePort 30000. Son NodePort a été déplacé à 32000 pour respecter la consigne ; le service reste défini dans le cluster.

## Vérification et utilisation

Vérifie les ressources, les logs et la disponibilité de l’API :

```bash
make verify
kubectl -n eval get all,pvc
kubectl -n eval logs deployment/fastapi
curl http://<IP_DU_NOEUD>:30000/health
curl http://<IP_DU_NOEUD>:30000/tables
```

L’endpoint `PUT /table` crée une table. Exemple :

```bash
curl -X PUT http://<IP_DU_NOEUD>:30000/table \
  -H 'Content-Type: application/json' \
  -d '{"table_name":"exam_result","columns":{"id":"Integer","label":"String(100)"}}'
```

Types pris en charge : `Integer`, `String`, `String(n)`, `Text`, `Boolean`, `Float`, `Date` et `DateTime`. Les types et identifiants sont validés ; le code n’évalue pas les chaînes reçues comme du Python.

Pour un accès local lorsque le NodePort n’est pas joignable depuis le poste :

```bash
kubectl -n eval port-forward service/fastapi 8000:8000
```

Puis appelle `http://127.0.0.1:8000/health`.

## Structure du rendu

```text
eval/
├── data/mysql/                 # Répertoire hôte du PV (données non archivées)
├── fastapi/
│   ├── deployment.yaml         # Deployment de 3 replicas
│   └── service.yaml            # NodePort 30000
├── mysql/
│   ├── mysql-local-data-folder-pv.yaml
│   ├── mysql-service.yaml      # ClusterIP 10.43.0.42:3307 et service headless
│   ├── mysql-statefulset.yaml  # MySQL 8.4, 1 replica, PVC de 2 Gio
│   └── *.env.example           # Modèles locaux des deux Secrets
├── test/
│   ├── app/main.py             # API FastAPI reliée à MySQL
│   ├── Dockerfile
│   ├── fastapi-pod.yaml        # Pod de test avec --reload
│   └── requirements.txt
├── namespace.yaml
├── Makefile
└── README.md
```

Le rendu final demandé peut être produit avec `make archive`. L’archive `../eval-submission.tar.gz` exclut les données MySQL et les deux fichiers locaux de Secrets.
