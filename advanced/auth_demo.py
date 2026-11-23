"""In-memory exercise for session expiry and tenant-scoped authorization."""

from secrets import token_urlsafe


class InvoiceAccess:
    def __init__(self):
        self.sessions = {}
        self.roles = {("maya", "tenant-a"): "billing"}
        self.invoice_tenants = {"a-724": "tenant-a", "b-724": "tenant-b"}

    def create_session(self, verified_subject, now, lifetime=300):
        """Call after a trusted identity provider verifies the subject."""
        session_id = token_urlsafe(32)
        self.sessions[session_id] = (verified_subject, now + lifetime)
        return session_id

    def logout(self, session_id):
        self.sessions.pop(session_id, None)

    def can_read_invoice(self, session_id, invoice_id, now):
        session = self.sessions.get(session_id)
        if session is None:
            return False
        subject, expires_at = session
        if now >= expires_at:
            self.logout(session_id)
            return False
        tenant = self.invoice_tenants.get(invoice_id)
        return tenant is not None and self.roles.get((subject, tenant)) == "billing"


def main():
    access = InvoiceAccess()
    session = access.create_session("maya", now=100)
    assert access.can_read_invoice(session, "a-724", now=101)
    assert not access.can_read_invoice(session, "b-724", now=101)
    assert not access.can_read_invoice(session, "missing", now=101)

    del access.roles[("maya", "tenant-a")]
    assert not access.can_read_invoice(session, "a-724", now=102)

    access.roles[("maya", "tenant-a")] = "billing"
    assert not access.can_read_invoice(session, "a-724", now=400)

    new_session = access.create_session("maya", now=401)
    access.logout(new_session)
    assert not access.can_read_invoice(new_session, "a-724", now=402)
    print("Verified tenant isolation, live membership, session expiry, and logout.")


if __name__ == "__main__":
    main()
