"""End-to-end through the HTTP layer, using TestClient (no server, no network)."""

from __future__ import annotations

PAYLOAD = {"subject": "Refund", "text": "Please refund my order", "priority": 2}


def _create(client, headers, **overrides):
    body = {**PAYLOAD, **overrides}
    return client.post("/tickets", json=body, headers=headers)


def test_health_needs_no_auth(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_returns_201_and_public_shape(client, alice):
    response = _create(client, alice)
    assert response.status_code == 201
    body = response.json()
    assert body["subject"] == "Refund"
    assert body["status"] == "open"
    # response_model filtering: internal fields must NOT be present.
    assert "owner_id" not in body
    assert "internal_notes" not in body


def test_missing_token_is_401(client):
    assert _create(client, {}).status_code == 401


def test_invalid_token_is_401(client):
    assert _create(client, {"Authorization": "Bearer nope"}).status_code == 401


def test_validation_error_is_422_with_field(client, alice):
    response = _create(client, alice, priority=99)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "priority"]


def test_mass_assignment_rejected(client, alice):
    response = client.post(
        "/tickets",
        json={**PAYLOAD, "owner_id": "u-bob", "status": "resolved"},
        headers=alice,
    )
    assert response.status_code == 422
    fields = {tuple(e["loc"]) for e in response.json()["detail"]}
    assert ("body", "owner_id") in fields


def test_owner_can_read_own_ticket(client, alice):
    ticket_id = _create(client, alice).json()["ticket_id"]
    assert client.get(f"/tickets/{ticket_id}", headers=alice).status_code == 200


def test_other_user_gets_404_not_403(client, alice, bob):
    """404 deliberately, so the response does not confirm the ticket exists."""
    ticket_id = _create(client, alice).json()["ticket_id"]
    response = client.get(f"/tickets/{ticket_id}", headers=bob)
    assert response.status_code == 404
    assert response.json()["detail"] == "ticket not found"


def test_nonexistent_ticket_is_indistinguishable(client, alice, bob):
    ticket_id = _create(client, alice).json()["ticket_id"]
    real = client.get(f"/tickets/{ticket_id}", headers=bob)
    fake = client.get("/tickets/T-does-not-exist", headers=bob)
    assert real.status_code == fake.status_code == 404
    assert real.json()["detail"] == fake.json()["detail"]


def test_admin_can_read_any_ticket(client, alice, admin):
    ticket_id = _create(client, alice).json()["ticket_id"]
    assert client.get(f"/tickets/{ticket_id}", headers=admin).status_code == 200


def test_list_is_scoped(client, alice, bob, admin):
    _create(client, alice)
    _create(client, bob)
    assert len(client.get("/tickets", headers=alice).json()) == 1
    assert len(client.get("/tickets", headers=bob).json()) == 1
    assert len(client.get("/tickets", headers=admin).json()) == 2


def test_pagination_bounds_enforced(client, alice):
    assert client.get("/tickets?limit=0", headers=alice).status_code == 422
    assert client.get("/tickets?limit=101", headers=alice).status_code == 422
    assert client.get("/tickets?offset=-1", headers=alice).status_code == 422
    assert client.get("/tickets?limit=50", headers=alice).status_code == 200


def test_sql_injection_in_sort_is_rejected(client, alice):
    response = client.get(
        "/tickets?sort=priority;%20DROP%20TABLE%20tickets", headers=alice
    )
    assert response.status_code == 422
    # And the table is still there.
    assert client.get("/tickets", headers=alice).status_code == 200


def test_patch_updates_status(client, alice):
    ticket_id = _create(client, alice).json()["ticket_id"]
    response = client.patch(f"/tickets/{ticket_id}",
                            json={"status": "resolved"}, headers=alice)
    assert response.status_code == 200
    assert response.json()["status"] == "resolved"


def test_empty_patch_is_422(client, alice):
    ticket_id = _create(client, alice).json()["ticket_id"]
    response = client.patch(f"/tickets/{ticket_id}", json={}, headers=alice)
    assert response.status_code == 422


def test_non_admin_cannot_set_internal_notes(client, alice):
    ticket_id = _create(client, alice).json()["ticket_id"]
    response = client.patch(f"/tickets/{ticket_id}",
                            json={"internal_notes": "VIP"}, headers=alice)
    assert response.status_code == 403


def test_admin_endpoint_requires_admin(client, alice, admin):
    assert client.get("/admin/stats", headers=alice).status_code == 403
    assert client.get("/admin/stats", headers=admin).status_code == 200


def test_every_response_carries_a_request_id(client, alice):
    response = _create(client, alice)
    assert response.headers["X-Request-ID"].startswith("req_")


def test_supplied_request_id_is_echoed(client, alice):
    response = client.post("/tickets", json=PAYLOAD,
                           headers={**alice, "X-Request-ID": "req_from_caller"})
    assert response.headers["X-Request-ID"] == "req_from_caller"


def test_error_responses_include_request_id(client, alice):
    response = client.get("/tickets/T-missing", headers=alice)
    assert response.status_code == 404
    assert response.json()["request_id"].startswith("req_")


def test_ticket_text_is_not_logged(client, alice, caplog):
    """A privacy property, asserted rather than hoped for (M2-L18)."""
    import logging

    with caplog.at_level(logging.INFO):
        _create(client, alice, text="SECRET complaint about Jane Doe")
    assert "SECRET" not in caplog.text
    assert "Jane Doe" not in caplog.text
