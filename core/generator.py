import subprocess
import os
import re

# FIX: unify with installer path
TRUSTTUNNEL_DIR = "/opt/trustpanel"


# -------------------------
# RESOLVE BINARY
# -------------------------
def resolve_endpoint_binary():
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
# DOMAIN VALIDATION (HARDENED)
# -------------------------
def validate_domain(domain: str):
    if not domain:
        raise ValueError("Domain is empty")

    domain = domain.strip()

    # block obvious injections
    if any(x in domain for x in [" ", ";", "&", "|", "$", "`"]):
        raise ValueError("Invalid domain (suspicious chars)")

    if domain.startswith("http://") or domain.startswith("https://"):
        raise ValueError("Domain must not include scheme")

    # RFC-ish simple validation
    if not re.match(r"^[a-zA-Z0-9.-]+$", domain):
        raise ValueError("Invalid domain format")


# -------------------------
# GENERATE LINK
# -------------------------
def generate_link(username: str, domain: str) -> str:
    validate_domain(domain)

    binary_path = resolve_endpoint_binary()

    fallback_url = f"https://{domain}/connect/{username}"

    # fallback if binary missing
    if not binary_path:
        return fallback_url

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
            timeout=15,
            env={"PATH": "/usr/bin:/bin"}
        )

        if result.returncode != 0:
            # loggable error but safe fallback
            print(f"[generator error] {result.stderr.strip()}")
            return fallback_url

        output = result.stdout.strip()

        if not output:
            print("[generator warning] empty output from endpoint")
            return fallback_url

        return output

    except subprocess.TimeoutExpired:
        print("[generator timeout]")
        return fallback_url

    except Exception as e:
        print(f"[generator exception] {str(e)}")
        return fallback_url
