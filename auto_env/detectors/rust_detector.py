"""Rust 项目检测器"""

import os
import platform
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class RustDetector(BaseDetector):
    NAME = "rust"
    CONFIG_FILES = ["Cargo.toml", "Cargo.lock"]

    @classmethod
    def _parse_project_name(cls, project_dir: str, matched_files: list[str]) -> str:
        cargo = os.path.join(project_dir, "Cargo.toml")
        if os.path.isfile(cargo):
            content = Path(cargo).read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("name") and "=" in line:
                    name = line.split("=", 1)[1].strip().strip('"').strip("'")
                    return name
        return super()._parse_project_name(project_dir, matched_files)

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []
        grep = "findstr" if platform.system() == "Windows" else "grep"

        deps.append(DepInfo(
            name="rust",
            dep_type=DepType.RUNTIME,
            install_command="请从 https://rustup.rs 安装 Rust",
            check_command="rustc --version",
        ))
        deps.append(DepInfo(
            name="cargo",
            dep_type=DepType.BUILD_TOOL,
            install_command="随 Rust 安装",
            check_command="cargo --version",
        ))

        cargo = os.path.join(project_dir, "Cargo.toml")
        if os.path.isfile(cargo):
            content = Path(cargo).read_text(encoding="utf-8", errors="ignore")
            in_deps = False
            in_build_deps = False
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("[dependencies]"):
                    in_deps = True
                    continue
                elif line.startswith("[build-dependencies]"):
                    in_build_deps = True
                    in_deps = False
                    continue
                elif line.startswith("[") and (in_deps or in_build_deps):
                    in_deps = False
                    in_build_deps = False

                if (in_deps or in_build_deps) and "=" in line and not line.startswith("#"):
                    name = line.split("=")[0].strip().strip('"')
                    ver_part = line.split("=", 1)[1].strip().strip('"')
                    # 提取版本号
                    import re
                    m = re.search(r'(\d+\.\d+[^\s,"]*)', ver_part)
                    version = m.group(1) if m else None
                    deps.append(DepInfo(
                        name=name,
                        dep_type=DepType.PACKAGE,
                        version=version,
                        install_command=f"cargo add {name}",
                        check_command=f"cargo tree | {grep} {name}",
                    ))

        return deps
