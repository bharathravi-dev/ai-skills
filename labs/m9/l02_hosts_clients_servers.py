"""M9-L02 lab -- M9-L01 showed the standardized SHAPE of tools/list and
tools/call. This lesson names the three architectural roles that shape
traveled between: a SERVER exposes tools; a CLIENT holds one dedicated,
stateful connection to exactly one server; a HOST is the application that
owns one or more clients (one per connected server) and aggregates their
tools into a single combined view for its own decision logic. The lab builds
this literally -- two servers, a Client class enforcing the 1:1 relationship,
and a Host class that aggregates -- then finds a real bug naive aggregation
produces: two servers exposing a tool with the identical name silently
collide, and only namespacing by server fixes it.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m9/l02_hosts_clients_servers.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. A SERVER: TOOLS PLUS A HANDLER, NOTHING ELSE")


class Server:
    """[REAL] A minimal MCP-style server -- a name, a tools/list-shaped
    catalog, and a call() method. It knows nothing about any client or
    host that might connect to it."""

    def __init__(self, name: str, tools: dict[str, dict], handlers: dict):
        self.name = name
        self.tools = tools
        self._handlers = handlers

    def list_tools(self) -> list[dict]:
        return [{"name": n, **spec} for n, spec in self.tools.items()]

    def call(self, tool_name: str, arguments: dict):
        return self._handlers[tool_name](**arguments)


refund_server = Server(
    name="refund_server",
    tools={"get_status": {"description": "Get an order's refund status."},
           "issue_refund": {"description": "Issue a refund for an order."}},
    handlers={
        "get_status": lambda order_id: {"order_id": order_id, "refund_status": "none"},
        "issue_refund": lambda order_id, amount: {"order_id": order_id, "refunded": amount},
    },
)

shipping_server = Server(
    name="shipping_server",
    tools={"get_status": {"description": "Get an order's shipping status."}},
    handlers={"get_status": lambda order_id: {"order_id": order_id, "shipping_status": "in_transit"}},
)

print(f"  refund_server.list_tools()   -> {refund_server.list_tools()}")
print(f"  shipping_server.list_tools() -> {shipping_server.list_tools()}")
print("\n  Two independent servers, each with its own tool catalog and its")
print("  own handler logic -- neither aware the other exists. Notice both")
print("  happen to expose a tool named 'get_status', with entirely")
print("  different meanings -- ordinary, since neither server designed")
print("  itself around the other.")


# ============================================================ 2
rule("2. A CLIENT: ONE DEDICATED CONNECTION TO EXACTLY ONE SERVER")


class Client:
    """[REAL] MCP's own defined relationship: a client is a 1:1 connection
    to a single server. This class enforces that structurally -- it is
    constructed against exactly one Server and can never reach another."""

    def __init__(self, server: Server):
        self._server = server

    def list_tools(self) -> list[dict]:
        return self._server.list_tools()

    def call_tool(self, tool_name: str, arguments: dict):
        return self._server.call(tool_name, arguments)


refund_client = Client(refund_server)
shipping_client = Client(shipping_server)

print(f"  refund_client (bound to {refund_client._server.name!r}):")
print(f"    call_tool('get_status', {{'order_id': 'O-1'}}) -> "
      f"{refund_client.call_tool('get_status', {'order_id': 'O-1'})}")
print(f"  shipping_client (bound to {shipping_client._server.name!r}):")
print(f"    call_tool('get_status', {{'order_id': 'O-1'}}) -> "
      f"{shipping_client.call_tool('get_status', {'order_id': 'O-1'})}")

print("\n  Each client is structurally bound to exactly one server at")
print("  construction time -- refund_client has no way to reach")
print("  shipping_server, and vice versa. This is what 'one client per")
print("  server connection' means concretely: not a preference, a")
print("  structural property of this class.")


# ============================================================ 3
rule("3. A HOST: OWNS MULTIPLE CLIENTS, AGGREGATES THEIR TOOLS")


class NaiveHost:
    """[REAL, deliberately naive] Owns one Client per connected server and
    aggregates every client's tools into a single flat dict keyed only by
    tool NAME -- the simplest possible aggregation, and, as section 4
    shows, a broken one."""

    def __init__(self, clients: dict[str, Client]):
        self.clients = clients

    def aggregated_tools(self) -> dict[str, str]:
        """Maps a bare tool name -> which server's client will handle it."""
        catalog: dict[str, str] = {}
        for server_name, client in self.clients.items():
            for tool in client.list_tools():
                catalog[tool["name"]] = server_name
        return catalog


