#!/bin/sh
# Copy the mounted contact form settings to a file only Apache's worker user can
# read. The host copy can then stay chmod 600 and owned by whoever deploys,
# since this script runs as root before Apache drops privileges.
set -e

SOURCE=/run/secrets/contact.ini
TARGET=/usr/local/apache2/conf/contact.ini
# CGI scripts run as the httpd.conf User (www-data in the official image).
APACHE_USER=$(awk '$1 == "User" { print $2 }' /usr/local/apache2/conf/httpd.conf)

if [ -f "$SOURCE" ]; then
    cp "$SOURCE" "$TARGET"
    chown "$APACHE_USER" "$TARGET"
    chmod 400 "$TARGET"
else
    echo "entrypoint: $SOURCE not mounted; the contact form will report errors" >&2
fi

exec "$@"
