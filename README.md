# Script de collecte d'informations système et envoi SFTP sécurisé

## Description
Ce projet propose un script Python multiplateforme (Windows et Linux) qui collecte discrètement plusieurs informations sur la machine locale, génère un rapport temporaire, puis l'envoie de manière sécurisée vers un serveur distant via SFTP. Le script est conçu pour s'exécuter en **mode silencieux**, c'est-à-dire sans aucune sortie visible à l'écran, afin de pouvoir fonctionner en arrière-plan.

## Fonctionnement du script
Le script effectue les étapes suivantes :
1. **Collecte d'informations système** : Récupération du nom de machine (*hostname*), de l'utilisateur courant, des adresses IP assignées, de la liste des processus en cours, des informations sur les disques (taille totale et espace libre), de la quantité de mémoire RAM et de la liste des logiciels installés sur la machine.
2. **Génération d'un rapport** : Les données collectées sont formatées et écrites dans un fichier texte temporaire (par exemple `rapport_systeme.txt`) stocké dans le répertoire temporaire de l'OS (comme `%TEMP%` sous Windows ou `/tmp` sous Linux).
3. **Transfert SFTP sécurisé** : Le fichier de rapport est ensuite transmis au serveur SFTP spécifié. La connexion s'effectue de manière sécurisée en utilisant SSH (port 22 par défaut) avec vérification de l'identité du serveur (voir section Sécurité ci-dessous).
4. **Nettoyage** : Une fois le fichier envoyé avec succès, le fichier temporaire local est supprimé du système pour ne laisser aucune trace.

## Paramètres SFTP à configurer
Certains paramètres doivent être ajustés dans le script avant son exécution afin de correspondre à votre environnement :
- **SFTP_HOST** : le nom d'hôte ou l'adresse IP du serveur SFTP de destination.
- **SFTP_PORT** : le port TCP du service SFTP (22 par défaut pour SSH).
- **SFTP_USERNAME** : le nom d'utilisateur pour la connexion au serveur SFTP.
- **SFTP_PASSWORD** : le mot de passe de l'utilisateur SFTP.
- **REMOTE_PATH** : le chemin complet (sur le serveur) où le fichier de rapport doit être déposé. Par exemple, `/home/user/rapports/rapport_systeme.txt`.

Ces informations d'identification et de configuration sont stockées en tête de script dans des variables faciles à repérer et à modifier. **Important** : évitez de laisser ces informations sensibles (comme le mot de passe) dans le dépôt GitHub public. Vous pouvez utiliser un fichier de configuration séparé ou des variables d'environnement pour plus de sécurité si nécessaire.

## Sécurité SSH renforcée (vérification de la clé du serveur)
Ce script intègre une mesure de sécurité supplémentaire pour prévenir les attaques de type **Man-in-the-Middle (MITM)** lors de la connexion SFTP. Avant d'envoyer le mot de passe ou le fichier, il vérifie que la clé publique du serveur SFTP correspond à celle attendue.

- **Clé publique connue à l'avance** : Il est supposé que l'empreinte (empreinte numérique, hash) de la clé publique du serveur est connue et codée en dur dans le script (variable `EXPECTED_HOSTKEY_FINGERPRINT`). Cette empreinte est au format SHA-256 (format par défaut d'OpenSSH), généralement représentée sous forme Base64 (une chaîne de caractères).
- **Comparaison d'empreinte** : Lors de la connexion, le script récupère la clé publique présentée par le serveur et calcule son empreinte SHA-256. Il la compare ensuite avec l'empreinte attendue fournie dans la configuration. Si les deux ne correspondent pas exactement, la connexion est immédiatement interrompue **et le fichier n'est pas envoyé**, évitant ainsi de potentiellement transmettre des données à un serveur non autorisé.
- **Obtention de l'empreinte du serveur** : Pour configurer `EXPECTED_HOSTKEY_FINGERPRINT`, vous pouvez obtenir l'empreinte de la clé publique de votre serveur SFTP de plusieurs manières sécurisées. Par exemple, depuis une session shell sûre sur le serveur lui-même, vous pouvez utiliser la commande OpenSSH suivante (en adaptant le chemin vers la clé adéquate) :

    ```bash
    ssh-keygen -l -f /etc/ssh/ssh_host_rsa_key.pub -E sha256
    ```

  Cette commande affichera l'empreinte SHA-256 de la clé publique du serveur (après le préfixe "`SHA256:`"). Vous pouvez aussi utiliser `ssh-keyscan` depuis une machine cliente de confiance, puis calculer l'empreinte via `ssh-keygen`. L'empreinte obtenue (la suite de caractères Base64) doit être recopiée dans le script.

- **Bibliothèque Paramiko** : Le script utilise la bibliothèque Python [Paramiko](https://docs.paramiko.org/) pour établir la connexion SSH/SFTP. La vérification de l'empreinte se fait manuellement dans le code en utilisant les fonctions de Paramiko (récupération de la clé du serveur et calcul de son hash SHA-256) afin de la comparer à la valeur attendue. Si vous exécutez ce script, assurez-vous d'avoir installé Paramiko au préalable (`pip install paramiko`).

## Suppression du fichier local
Le fichier temporaire contenant le rapport (`rapport_systeme.txt`) est supprimé du système local une fois l'envoi terminé. Cette suppression est effectuée dans tous les cas de figure possibles (dans un bloc `finally` en Python) pour s'assurer que même en cas d'erreur lors de l'envoi, le script tente de ne pas laisser de fichier sensible sur la machine. Cette précaution contribue à la discrétion du script en évitant qu'un utilisateur local ne découvre le rapport.

## Utilisation du script
Pour utiliser le script, il suffit de le lancer sur la machine à auditer :

- Sur Windows, vous pouvez exécuter `python script.py` (avec Python 3 installé). Pour un mode totalement silencieux, il est possible d'utiliser `pythonw.exe` ou d'en faire un service/une tâche planifiée afin qu'aucune console ne s'ouvre.
- Sur Linux, exécutez `python3 script.py` (en veillant à ce que le script soit exécutable ou en appelant explicitement l'interpréteur Python). Aucune sortie ne sera affichée à l'écran. Vous pouvez planifier ce script via `cron` ou un autre planificateur pour des exécutions périodiques discrètes.

Une fois exécuté, le script créera le rapport, le transférera via SFTP puis se terminera. Si tout est correctement configuré, le fichier de rapport devrait se trouver sur le serveur SFTP au chemin spécifié, et aucune trace locale ne subsiste en dehors des éventuels journaux du système (si le script a été lancé via une tâche planifiée, par exemple).

## Structure du dépôt GitHub
Ce dépôt contient les fichiers suivants :
- **script.py** : Le script Python principal décrivant l'ensemble du processus (collecte d'infos, transfert SFTP). Il est abondamment commenté pour expliquer chaque étape.
- **README.md** : Le présent document explicatif décrivant le fonctionnement du script, les paramètres à configurer, les mesures de sécurité mises en place, et les instructions d'utilisation.
- **.gitignore** : Fichier listant les éléments à ignorer dans le dépôt Git (par exemple, le fichier de rapport temporaire s'il était généré localement, les fichiers de cache Python `__pycache__`, etc.). Cela permet d'éviter de compromettre des informations sensibles ou inutiles dans le contrôle de version.

***By Micka Delcato***
