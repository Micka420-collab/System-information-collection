# System Information Collection and Secure SFTP Transfer Script

## Description

This project provides a cross-platform Python script (Windows and Linux) that discreetly gathers various pieces of information from the local machine, generates a temporary report, and then securely sends it to a remote server via SFTP. The script is designed to run in **silent mode**, meaning no visible output on the screen, allowing it to operate in the background.

## Script Workflow

The script performs the following steps:

1. **System Information Collection**: Retrieves the hostname, current user, assigned IP addresses, list of running processes, disk information (total size and free space), RAM details, and the list of installed software.
2. **Report Generation**: The collected data is formatted and written to a temporary text file (e.g., `system_report.txt`) stored in the OS's temporary directory (such as `%TEMP%` on Windows or `/tmp` on Linux).
3. **Secure SFTP Transfer**: The report file is then securely transmitted to the specified SFTP server. The connection uses SSH (port 22 by default) with server identity verification (see Security section below).
4. **Cleanup**: Once the file is successfully sent, the local temporary file is deleted to leave no trace.

## SFTP Configuration Parameters

The following parameters must be configured in the script prior to execution to match your environment:

* **SFTP\_HOST**: Hostname or IP address of the destination SFTP server.
* **SFTP\_PORT**: TCP port of the SFTP service (default is 22 for SSH).
* **SFTP\_USERNAME**: Username for SFTP server login.
* **SFTP\_PASSWORD**: Password for the SFTP user.
* **REMOTE\_PATH**: Full path on the server where the report file should be uploaded. For example: `/home/user/reports/system_report.txt`.

These credentials and configuration values are stored at the top of the script in easily identifiable variables. **Important**: Do not store sensitive information (like passwords) in a public GitHub repository. Consider using a separate configuration file or environment variables for enhanced security.

## Enhanced SSH Security (Server Key Verification)

The script includes an additional security measure to prevent **Man-in-the-Middle (MITM)** attacks during the SFTP connection. Before transmitting the password or file, it verifies that the SFTP server’s public key matches the expected one.

* **Known Public Key Fingerprint**: It is assumed that the fingerprint (digital hash) of the server’s public key is known and hardcoded in the script (`EXPECTED_HOSTKEY_FINGERPRINT`). This fingerprint is in SHA-256 format (OpenSSH default), typically Base64-encoded.

* **Fingerprint Comparison**: During connection, the script retrieves the server’s presented public key and calculates its SHA-256 fingerprint. It then compares it with the expected value. If they do not match exactly, the connection is immediately aborted **and the file is not sent**, thereby avoiding potential data leaks to unauthorized servers.

* **Getting the Server Fingerprint**: To set `EXPECTED_HOSTKEY_FINGERPRINT`, you can retrieve the server's public key fingerprint securely from a trusted session on the server using:

  ```bash
  ssh-keygen -l -f /etc/ssh/ssh_host_rsa_key.pub -E sha256
  ```

  This command outputs the server’s SHA-256 fingerprint (following the "`SHA256:`" prefix). You can also use `ssh-keyscan` from a trusted client machine and calculate the fingerprint using `ssh-keygen`. Copy the resulting Base64 string into your script.

* **Paramiko Library**: The script uses the Python [Paramiko](https://docs.paramiko.org/) library to establish the SSH/SFTP connection. Fingerprint verification is performed manually in the code by retrieving the server key and computing its SHA-256 hash for comparison. Ensure Paramiko is installed beforehand (`pip install paramiko`).

## Local File Deletion

The temporary report file (`system_report.txt`) is deleted from the local system after transfer. This deletion is handled in a `finally` block in Python to ensure that even if an error occurs during upload, the script will still attempt to remove the file. This contributes to the script’s discretion by minimizing the chance a local user could discover the report.

## Using the Script

To use the script, simply execute it on the machine to be audited:

* On Windows, run `python script.py` (requires Python 3). For full silent mode, you can use `pythonw.exe` or set it up as a scheduled task/service to avoid opening a console window.
* On Linux, execute `python3 script.py` (ensure the script is executable or explicitly call the Python interpreter). No output will appear on screen. You can schedule this script using `cron` or another scheduler for periodic background runs.

Once executed, the script will generate the report, transfer it via SFTP, and then terminate. If everything is configured correctly, the report file will be found on the SFTP server at the specified path, and no local trace remains except for potential system logs (if launched via scheduled task, for example).

## GitHub Repository Structure

This repository contains the following files:

* **script.py**: The main Python script that handles information gathering and SFTP transfer. It includes extensive comments explaining each step.
* **README.md**: This documentation file describing how the script works, configuration parameters, security measures, and usage instructions.
* **.gitignore**: Lists items to ignore in the Git repository (e.g., the temporary report file, Python cache directories like `__pycache__`, etc.). This helps avoid leaking sensitive or unnecessary files through version control.

***By Micka Delcato***
