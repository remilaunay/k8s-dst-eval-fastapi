9. Conclusion et évaluation
9.1. Conclusion
Dans ce cours, nous avons pu voir l'intérêt d'une plateforme comme Kubernetes. Nous avons pu voir l'architecture et différents objets qui constituent l'utilisation de Kubernetes. Nous avons enfin vu comment déployer des applications avec Kubernetes.

Kubernetes, étant un outil très complexe, nous n'avons pas abordé tous les éléments qui le composent, ni les aspects de sécurité ou même de persistance des données. On aurait aussi pu parler longuement de l'articulation de Kubernetes avec les hébergeurs de Cloud.

9.2. Évaluation
Vous allez déployer le SGBD MySQL à l'aide d'un StatefulSet, exposer le pod à l'aide d'un service afin de connecter 3 pods, déployés à l'aide d'un Deployment, dans lesquels tournent une application FastAPI.

Veuillez suivre scrupuleusement les consignes afin de délivrer votre évaluation dans le format attendu. Si le format n'est pas respecté, nous nous verrons obliger de refuser votre rendu.
Mise en place de l'architecture
Créez un dossier nommé eval.

Dans le dossier eval, créez 4 dossiers : data, fastapi, mysql et test.

Créez un namespace nommé eval et travaillez dedans.

Mise en place du SGBD
Exécutez les instructions suivantes à partir du dossier eval/mysql.

Créez un StatefulSet déployant un replica dans lequel se trouve un conteneur créé à partir de l'image docker.io/mysql:8.4.

Créez 2 secrets :
- mysql-root-password : Définissez le mot de passe de l'utilisateur root.
- mysql-user : Définissez le nom d'un utilisateur et son mot de passe, ainsi que le nom de la base de données sur laquelle cet utilisateur aura tous les droits. Je vous invite à consulter la documentation de l'image Docker officielle de MySQL.

Créez un PV dans un fichier nommé mysql-local-data-folder-pv.yaml avec le contenu suivant et complétez-le :

apiVersion: v1
kind: PersistentVolume
metadata:
  name:
spec:
  storageClassName: local-path
  capacity:
    storage: 2Gi
  accessModes:
    - ReadWriteOnce
  claimRef:
     namespace:
     name:
  hostPath:
    path:
Revenez sur votre StatefulSet et ajoutez les variables d'environnements à votre conteneur.
Ajoutez ensuite un template de PVC à l'aide de l'instruction volumeClaimTemplates. Pensez à regarder le nom du PVC généré lors du déploiement de votre StatefulSet afin de le faire correspondre au spec.claimRef.name de votre PV.

Créez un service afin d'exposer votre SGBD via l'adresse IP 10.43.0.42 sur le port 3307. Le port qu'utilise le SGBD MySQL est le 3306.

Déployez votre StatefulSet et le service.

Développement de votre application FastAPI
Exécutez les instructions suivantes à partir du dossier eval/test. Vous allez devoir mettre à jour le script de votre application FastAPI afin de la faire communiquer avec votre SGBD MySQL.

Téléchargez le fichier .tar suivant à l'aide d'un wget : https://dst-de.s3.eu-west-3.amazonaws.com/kubernetes_fr/eval/k8s-eval-fastapi.tar.

Vous trouverez 1 dossier et 3 fichiers :

app/ : Ce dossier contient le fichier main.py, le code source de votre application FastAPI.
Dockerfile : Ce fichier correspond à la recette de votre image.
fastapi-pod.yaml : Ce manifeste YAML déploie un pod dans lequel tourne votre conteneur instanciant votre application FastAPI.
requirements.txt : Ce fichier répertorie les dépendances Python de votre application FastAPI.
Depuis Docker Hub, créez un répertoire publique nommé k8s-dst-eval-fastapi. ("dst" pour "datascientest")
Construisez votre image et faites un push de celle-ci vers votre répertoire sur Docker Hub.

Configurez le fichier fastapi-pod.yaml et ajoutez :
- l'image de votre répertoire sur Docker Hub ;
- les variables du secret mysql-user ;
- un volume de type hostPath entre le dossier eval/test/app de votre machine vers le dossier /app de votre conteneur.

Pour cette partie, vous devez obligatoirement lancer le service exposant votre SGBD MySQL.
Vous pouvez maintenant lancer votre pod. Les modifications du fichier eval/test/app/main.py seront prises en compte grâce au volume et l'option --reload de la commande uvicorn.

Observez les logs, en particulier l'affichage des variables d'environnement, du conteneur de votre pod à l'aide de la commande kubectl logs -f fastapi.
Modifiez le fichier main.py afin de vous connecter à votre SGBD. Vous devez utiliser la librairie os pour extraire les variables d'environnement qui vous intéressent.

Une fois le fichier main.py, reconstruisez votre image et refaites un push vers votre répertoire k8s-dst-eval-fastapi.

Mise en place de l'application FastAPI
Créez un Deployment avec 3 replicas. Utilisez la dernière version de votre image pour créé votre conteneur. N'oubliez pas l'ajout des variables d'environnement du secret mysql-user et retirez l'option --reload de la commande uvicorn. Créez un service exposant votre Deployment à l'extérieur de votre cluster Kubernetes via le port 30000.

C'est la fin de l'évaluation, veuillez rendre une archive zip ou tar de votre dossier eval.

N'oubliez pas d'uploader votre examen, dans l'onglet Mes Exams, après avoir validé tous les exercices du module.

Bon courage !