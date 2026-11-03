import os
from pathlib import Path


root = Path(__file__).resolve().parent
root.joinpath("data/mysql").mkdir(parents=True, exist_ok=True)

manifests = (
    (
        root / "mysql/mysql-local-data-folder-pv.yaml.in",
        root / "mysql/mysql-local-data-folder-pv.yaml",
        "__MYSQL_DATA_PATH__",
        Path(os.environ.get("MYSQL_DATA_PATH", root / "data/mysql")),
    ),
    (
        root / "test/fastapi-pod.yaml.in",
        root / "test/fastapi-pod.yaml",
        "__FASTAPI_APP_PATH__",
        Path(os.environ.get("FASTAPI_APP_PATH", root / "test/app")),
    ),
)

for template_path, manifest_path, marker, host_path in manifests:
    if not host_path.is_absolute():
        raise SystemExit(f"{host_path} must be an absolute path on the Kubernetes node")
    template = template_path.read_text()
    if marker not in template:
        raise SystemExit(f"Missing {marker} in {template_path}")
    manifest_path.write_text(template.replace(marker, str(host_path)))
