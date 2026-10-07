#!/usr/bin/env python3
"""CGI handler for the static site's Contact Us form.

Sends the visitor's message through Gmail SMTP to an address that only the
server knows, then redirects back to contact.html with a status fragment
(#sent, #error or #busy) that the page shows using CSS :target, so the page
needs no JavaScript.

Standard library only. The ``cgi`` module was removed in Python 3.13, so the
form body is parsed by hand.

Settings come from an INI file outside the web root, whose path is given by the
CONTACT_CONFIG environment variable, and/or CONTACT_<KEY> environment variables,
which take precedence. See deploy/contact.example.ini.
"""

import configparser
import json
import os
import smtplib
import ssl
import sys
import tempfile
import time
from email.message import EmailMessage
from email.utils import formataddr
from urllib.parse import parse_qs

MAX_BODY_BYTES = 20_000
FIELD_LIMITS = {"name": 100, "email": 254, "subject": 150, "message": 5000}
REQUIRED_FIELDS = ("name", "email", "message")
HONEYPOT_FIELD = "website"

RATE_LIMIT_COUNT = 5
RATE_LIMIT_WINDOW_SECONDS = 3600
RATE_LIMIT_FILE = os.path.join(tempfile.gettempdir(), "church-alliance-contact-rate.json")

DEFAULT_SETTINGS = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": "587",
    "smtp_user": "",
    "smtp_password": "",
    "sender": "",
    "sender_name": "Church Alliance Website",
    "recipient": "",
    "redirect": "/contact.html",
}


class FormError(ValueError):
    """The submission is malformed or fails validation."""


def log(message):
    # CGI stderr goes to the web server's error log.
    print(f"contact.py: {message}", file=sys.stderr)


def load_settings(environ):
    settings = dict(DEFAULT_SETTINGS)

    config_path = environ.get("CONTACT_CONFIG")
    if config_path:
        parser = configparser.ConfigParser(interpolation=None)
        if not parser.read(config_path, encoding="utf-8"):
            raise RuntimeError(f"cannot read config file {config_path}")
        if parser.has_section("contact"):
            settings.update({key: value for key, value in parser["contact"].items() if key in settings})

    for key in settings:
        value = environ.get(f"CONTACT_{key.upper()}")
        if value:
            settings[key] = value

    # Gmail displays app passwords in groups of four; the spaces are not part of it.
    settings["smtp_password"] = settings["smtp_password"].replace(" ", "")
    settings["sender"] = settings["sender"] or settings["smtp_user"]

    missing = [key for key in ("smtp_user", "smtp_password", "recipient") if not settings[key]]
    if missing:
        raise RuntimeError(f"missing settings: {', '.join(missing)}")
    return settings


def read_body(environ, stdin):
    """Read the request body up front.

    Apache writes the body to the script's stdin; exiting without reading it
    makes that write fail and the response gets cut off. Oversized bodies are
    not read at all.
    """
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        length = 0
    if length <= 0 or length > MAX_BODY_BYTES:
        return None
    return stdin.read(length)


def parse_form(environ, body):
    if body is None:
        raise FormError(f"missing or oversized body (Content-Length {environ.get('CONTENT_LENGTH')!r})")

    content_type = environ.get("CONTENT_TYPE", "").split(";")[0].strip().lower()
    if content_type != "application/x-www-form-urlencoded":
        raise FormError(f"unsupported content type {content_type!r}")

    try:
        fields = parse_qs(body.decode("utf-8", errors="replace"), keep_blank_values=True, max_num_fields=20)
    except ValueError as exc:
        raise FormError(str(exc)) from exc
    return {key: values[0].strip() for key, values in fields.items()}


def single_line(value):
    """Collapse line breaks so a value can't inject extra email headers."""
    return " ".join(value.split())


