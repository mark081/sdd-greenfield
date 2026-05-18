"""Property-based tests for the todo-app using Hypothesis.

Each test is tagged with the design property it validates.
"""
import re

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ISO8601_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?\+00:00$|"
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$"
)

# Strategies
valid_title_st = st.text(min_size=1, max_size=200).filter(lambda s: s.strip() != "")
valid_description_st = st.text(min_size=1, max_size=1000)
whitespace_title_st = st.text(alphabet=" \t\n\r", min_size=1)
long_title_st = st.text(min_size=201)

_SUPPRESS = [HealthCheck.function_scoped_fixture]


# ---------------------------------------------------------------------------
# Property 1: Creation round-trip preserves all fields
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=_SUPPRESS)
@given(
    title=valid_title_st,
    description=st.one_of(st.none(), valid_description_st),
)
def test_creation_round_trip(client, title, description):
    # Feature: todo-app, Property 1: Creation round-trip preserves all fields
    # Validates: Requirements 1.1, 1.6, 2.3, 3.1
    payload = {"title": title}
    if description is not None:
        payload["description"] = description

    create_resp = client.post("/todos", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.get_json()

    get_resp = client.get(f"/todos/{created['id']}")
    assert get_resp.status_code == 200
    fetched = get_resp.get_json()

    assert fetched["id"] == created["id"]
    assert fetched["title"] == created["title"]
    assert fetched["description"] == created["description"]
    assert fetched["completed"] == created["completed"]
    assert fetched["created_at"] == created["created_at"]


# ---------------------------------------------------------------------------
# Property 2: Whitespace-only titles are always rejected
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=_SUPPRESS)
@given(title=whitespace_title_st)
def test_whitespace_title_rejected_on_create(client, title):
    # Feature: todo-app, Property 2: Whitespace-only titles are always rejected
    # Validates: Requirements 1.2, 4.3, 7.2, 7.3
    resp = client.post("/todos", json={"title": title})
    assert resp.status_code == 422
    assert "message" in resp.get_json()


@settings(max_examples=100, suppress_health_check=_SUPPRESS)
@given(title=whitespace_title_st)
def test_whitespace_title_rejected_on_update(client, title):
    # Feature: todo-app, Property 2: Whitespace-only titles are always rejected
    # Validates: Requirements 1.2, 4.3, 7.2, 7.3
    # Create a valid item first
    created = client.post("/todos", json={"title": "Seed item"}).get_json()
    resp = client.put(f"/todos/{created['id']}", json={"title": title})
    assert resp.status_code == 422
    assert "message" in resp.get_json()


# ---------------------------------------------------------------------------
# Property 3: Titles exceeding 200 characters are always rejected
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=_SUPPRESS)
@given(title=long_title_st)
def test_title_too_long_rejected_on_create(client, title):
    # Feature: todo-app, Property 3: Titles exceeding 200 characters are always rejected
    # Validates: Requirements 1.3, 4.4, 7.4
    resp = client.post("/todos", json={"title": title})
    assert resp.status_code == 422


@settings(max_examples=100, suppress_health_check=_SUPPRESS)
@given(title=long_title_st)
def test_title_too_long_rejected_on_update(client, title):
    # Feature: todo-app, Property 3: Titles exceeding 200 characters are always rejected
    # Validates: Requirements 1.3, 4.4, 7.4
    created = client.post("/todos", json={"title": "Seed item"}).get_json()
    resp = client.put(f"/todos/{created['id']}", json={"title": title})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Property 4: Missing required field always returns 422 with a message
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=_SUPPRESS)
@given(extra=st.fixed_dictionaries({"description": st.text(min_size=1, max_size=100)}))
def test_missing_title_returns_422(client, extra):
    # Feature: todo-app, Property 4: Missing required field always returns 422 with a message
    # Validates: Requirements 1.4, 7.5
    resp = client.post("/todos", json=extra)
    assert resp.status_code == 422
    data = resp.get_json()
    assert "message" in data


# ---------------------------------------------------------------------------
# Property 5: Newly created items have correct default values
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=_SUPPRESS)
@given(title=valid_title_st)
def test_creation_defaults(client, title):
    # Feature: todo-app, Property 5: Newly created items have correct default values
    # Validates: Requirements 1.5
    resp = client.post("/todos", json={"title": title})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["completed"] is False
    assert _ISO8601_UTC_RE.match(data["created_at"]), (
        f"created_at '{data['created_at']}' is not a valid ISO 8601 UTC timestamp"
    )


# ---------------------------------------------------------------------------
# Property 6: List is always ordered by creation time ascending
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=_SUPPRESS)
@given(n=st.integers(min_value=1, max_value=10))
def test_list_ordering(client, n):
    # Feature: todo-app, Property 6: List is always ordered by creation time ascending
    # Validates: Requirements 2.1
    titles = [f"Item {i}" for i in range(n)]
    for t in titles:
        client.post("/todos", json={"title": t})

    items = client.get("/todos").get_json()
    timestamps = [item["created_at"] for item in items]
    assert timestamps == sorted(timestamps)


# ---------------------------------------------------------------------------
# Property 7: Update round-trip reflects all changed fields
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=_SUPPRESS)
@given(
    new_title=valid_title_st,
    new_completed=st.booleans(),
)
def test_update_round_trip(client, new_title, new_completed):
    # Feature: todo-app, Property 7: Update round-trip reflects all changed fields
    # Validates: Requirements 4.1, 4.5
    created = client.post("/todos", json={"title": "Original title"}).get_json()
    todo_id = created["id"]

    put_resp = client.put(
        f"/todos/{todo_id}",
        json={"title": new_title, "completed": new_completed},
    )
    assert put_resp.status_code == 200

    get_resp = client.get(f"/todos/{todo_id}")
    assert get_resp.status_code == 200
    fetched = get_resp.get_json()

    assert fetched["title"] == new_title.strip()
    assert fetched["completed"] == new_completed


# ---------------------------------------------------------------------------
# Property 8: Delete removes item from all access paths
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=_SUPPRESS)
@given(title=valid_title_st)
def test_delete_removes_item(client, title):
    # Feature: todo-app, Property 8: Delete removes item from all access paths
    # Validates: Requirements 5.1, 3.2
    created = client.post("/todos", json={"title": title}).get_json()
    todo_id = created["id"]

    del_resp = client.delete(f"/todos/{todo_id}")
    assert del_resp.status_code == 204

    # Should not appear in list
    items = client.get("/todos").get_json()
    assert all(item["id"] != todo_id for item in items)

    # Should return 404 on direct GET
    get_resp = client.get(f"/todos/{todo_id}")
    assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# Property 9: Non-existent ID always returns 404 with a message field
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=_SUPPRESS)
@given(todo_id=st.integers(min_value=1, max_value=2**63 - 1))
def test_nonexistent_id_returns_404(client, todo_id):
    # Feature: todo-app, Property 9: Non-existent ID always returns 404 with a message field
    # Validates: Requirements 3.2, 5.2
    get_resp = client.get(f"/todos/{todo_id}")
    assert get_resp.status_code == 404
    assert "message" in get_resp.get_json()

    del_resp = client.delete(f"/todos/{todo_id}")
    assert del_resp.status_code == 404
    assert "message" in del_resp.get_json()
