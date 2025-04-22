# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportAttributeAccessIssue=false
import logging
import time
import uuid
from collections.abc import Generator, Iterable
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from python_on_whales import DockerClient
from python_on_whales.components.container.cli_wrapper import Container
from python_on_whales.exceptions import DockerException, NoSuchContainer
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.deps import get_db
from app.main import app

# Configure basic logging for tests
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Database Fixture (Overrides get_db dependency)
@pytest.fixture
def session() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]


# --- Helper Functions for Docker Fixture ---


def _get_container_host_port(docker: DockerClient, container_name: str) -> str | None:
    """Safely get the host port mapped to container port 8000."""
    host_port: str | None = None
    port_info: dict[str, str] | None = None
    try:
        inspected_container = docker.container.inspect(container_name)
        ports = inspected_container.network_settings.ports  # type: ignore[reportUnknownVariableType]
        if (
            ports
            and "8000/tcp" in ports
            and isinstance(ports["8000/tcp"], list)
            and len(ports["8000/tcp"]) > 0
        ):
            port_info = ports["8000/tcp"][0]
            if port_info:
                host_port = port_info.get("HostPort")

    except (AttributeError, KeyError, IndexError, TypeError, DockerException) as e:
        logger.warning("Error extracting host port for %s: %s", container_name, e)
        return None
    else:
        if host_port:
            return host_port
        logger.warning("Port 8000/tcp not found/mapped in %s.", container_name)
        return None


def _wait_for_server_ready(base_url: str, max_wait: int = 30) -> None:
    """Wait for the server at base_url to become responsive."""
    start_time = time.time()
    check_url = f"{base_url}/docs"
    logger.info("Checking server readiness at %s...", check_url)
    with httpx.Client(timeout=max_wait + 5.0) as client:
        while time.time() - start_time < max_wait:
            try:
                response = client.get(check_url, timeout=2.0)
                response.raise_for_status()
            except httpx.HTTPStatusError as status_err:
                logger.warning(
                    "Health check %s failed: Status %s. Retrying...",
                    check_url,
                    status_err.response.status_code,
                )
            except (
                httpx.ConnectError,
                httpx.TimeoutException,
                httpx.ReadTimeout,
            ) as http_err:
                logger.info(
                    "Server at %s not ready yet (%s), waiting...",
                    check_url,
                    http_err.__class__.__name__,
                )
            except Exception:
                logger.exception("Unexpected health check error for %s", check_url)
            else:
                logger.info("Server at %s is ready.", base_url)
                return
            time.sleep(1)

    pytest.fail(f"Server at {base_url} did not become ready within {max_wait} seconds.")


def _log_container_output(container: Container, container_name: str) -> None:
    """Logs the output of a given Docker container."""
    assert container is not None
    container_id = container.id  # type: ignore[reportAttributeAccessIssue]
    logger.info(
        "--- Container logs for %s (%s) ---",
        container_name,
        container_id,
    )
    try:
        logs = container.logs()
        logger.info("Container Logs:\n%s", logs)
    except DockerException as log_err:
        logger.warning(
            "Warning: Failed to retrieve logs for %s: %s",
            container_name,
            log_err,
        )
    except Exception:
        logger.exception(
            "Warning: Unexpected error retrieving logs for %s", container_name
        )
    logger.info("--- End logs for %s (%s) ---", container_name, container_id)


