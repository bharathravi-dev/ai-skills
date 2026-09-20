# A stdio MCP server in a container (M9-L16).
# Build:  docker build -t mcp-catalog:lab labs/m9/l09_catalog_server
# Run:    docker run -i --rm --network none --read-only mcp-catalog:lab
# The host launches this with `docker run -i ...` as the command; stdin/stdout
# are the transport, so the container must not print anything else to stdout.
FROM python:3.12-slim

# Run as a non-root user: an MCP server executes model-chosen actions.
RUN useradd --create-home --uid 10001 mcp
WORKDIR /srv
COPY server.py /srv/server.py
USER mcp

# No dependencies to install: this server is standard library only.
# -u keeps stdout unbuffered so responses are not held in a pipe buffer.
ENTRYPOINT ["python", "-u", "/srv/server.py"]
