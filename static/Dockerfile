# Static public site (index, about, courses, contact) served by Apache, with the
# Contact Us form handled by cgi-bin/contact.py. Runs behind the caddy service in
# docker-compose.yml, which terminates HTTPS; this container only speaks HTTP.
FROM httpd:2.4-alpine

RUN apk add --no-cache python3 \
 && rm -rf /usr/local/apache2/htdocs/* /usr/local/apache2/cgi-bin/*

COPY docker/site.conf /usr/local/apache2/conf/extra/site.conf
RUN echo "Include conf/extra/site.conf" >> /usr/local/apache2/conf/httpd.conf

# The stock ScriptAlias maps /cgi-bin/ to this directory, outside the document root.
# --chmod because a Windows checkout carries no executable bit.
COPY --chmod=755 cgi-bin/contact.py /usr/local/apache2/cgi-bin/contact.py
COPY *.html styles.css /usr/local/apache2/htdocs/
COPY images/ /usr/local/apache2/htdocs/images/

COPY --chmod=755 docker/entrypoint.sh /usr/local/bin/entrypoint.sh

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["httpd-foreground"]
