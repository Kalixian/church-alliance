import importlib.util
import io
import smtplib
from pathlib import Path
from urllib.parse import urlencode

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "static" / "cgi-bin" / "contact.py"
spec = importlib.util.spec_from_file_location("contact_cgi", SCRIPT)
contact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contact)

SETTINGS_ENV = {
    "CONTACT_SMTP_USER": "sender@gmail.com",
    "CONTACT_SMTP_PASSWORD": "abcd efgh ijkl mnop",
    "CONTACT_RECIPIENT": "hidden@example.org",
}

VALID_FORM = {
    "name": "Pat Visitor",
    "email": "pat@example.com",
    "subject": "Training",
    "message": "When is the next class?",
    "website": "",
}


class FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout=None):
        self.host, self.port = host, port
        self.started_tls = False
        self.login_args = None
        self.sent = []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self, context=None):
        self.started_tls = True

    def login(self, user, password):
        self.login_args = (user, password)

    def send_message(self, message):
        self.sent.append(message)


@pytest.fixture(autouse=True)
def fake_smtp(monkeypatch, tmp_path):
    FakeSMTP.instances = []
    monkeypatch.setattr(contact.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(contact, "RATE_LIMIT_FILE", str(tmp_path / "rate.json"))
    return FakeSMTP


def run(form=None, method="POST", env=None, remote_addr="203.0.113.5"):
    body = urlencode(form if form is not None else VALID_FORM).encode()
    environ = {
        **SETTINGS_ENV,
        "REQUEST_METHOD": method,
        "CONTENT_LENGTH": str(len(body)),
        "CONTENT_TYPE": "application/x-www-form-urlencoded",
        "REMOTE_ADDR": remote_addr,
        **(env or {}),
    }
    stdout = io.StringIO()
    contact.main(environ=environ, stdin=io.BytesIO(body), stdout=stdout)
    return stdout.getvalue()


def sent_messages():
    return [message for smtp in FakeSMTP.instances for message in smtp.sent]


def test_valid_submission_sends_to_hidden_recipient_and_redirects():
    output = run()

    assert output.startswith("Status: 303")
    assert "Location: /contact.html#sent" in output
    [message] = sent_messages()
    assert message["To"] == "hidden@example.org"
    assert message["Reply-To"] == "Pat Visitor <pat@example.com>"
    assert "sender@gmail.com" in message["From"]
    assert message["Subject"] == "Website contact: Training"
    assert "When is the next class?" in message.get_content()

    smtp = FakeSMTP.instances[0]
    assert (smtp.host, smtp.port) == ("smtp.gmail.com", 587)
    assert smtp.started_tls
    assert smtp.login_args == ("sender@gmail.com", "abcdefghijklmnop")


def test_settings_load_from_config_file(tmp_path):
    config = tmp_path / "contact.ini"
    config.write_text(
        "[contact]\nsmtp_user = file@gmail.com\nsmtp_password = p%ss\n"
        "recipient = file-recipient@example.org\nredirect = /site/contact.html\n",
        encoding="utf-8",
    )
    environ = {"CONTACT_CONFIG": str(config)}

    settings = contact.load_settings(environ)

    assert settings["smtp_user"] == "file@gmail.com"
    assert settings["smtp_password"] == "p%ss"
    assert settings["sender"] == "file@gmail.com"
    assert settings["redirect"] == "/site/contact.html"


def test_environment_overrides_config_file(tmp_path):
    config = tmp_path / "contact.ini"
    config.write_text("[contact]\nsmtp_user = a@gmail.com\nsmtp_password = x\nrecipient = a@example.org\n")

    settings = contact.load_settings({"CONTACT_CONFIG": str(config), "CONTACT_RECIPIENT": "b@example.org"})

    assert settings["recipient"] == "b@example.org"


def test_missing_settings_redirect_to_error_without_sending():
    output = run(env={"CONTACT_RECIPIENT": "", "CONTACT_SMTP_PASSWORD": ""})

    assert "#error" in output
    assert sent_messages() == []


def test_body_is_read_even_when_settings_are_missing():
    # Apache's write to the script's stdin fails if the script exits without reading it.
    body = urlencode(VALID_FORM).encode()
    stdin = io.BytesIO(body)
    environ = {"REQUEST_METHOD": "POST", "CONTENT_LENGTH": str(len(body)),
               "CONTENT_TYPE": "application/x-www-form-urlencoded"}

    contact.main(environ=environ, stdin=stdin, stdout=io.StringIO())

    assert stdin.tell() == len(body)


def test_get_request_is_rejected():
    output = run(method="GET")

    assert output.startswith("Status: 405")
    assert sent_messages() == []


def test_honeypot_pretends_success_without_sending():
    output = run({**VALID_FORM, "website": "http://spam.example"})

    assert "#sent" in output
    assert sent_messages() == []


@pytest.mark.parametrize(
    "changes",
    [
        {"name": ""},
        {"message": "   "},
        {"email": "not-an-email"},
        {"email": "a@b@example.com"},
        {"message": "x" * 5001},
    ],
)
def test_invalid_submissions_redirect_to_error(changes):
    output = run({**VALID_FORM, **changes})

    assert "#error" in output
    assert sent_messages() == []


def test_line_breaks_cannot_inject_headers():
    run({**VALID_FORM, "name": "Pat\r\nBcc: victim@example.com", "subject": "Hi\nBcc: x@example.com"})

    [message] = sent_messages()
    assert message["Bcc"] is None
    assert message["Subject"] == "Website contact: Hi Bcc: x@example.com"


def test_rate_limit_per_address():
    for _ in range(contact.RATE_LIMIT_COUNT):
        assert "#sent" in run()

    assert "#busy" in run()
    assert "#sent" in run(remote_addr="198.51.100.7")
    assert len(sent_messages()) == contact.RATE_LIMIT_COUNT + 1


def test_smtp_failure_redirects_to_error(monkeypatch):
    class FailingSMTP(FakeSMTP):
        def login(self, user, password):
            raise smtplib.SMTPAuthenticationError(535, b"bad credentials")

    monkeypatch.setattr(contact.smtplib, "SMTP", FailingSMTP)

    assert "#error" in run()
