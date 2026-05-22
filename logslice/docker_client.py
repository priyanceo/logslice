"""Docker container log fetching and streaming utilities."""

from __future__ import annotations

import docker
from docker.errors import DockerException, NotFound
from typing import Generator, Optional


class DockerClientError(Exception):
    """Raised when Docker client operations fail."""


class DockerLogClient:
    """Thin wrapper around the Docker SDK for container log access."""

    def __init__(self) -> None:
        try:
            self._client = docker.from_env()
        except DockerException as exc:
            raise DockerClientError(
                "Failed to connect to Docker daemon. Is Docker running?"
            ) from exc

    def list_containers(self, all: bool = False) -> list[dict]:
        """Return a list of containers with id, name, status, and image."""
        containers = self._client.containers.list(all=all)
        return [
            {
                "id": c.short_id,
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else c.image.short_id,
            }
            for c in containers
        ]

    def stream_logs(
        self,
        container_name: str,
        tail: int = 100,
        follow: bool = False,
        since: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """Yield log lines from the specified container."""
        try:
            container = self._client.containers.get(container_name)
        except NotFound:
            raise DockerClientError(f"Container '{container_name}' not found.")

        kwargs: dict = {
            "stream": True,
            "follow": follow,
            "tail": tail,
            "timestamps": True,
        }
        if since is not None:
            kwargs["since"] = since

        log_stream = container.logs(**kwargs)
        for chunk in log_stream:
            yield chunk.decode("utf-8", errors="replace").rstrip("\n")

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "DockerLogClient":
        return self

    def __exit__(self, *_) -> None:
        self.close()
