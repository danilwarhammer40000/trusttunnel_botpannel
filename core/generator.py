import subprocess
import os

TRUSTTUNNEL_DIR = "/opt/trusttunnel"


def resolve_endpoint_binary():
    """
    1. ENV (TRUSTTUNNEL_ENDPOINT_BIN)
    2. /opt/trusttunnel/trusttunnel_endpoint
    3. None (fallback)
    """

    # 1. ENV (самый приоритетный)
    env_path = os.getenv("TRUSTTUNNEL_ENDPOINT_BIN")
    if env_path and os.path.exists(env_path):
        return env_path

    # 2. Серверный путь
    server_path = os.path.join(TRUSTTUNNEL_DIR, "trusttunnel_endpoint")
    if os.path.exists(server_path):
        return server_path

    # 3. fallback
    return None


def generate_link(username, domain):
    binary_path = resolve_endpoint_binary()

    # 👉 FALLBACK режим (разработка / Windows)
    if binary_path is None:
        # можно лог добавить
        return f"https://{domain}/connect/{username}"

    cmd = [
        binary_path,
        "vpn.toml",
        "hosts.toml",
        "-c", username,
        "-a", domain
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(binary_path),
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode != 0:
            raise RuntimeError(f"Generator error: {result.stderr.strip()}")

        output = result.stdout.strip()

        if not output:
            raise RuntimeError("Empty generator output")

        return output

    except subprocess.TimeoutExpired:
        raise RuntimeError("Generator timeout")