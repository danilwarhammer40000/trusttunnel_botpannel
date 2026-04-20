import subprocess
import os

TRUSTTUNNEL_DIR = "/opt/trusttunnel"


def generate_link(username, domain):
    binary_path = os.path.join(TRUSTTUNNEL_DIR, "trusttunnel_endpoint")

    if not os.path.exists(binary_path):
        raise FileNotFoundError("trusttunnel_endpoint not found")

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
            cwd=TRUSTTUNNEL_DIR,
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())

        output = result.stdout.strip()

        # 👉 ВАЖНО: возвращаем ПОЛНЫЙ блок
        return output

    except subprocess.TimeoutExpired:
        raise RuntimeError("Generator timeout")