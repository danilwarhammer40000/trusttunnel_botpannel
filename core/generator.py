import subprocess
import os

TRUSTTUNNEL_DIR = "/opt/trusttunnel"


def resolve_endpoint_binary():
    """
    Priority:
    1. ENV (TRUSTTUNNEL_ENDPOINT_BIN)
    2. /opt/trusttunnel/trusttunnel_endpoint
    3. None (fallback mode)
    """

    # 1. ENV (highest priority)
    env_path = os.getenv("TRUSTTUNNEL_ENDPOINT_BIN")
    if env_path:
        env_path = os.path.abspath(env_path)
        if os.path.exists(env_path):
            return env_path

    # 2. Default server path
    server_path = os.path.join(TRUSTTUNNEL_DIR, "trusttunnel_endpoint")
    if os.path.exists(server_path):
        return server_path

    # 3. fallback
    return None


def generate_link(username: str, domain: str) -> str:
    binary_path = resolve_endpoint_binary()

    # -------------------------
    # FALLBACK MODE (DEV / NO BINARY)
    # -------------------------
    if binary_path is None:
        return f"https://{domain}/connect/{username}"

    # -------------------------
    # SAFETY CHECK
    # -------------------------
    if not os.path.isfile(binary_path):
        return f"https://{domain}/connect/{username}"

    # -------------------------
    # BUILD COMMAND
    # -------------------------
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

        # -------------------------
        # ERROR HANDLING
        # -------------------------
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            raise RuntimeError(f"TrustTunnel generator failed: {error_msg}")

        output = result.stdout.strip()

        if not output:
            raise RuntimeError("TrustTunnel returned empty output")

        return output

    except subprocess.TimeoutExpired:
        raise RuntimeError("TrustTunnel generator timeout (15s)")
    except Exception as e:
        # fallback safety (НЕ падаем ботом)
        return f"https://{domain}/connect/{username}"