naive_host = NaiveHost({"refund_server": refund_client, "shipping_server": shipping_client})
naive_catalog = naive_host.aggregated_tools()

print(f"  NaiveHost owns clients for: {list(naive_host.clients.keys())}")
print(f"  Naively aggregated catalog (tool name -> owning server): {naive_catalog}")

print("\n  Only ONE 'get_status' entry survived -- shipping_server's,")
print("  because it was processed last and silently overwrote")
print("  refund_server's identically-named entry in the same dict key.")
print("  A host decision step consulting this catalog has now lost all")
print("  ability to reach refund_server's own get_status tool at all.")


# ============================================================ 4
rule("4. THE FIX: NAMESPACE EVERY TOOL BY ITS OWNING SERVER")


class NamespacedHost:
    """[REAL] Aggregates using a 'server_name.tool_name' key -- the
    standard fix for exactly this collision, since MCP's own tools/list
    response (M9-L01) never guarantees uniqueness of a bare tool name
    ACROSS servers, only within one server's own catalog."""

    def __init__(self, clients: dict[str, Client]):
        self.clients = clients

    def aggregated_tools(self) -> dict[str, tuple[str, str]]:
        """Maps a namespaced key -> (server_name, bare tool_name)."""
        catalog: dict[str, tuple[str, str]] = {}
        for server_name, client in self.clients.items():
            for tool in client.list_tools():
                catalog[f"{server_name}.{tool['name']}"] = (server_name, tool["name"])
        return catalog

    def call(self, namespaced_name: str, arguments: dict):
        server_name, tool_name = self.aggregated_tools()[namespaced_name]
        return self.clients[server_name].call_tool(tool_name, arguments)


fixed_host = NamespacedHost({"refund_server": refund_client, "shipping_server": shipping_client})
fixed_catalog = fixed_host.aggregated_tools()
print(f"  Namespaced catalog: {list(fixed_catalog.keys())}")

refund_status = fixed_host.call("refund_server.get_status", {"order_id": "O-1"})
shipping_status = fixed_host.call("shipping_server.get_status", {"order_id": "O-1"})
print(f"\n  fixed_host.call('refund_server.get_status', ...)   -> {refund_status}")
print(f"  fixed_host.call('shipping_server.get_status', ...) -> {shipping_status}")

print("\n  Both servers' identically-named tools are now independently")
print("  reachable and correctly routed -- the collision from section 3 is")
print("  gone, not because either server changed anything, but because")
print("  the HOST's own aggregation now preserves which server each tool")
print("  actually came from. Per M9-L01, this aggregation and namespacing")
print("  scheme is entirely the host's own design choice -- MCP's")
print("  specification does not mandate any particular one.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: Server, Client, NaiveHost and NamespacedHost are genuinely")
print("  exercised above; the collision in section 3 and its fix in")
print("  section 4 are both measured, not asserted -- the naive catalog")
print("  really did lose an entry, and the namespaced one really did")
print("  preserve both.")
print("\n  ILLUSTRATIVE: real MCP hosts (e.g., an IDE or chat application)")
print("  manage client connections with considerably more machinery")
print("  (lifecycle, capability negotiation -- M9-L05) than this lab's")
print("  minimal classes show.")
print("\n  NOT SHOWN: the three MCP primitives beyond tools -- resources and")
print("  prompts (M9-L03); real transport connecting a client to a remote")
print("  server (M9-L08); and any authorization over which client may")
print("  reach which server (M9-L10 through M9-L13).")

print("\nDone.")