def validate(form):
    data = {key: form.get(key, "") for key in FIELD_LIMITS}

    for key in REQUIRED_FIELDS:
        if not data[key]:
            raise FormError(f"missing {key}")
    for key, limit in FIELD_LIMITS.items():
        if len(data[key]) > limit:
            raise FormError(f"{key} longer than {limit} characters")

    for key in ("name", "email", "subject"):
        data[key] = single_line(data[key])

    local, _, domain = data["email"].partition("@")
    if not local or "." not in domain or " " in data["email"] or "@" in domain:
        raise FormError("invalid email address")
    return data


def allow_request(remote_addr, now=None):
    """Best-effort per-IP limit, stored in a small JSON file in the temp directory."""
    now = time.time() if now is None else now
    try:
        with open(RATE_LIMIT_FILE, encoding="utf-8") as handle:
            hits = json.load(handle)
    except (OSError, ValueError):
        hits = {}

    hits = {
        addr: recent
        for addr, times in hits.items()
        if (recent := [t for t in times if now - t < RATE_LIMIT_WINDOW_SECONDS])
    }
    recent = hits.setdefault(remote_addr, [])
    allowed = len(recent) < RATE_LIMIT_COUNT
    if allowed:
        recent.append(now)

    try:
        with open(RATE_LIMIT_FILE, "w", encoding="utf-8") as handle:
            json.dump(hits, handle)
    except OSError as exc:
        log(f"could not write rate limit file: {exc}")
    return allowed


def build_message(settings, data, remote_addr):
    message = EmailMessage()
    message["Subject"] = f"Website contact: {data['subject'] or 'New message'}"
    message["From"] = formataddr((settings["sender_name"], settings["sender"]))
    message["To"] = settings["recipient"]
    # Gmail only sends as the authenticated account, so the visitor goes in Reply-To.
    message["Reply-To"] = formataddr((data["name"], data["email"]))
    message.set_content(
        f"Name: {data['name']}\n"
        f"Email: {data['email']}\n"
        f"Subject: {data['subject'] or '(none)'}\n"
        f"Sender IP: {remote_addr}\n"
        f"\n{data['message']}\n"
    )
    return message


def send_message(settings, message):
    host, port = settings["smtp_host"], int(settings["smtp_port"])
    context = ssl.create_default_context()
    if port == 465:
        smtp = smtplib.SMTP_SSL(host, port, timeout=20, context=context)
    else:
        smtp = smtplib.SMTP(host, port, timeout=20)
    with smtp:
        if port != 465:
            smtp.starttls(context=context)
        smtp.login(settings["smtp_user"], settings["smtp_password"])
        smtp.send_message(message)


def redirect(stdout, base, status):
    stdout.write(f"Status: 303 See Other\r\nLocation: {base}#{status}\r\n\r\n")


def main(environ=None, stdin=None, stdout=None):
    environ = os.environ if environ is None else environ
    stdin = sys.stdin.buffer if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout

    if environ.get("REQUEST_METHOD") != "POST":
        stdout.write("Status: 405 Method Not Allowed\r\nAllow: POST\r\nContent-Type: text/plain\r\n\r\nMethod not allowed\n")
        return

    body = read_body(environ, stdin)

    try:
        settings = load_settings(environ)
    except Exception as exc:
        log(f"configuration error: {exc}")
        redirect(stdout, DEFAULT_SETTINGS["redirect"], "error")
        return
    target = settings["redirect"]

    try:
        form = parse_form(environ, body)
        if form.get(HONEYPOT_FIELD):
            # Bots fill the hidden field; pretend it worked so they don't adapt.
            redirect(stdout, target, "sent")
            return
        data = validate(form)
    except FormError as exc:
        log(f"rejected submission: {exc}")
        redirect(stdout, target, "error")
        return

    remote_addr = environ.get("REMOTE_ADDR", "unknown")
    if not allow_request(remote_addr):
        log(f"rate limit reached for {remote_addr}")
        redirect(stdout, target, "busy")
        return

    try:
        send_message(settings, build_message(settings, data, remote_addr))
    except (OSError, smtplib.SMTPException) as exc:
        log(f"sending failed: {exc!r}")
        redirect(stdout, target, "error")
        return

    redirect(stdout, target, "sent")


if __name__ == "__main__":
    main()