def _cleanup_container(
    docker: DockerClient, container: Container | None, container_name: str
) -> None:
    """Stop and remove the specified Docker container, handling errors."""
    if container:
        assert container is not None
        _log_container_output(container, container_name)

        logger.info(
            "Stopping and removing container %s (%s)...",
            container_name,
            container.id,  # type: ignore[reportAttributeAccessIssue]
        )
        try:
            container.stop()
            logger.info("Container %s stopped.", container_name)
        except NoSuchContainer:
            logger.warning(
                "Container %s already removed or failed to start.", container_name
            )
        except DockerException:
            logger.exception("Error stopping container %s", container_name)

    elif container_name:
        # Attempt cleanup by name if container object wasn't assigned or lost
        logger.info("Attempting cleanup by name for %s", container_name)
        try:
            running_container = docker.container.inspect(container_name)
            if running_container:
                logger.warning(
                    "Container obj lost, attempting cleanup by name: %s",
                    container_name,
                )
                docker.container.stop(container_name)
                docker.container.remove(container_name)
                logger.info("Cleaned up container by name: %s", container_name)
        except NoSuchContainer:
            logger.info("Container %s not found for cleanup by name.", container_name)
        except DockerException:
            logger.exception(
                "Error during cleanup by name for container %s", container_name
            )
        except Exception:
            logger.exception(
                "Unexpected error during cleanup by name for %s", container_name
            )


# --- Docker Fixtures ---


@pytest.fixture(scope="session")
def docker() -> DockerClient:
    """Provide a Docker client, checking if the daemon is running."""
    client = None
    try:
        client = DockerClient()
        client.system.info()
    except DockerException as e:
        pytest.fail(
            f"Docker daemon not running or inaccessible: {e}. "
            "Please ensure Docker is installed and running."
        )
    else:
        return client


@pytest.fixture(scope="session")
def docker_image(docker: DockerClient) -> Generator[str, None, None]:
    """Build the Docker image for the backend app once per session."""
    image_tag = f"captioner-backend-test:{uuid.uuid4()}"
    logger.info("Building Docker image: %s...", image_tag)
    built_image_obj = None
    try:
        project_root = Path(__file__).parent.parent
        built_image_obj = docker.build(context_path=project_root, tags=image_tag)
        if built_image_obj and built_image_obj.id:
            logger.info("Docker image built: %s", built_image_obj.id)
        else:
            logger.warning("Docker image built but ID is missing: %s", image_tag)
        yield image_tag
    except DockerException as e:
        pytest.fail(f"Docker build failed: {e}")
    except Exception as e:
        logger.exception("An unexpected error occurred during Docker build.")
        pytest.fail(f"An unexpected error occurred during Docker build: {e}")
    finally:
        if image_tag:
            try:
                logger.info("Removing Docker image: %s...", image_tag)
                docker.image.remove(image_tag, force=True)
                logger.info("Docker image removed: %s", image_tag)
            except DockerException as e:
                logger.warning("Failed to remove Docker image %s: %s", image_tag, e)


@pytest.fixture
def live_server_url(
    docker: DockerClient, docker_image: str
) -> Generator[str, None, None]:
    """Start the backend app in a Docker container for a test function."""
    container_run_result: Container | str | Iterable[tuple[str, bytes]] | None = None
    container: Container | None = None
    container_name = f"captioner-test-container-{uuid.uuid4()}"
    base_url: str | None = None

    try:
        logger.info(
            "Starting container '%s' from image '%s'...", container_name, docker_image
        )
        container_run_result = docker.run(
            image=docker_image,
            detach=True,
            publish=[(8000,)],
            remove=False,
            name=container_name,
        )

        if not isinstance(container_run_result, Container):
            logger.error(
                "docker.run did not return a Container object. Result: %s",
                type(container_run_result),
            )
            pytest.fail("Failed to start container properly.")
        else:
            container = container_run_result

        host_port_str = _get_container_host_port(docker, container_name)
        if not host_port_str:
            pytest.fail(f"Could not determine host port for container {container_name}")

        base_url = f"http://localhost:{host_port_str}"
        logger.info("Container %s started, accessible at %s", container_name, base_url)

        _wait_for_server_ready(base_url)

        yield base_url

    except DockerException:
        logger.exception("Docker error during container setup for %s", container_name)
        pytest.fail(f"Docker error for container {container_name}")
    except Exception:
        logger.exception("Unexpected error setting up container %s", container_name)
        pytest.fail(f"Unexpected error setting up container {container_name}")

    finally:
        _cleanup_container(docker, container, container_name)
