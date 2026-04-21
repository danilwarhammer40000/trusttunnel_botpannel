import subprocess
import os

TRUSTTUNNEL_DIR = "/opt/trusttunnel"


# -------------------------
# RESOLVE BINARY
# -------------------------
def resolve_endpoint_binary():
    """
    Priority:
    1. ENV TRUSTTUNNEL_ENDPOINT_BIN
    2. /opt/trusttunnel/trusttunnel_endpoint
    3. None (fallback mode)
    """

    env_path = os.getenv("TRUSTTUNNEL_ENDPOINT_BIN")
    if env_path:
        env_path = os.path.abspath(env_path)
        if os.path.isfile(env_path):
            return env_path

    server_path = os.path.join(TRUSTTUNNEL_DIR, "trusttunnel_endpoint")
    if os.path.isfile(server_path):
        return server_path

    return None


# -------------------------
# DOMAIN VALIDATION
# -------------------------
def validate_domain(domain: str):
    if not domain:
        raise ValueError("Domain is empty")

    # простая защита от мусора
    if " " in domain or domain.startswith("http"):
        raise ValueError(f"Invalid domain: {domain}")


# -------------------------
# GENERATE LINK
# -------------------------
def generate_link(username: str, domain: str) -> str:
    validate_domain(domain)

    binary_path = resolve_endpoint_binary()

    # -------------------------
    # FALLBACK MODE
    # -------------------------
    if not binary_path:
        return f"https://{domain}/connect/{username}"

    if not os.path.isfile(binary_path):
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
            # НЕ скрываем ошибку полностью
            raise RuntimeError(result.stderr.strip())

        output = result.stdout.strip()

        if not output:
            raise RuntimeError("Empty TrustTunnel output")

        return output

    except subprocess.TimeoutExpired:
        raise RuntimeError("TrustTunnel timeout (15s)")

    except Exception as e:
        # fallback только если всё сломалось полностью
        return f"https://{domain}/connect/{username}"