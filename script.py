#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de collecte d'informations système et envoi SFTP sécurisé.
Ce script fonctionne sous Windows et Linux.
By Micka
"""
import os
import platform
import socket
import getpass
import subprocess
import tempfile
import hashlib
import base64
import string
import shutil
import paramiko

# Paramètres SFTP à configurer
SFTP_HOST = "exemple.com"         # Nom d'hôte ou adresse du serveur SFTP
SFTP_PORT = 22                    # Port du serveur SFTP (22 par défaut pour SSH/SFTP)
SFTP_USERNAME = "utilisateur"     # Nom d'utilisateur pour la connexion SFTP
SFTP_PASSWORD = "mot_de_passe"    # Mot de passe pour la connexion SFTP
# Empreinte attendue de la clé publique du serveur (format SHA256 base64 sans le préfixe)
EXPECTED_HOSTKEY_FINGERPRINT = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
# Chemin distant où envoyer le fichier (par exemple dossier de destination sur le serveur)
REMOTE_PATH = "/chemin/serveur/rapport_systeme.txt"

# Récupération des informations système locales
system = platform.system()
hostname = socket.gethostname()
current_user = getpass.getuser()

# Récupération des adresses IP locales (possiblement multiples)
ips = []
try:
    host_info = socket.gethostbyname_ex(hostname)
    ips = host_info[2]
except Exception:
    try:
        ips.append(socket.gethostbyname(hostname))
    except Exception:
        pass
# Si aucune IP trouvée, on tente une méthode alternative via une connexion UDP fictive
if not ips:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
    except Exception:
        pass
    finally:
        s.close()

# Récupération des informations de processus en cours
try:
    if system == "Windows":
        # Sous Windows, utilisation de la commande 'tasklist'
        processes = subprocess.check_output(["tasklist"], shell=True)
    else:
        # Sous Linux/Unix, utilisation de la commande 'ps aux'
        processes = subprocess.check_output(["ps", "aux"])
    processes_output = processes.decode(errors='ignore').strip()
except Exception as e:
    processes_output = f"Impossible de récupérer la liste des processus: {e}"

# Récupération des informations sur les disques
try:
    if system == "Windows":
        # Sous Windows, parcourir les lecteurs de A: à Z: pour obtenir leur espace
        disks_info_lines = []
        for drive in string.ascii_uppercase:
            if os.path.exists(f"{drive}:\\\\"):
                try:
                    total, used, free = shutil.disk_usage(f"{drive}:\\\\")
                    total_gb = total // (1024**3)
                    free_gb = free // (1024**3)
                    disks_info_lines.append(f"{drive}: Total {total_gb} GB, Libre {free_gb} GB")
                except Exception:
                    pass
        if disks_info_lines:
            disks_info = "\\n".join(disks_info_lines)
        else:
            disks_info = "Aucun disque détecté."
    else:
        # Sous Linux, utilisation de la commande 'df -h' pour lister les systèmes de fichiers
        disks = subprocess.check_output(["df", "-h"])
        disks_info = disks.decode(errors='ignore').strip()
except Exception as e:
    disks_info = f"Impossible de récupérer les informations disque: {e}"

# Récupération des informations de mémoire RAM
try:
    if system == "Windows":
        # Sous Windows, utiliser WMIC pour obtenir la mémoire totale et libre en KB
        mem_info = subprocess.check_output(
            ["wmic", "OS", "get", "FreePhysicalMemory,TotalVisibleMemorySize", "/Value"],
            shell=True
        ).decode(errors='ignore')
        total_mem_kb = 0
        free_mem_kb = 0
        for line in mem_info.splitlines():
            if line.strip().startswith("TotalVisibleMemorySize="):
                total_mem_kb = int(line.split("=",1)[1])
            elif line.strip().startswith("FreePhysicalMemory="):
                free_mem_kb = int(line.split("=",1)[1])
        if total_mem_kb > 0:
            used_mem_kb = total_mem_kb - free_mem_kb
            total_mem_mb = total_mem_kb // 1024
            free_mem_mb = free_mem_kb // 1024
            used_mem_mb = used_mem_kb // 1024
            mem_info_str = f"Total: {total_mem_mb} MB, Libre: {free_mem_mb} MB, Utilisé: {used_mem_mb} MB"
        else:
            mem_info_str = "Informations mémoire non disponibles."
    else:
        # Sous Linux, lire /proc/meminfo pour obtenir la mémoire totale et disponible
        total_mem_kb = 0
        free_mem_kb = 0
        available_mem_kb = 0
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    parts = line.split()
                    if len(parts) >= 2:
                        total_mem_kb = int(parts[1])
                elif line.startswith("MemAvailable:"):
                    parts = line.split()
                    if len(parts) >= 2:
                        available_mem_kb = int(parts[1])
                elif line.startswith("MemFree:") and available_mem_kb == 0:
                    # Utiliser MemFree seulement si MemAvailable n'est pas présent
                    parts = line.split()
                    if len(parts) >= 2:
                        free_mem_kb = int(parts[1])
        if available_mem_kb:
            free_mem_kb = available_mem_kb
        if total_mem_kb > 0:
            used_mem_kb = total_mem_kb - free_mem_kb
            total_mem_mb = total_mem_kb // 1024
            free_mem_mb = free_mem_kb // 1024
            used_mem_mb = used_mem_kb // 1024
            mem_info_str = f"Total: {total_mem_mb} MB, Disponible: {free_mem_mb} MB, Utilisé: {used_mem_mb} MB"
        else:
            mem_info_str = "Informations mémoire non disponibles."
except Exception as e:
    mem_info_str = f"Impossible de récupérer les informations de mémoire: {e}"

# Récupération de la liste des logiciels installés
try:
    if system == "Windows":
        # Sous Windows, utiliser WMIC pour lister les logiciels installés (Nom et version)
        software = subprocess.check_output(["wmic", "product", "get", "Name,Version"], shell=True)
        software_list = software.decode(errors='ignore').strip()
    else:
        # Sous Linux, essayer dpkg (Debian/Ubuntu) ou rpm pour lister les paquets installés
        try:
            software_list = subprocess.check_output(["dpkg", "-l"], stderr=subprocess.DEVNULL)
            software_list = software_list.decode(errors='ignore').strip()
        except Exception:
            try:
                software_list = subprocess.check_output(["rpm", "-qa"], stderr=subprocess.DEVNULL)
                software_list = software_list.decode(errors='ignore').strip()
            except Exception as e_soft:
                software_list = f"Impossible de lister les logiciels installés: {e_soft}"
except Exception as e:
    software_list = f"Impossible de lister les logiciels installés: {e}"

# Construction du contenu du rapport
report_lines = []
report_lines.append(f"Hostname: {hostname}")
report_lines.append(f"Utilisateur: {current_user}")
report_lines.append(f"Système: {system}")
if ips:
    report_lines.append("Adresse(s) IP: " + ", ".join(ips))
else:
    report_lines.append("Adresse(s) IP: Aucune adresse détectée")
report_lines.append("")  # ligne vide
report_lines.append("=== Mémoire RAM ===")
report_lines.append(f"{mem_info_str}")
report_lines.append("")  # ligne vide
report_lines.append("=== Disques ===")
report_lines.append(f"{disks_info}")
report_lines.append("")  # ligne vide
report_lines.append("=== Processus en cours ===")
report_lines.append(processes_output)
report_lines.append("")  # ligne vide
report_lines.append("=== Logiciels installés ===")
report_lines.append(software_list)
report_lines.append("")  # ligne vide

report_content = "\\n".join(report_lines)

# Enregistrement du rapport dans un fichier temporaire
temp_dir = tempfile.gettempdir()
report_file_path = os.path.join(temp_dir, "rapport_systeme.txt")
try:
    with open(report_file_path, "w", encoding="utf-8") as f:
        f.write(report_content)
except Exception as e:
    # Si l'écriture du fichier échoue, on arrête le script (pas d'envoi)
    raise e

# Envoi sécurisé du fichier via SFTP (avec vérification de l'empreinte de clé SSH)
transport = None
sftp = None
try:
    # Initialisation de la connexion SSH/SFTP
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.start_client(timeout=10)
    # Récupérer la clé publique du serveur et vérifier son empreinte
    server_key = transport.get_remote_server_key()
    # Calculer l'empreinte SHA256 de la clé du serveur
    key_bytes = server_key.asbytes()
    sha256_digest = hashlib.sha256(key_bytes).digest()
    fingerprint_b64 = base64.b64encode(sha256_digest).decode('utf-8').rstrip("=")
    computed_fingerprint = f"SHA256:{fingerprint_b64}"
    # Comparer avec l'empreinte attendue
    if EXPECTED_HOSTKEY_FINGERPRINT and computed_fingerprint != f"SHA256:{EXPECTED_HOSTKEY_FINGERPRINT}":
        # Si elle ne correspond pas, lever une exception et interrompre la connexion
        raise paramiko.ssh_exception.BadHostKeyException(hostname=SFTP_HOST, key=server_key, expected_key=EXPECTED_HOSTKEY_FINGERPRINT)
    # Si l'empreinte est vérifiée, on peut continuer avec l'authentification
    transport.auth_password(username=SFTP_USERNAME, password=SFTP_PASSWORD)
    # Ouvrir la session SFTP et transférer le fichier
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.put(report_file_path, REMOTE_PATH)
finally:
    # Fermer proprement la connexion SFTP/SSH
    if sftp:
        try:
            sftp.close()
        except:
            pass
    if transport:
        transport.close()

# Suppression du fichier de rapport local temporaire
try:
    os.remove(report_file_path)
except Exception:
    pass