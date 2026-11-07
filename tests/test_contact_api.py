import smtplib

import pytest

from app.config.settings import settings
from app.db.user import UserCreate, UserRole, create_user
from app.services import contact as contact_service

VALID_MESSAGE = {
    "name": "Pat Visitor",
    "email": "pat@example.com",
    "subject": "Training",
    "message": "When is the next class?",
    "website": "",
}


class FakeSMTP:
    instances = []
    fail_with = None
    refuse = set()

    def __init__(self, host, port, timeout=None, context=None):
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
        if FakeSMTP.fail_with:
            raise FakeSMTP.fail_with
        if message["To"] in FakeSMTP.refuse:
            raise smtplib.SMTPRecipientsRefused({message["To"]: (550, b"no such user")})
        self.sent.append(message)


@pytest.fixture(autouse=True)
def contact_settings(monkeypatch):
    FakeSMTP.instances = []
    FakeSMTP.fail_with = None
    FakeSMTP.refuse = set()
    monkeypatch.setattr(contact_service.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(contact_service.smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setattr(settings, "contact_smtp_host", "smtp.gmail.com")
    monkeypatch.setattr(settings, "contact_smtp_port", 587)
    monkeypatch.setattr(settings, "contact_smtp_user", "sender@gmail.com")
    monkeypatch.setattr(settings, "contact_smtp_password", "abcd efgh ijkl mnop")
    monkeypatch.setattr(settings, "contact_sender", None)
    contact_service.rate_limiter.reset()
    yield
    contact_service.rate_limiter.reset()


def sent_messages():
    return [message for smtp in FakeSMTP.instances for message in smtp.sent]


@pytest.fixture()
def admins(db_session):
    # create_user makes the first user in an empty database an administrator.
    first = create_user(db_session, UserCreate(auth_id="admin-1", email="admin1@example.org", role=UserRole.ADMINISTRATOR))
    create_user(db_session, UserCreate(auth_id="member-1", email="member@example.org", role=UserRole.MEMBER))
    create_user(db_session, UserCreate(auth_id="coord-1", email="coordinator@example.org", role=UserRole.COORDINATOR))
    second = create_user(db_session, UserCreate(auth_id="admin-2", email="admin2@example.org", role=UserRole.ADMINISTRATOR))
    return [first.email, second.email]


def test_each_administrator_gets_a_copy(client, admins):
    response = client.post("/api/v1/contact", json=VALID_MESSAGE)

    assert response.status_code == 202
    messages = sent_messages()
    assert sorted(message["To"] for message in messages) == sorted(admins)
    assert len(FakeSMTP.instances) == 1  # one connection for all copies
    message = messages[0]
    assert message["From"] == "Church Alliance Website <sender@gmail.com>"
    assert message["Reply-To"] == "Pat Visitor <pat@example.com>"
    assert message["Subject"] == "Website contact: Training"
    assert "When is the next class?" in message.get_content()

    smtp = FakeSMTP.instances[0]
    assert (smtp.host, smtp.port) == ("smtp.gmail.com", 587)
    assert smtp.started_tls
    assert smtp.login_args == ("sender@gmail.com", "abcdefghijklmnop")


def test_non_administrators_are_not_emailed(client, admins):
    client.post("/api/v1/contact", json=VALID_MESSAGE)

    recipients = {message["To"] for message in sent_messages()}
    assert "member@example.org" not in recipients
    assert "coordinator@example.org" not in recipients


def test_administrator_addresses_are_not_exposed(client, admins):
    response = client.post("/api/v1/contact", json=VALID_MESSAGE)

    for address in admins:
        assert address not in response.text
    for message in sent_messages():
        assert message["Cc"] is None and message["Bcc"] is None


def test_no_administrators_returns_503(client):
    response = client.post("/api/v1/contact", json=VALID_MESSAGE)

    assert response.status_code == 503
    assert sent_messages() == []


def test_refused_recipient_does_not_block_others(client, admins):
    FakeSMTP.refuse = {admins[0]}

    response = client.post("/api/v1/contact", json=VALID_MESSAGE)

    assert response.status_code == 202
    assert [message["To"] for message in sent_messages()] == [admins[1]]


def test_all_recipients_refused_returns_503(client, admins):
    FakeSMTP.refuse = set(admins)

    response = client.post("/api/v1/contact", json=VALID_MESSAGE)

    assert response.status_code == 503


def test_header_injection_is_collapsed(client, admins):
    payload = {**VALID_MESSAGE, "subject": "Hi\r\nBcc: victim@example.com"}

    response = client.post("/api/v1/contact", json=payload)

    assert response.status_code == 202
    message = sent_messages()[0]
    assert message["Subject"] == "Website contact: Hi Bcc: victim@example.com"
    assert message["Bcc"] is None


@pytest.mark.parametrize(
    "changes",
    [
        {"name": ""},
        {"name": "   "},
        {"message": ""},
        {"email": "not-an-email"},
        {"email": "pat@localhost"},
        {"name": "x" * 101},
        {"subject": "x" * 151},
        {"message": "x" * 5001},
    ],
)
def test_invalid_message_is_rejected(client, changes):
    response = client.post("/api/v1/contact", json={**VALID_MESSAGE, **changes})

    assert response.status_code == 422
    assert sent_messages() == []


def test_honeypot_pretends_success_without_sending(client, admins):
    response = client.post("/api/v1/contact", json={**VALID_MESSAGE, "website": "http://spam.example"})

    assert response.status_code == 202
    assert FakeSMTP.instances == []


def test_rate_limit_per_client(client, admins):
    for _ in range(contact_service.RATE_LIMIT_COUNT):
        assert client.post("/api/v1/contact", json=VALID_MESSAGE).status_code == 202

    response = client.post("/api/v1/contact", json=VALID_MESSAGE)

    assert response.status_code == 429
    assert len(sent_messages()) == contact_service.RATE_LIMIT_COUNT * len(admins)


def test_rate_limit_window_expires():
    limiter = contact_service.RateLimiter(count=1, window_seconds=60)

    assert limiter.allow("203.0.113.5", now=1000)
    assert not limiter.allow("203.0.113.5", now=1030)
    assert limiter.allow("198.51.100.7", now=1030)
    assert limiter.allow("203.0.113.5", now=1061)


def test_missing_configuration_returns_503(client, admins, monkeypatch):
    monkeypatch.setattr(settings, "contact_smtp_password", None)

    response = client.post("/api/v1/contact", json=VALID_MESSAGE)

    assert response.status_code == 503
    assert FakeSMTP.instances == []


def test_smtp_failure_returns_503(client, admins):
    FakeSMTP.fail_with = smtplib.SMTPAuthenticationError(535, b"bad credentials")

    response = client.post("/api/v1/contact", json=VALID_MESSAGE)

    assert response.status_code == 503
    assert response.json()["detail"].startswith("Sorry")


def test_port_465_uses_implicit_tls(client, admins, monkeypatch):
    monkeypatch.setattr(settings, "contact_smtp_port", 465)

    response = client.post("/api/v1/contact", json=VALID_MESSAGE)

    assert response.status_code == 202
    smtp = FakeSMTP.instances[0]
    assert smtp.port == 465
    assert not smtp.started_tls
