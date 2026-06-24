"""Docker 项目检测器"""

import os
import re
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class DockerDetector(BaseDetector):
    NAME = "docker"
    CONFIG_FILES = ["Dockerfile", "Dockerfile.*", "docker-compose.yml", "docker-compose.yaml",
                    "compose.yml", "compose.yaml", ".dockerignore"]

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []
        deps.append(DepInfo(
            name="docker", dep_type=DepType.RUNTIME,
            install_command="请从 https://docker.com 下载 Docker Desktop",
            check_command="docker --version",
        ))

        compose_files = [f for f in matched_files if "compose" in f.lower()]
        for cf in compose_files:
            fpath = os.path.join(project_dir, cf)
            if os.path.isfile(fpath):
                try:
                    import yaml
                    data = yaml.safe_load(Path(fpath).read_text(encoding="utf-8", errors="ignore"))
                    services = data.get("services", {}) if data else {}
                    for svc_name, svc in services.items():
                        image = svc.get("image", "") if isinstance(svc, dict) else ""
                        deps.append(DepInfo(
                            name=f"服务: {svc_name}", dep_type=DepType.SERVICE,
                            version=image if image else "构建",
                            install_command=f"docker compose up {svc_name} -d",
                            check_command=f"docker compose ps {svc_name}",
                        ))
                except ImportError:
                    content = Path(fpath).read_text(encoding="utf-8", errors="ignore")
                    for m in re.finditer(r'^\s{2}(\w+):\s*$', content, re.MULTILINE):
                        deps.append(DepInfo(
                            name=f"服务: {m.group(1)}", dep_type=DepType.SERVICE,
                            install_command="docker compose up -d",
                        ))
                except Exception:
                    pass
        return deps
