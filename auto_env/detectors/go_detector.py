"""Go 项目检测器"""

import os
import re
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class GoDetector(BaseDetector):
    NAME = "go"
    CONFIG_FILES = ["go.mod", "go.sum"]

    @classmethod
    def _parse_project_name(cls, project_dir: str, matched_files: list[str]) -> str:
        gomod = os.path.join(project_dir, "go.mod")
        if os.path.isfile(gomod):
            content = Path(gomod).read_text(encoding="utf-8", errors="ignore")
            m = re.search(r'^module\s+(\S+)', content, re.MULTILINE)
            if m:
                return m.group(1)
        return super()._parse_project_name(project_dir, matched_files)

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []

        deps.append(DepInfo(
            name="go",
            dep_type=DepType.RUNTIME,
            install_command="请从 https://go.dev/dl/ 下载安装 Go",
            check_command="go version",
        ))

        gomod = os.path.join(project_dir, "go.mod")
        if os.path.isfile(gomod):
            content = Path(gomod).read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
            in_require = False
            for line in lines:
                line = line.strip()
                if line.startswith("require ("):
                    in_require = True
                    continue
                elif line.startswith(")") and in_require:
                    in_require = False
                    continue
                elif line.startswith("require ") and not in_require:
                    # 单行 require
                    parts = line.split()
                    if len(parts) >= 3:
                        name = parts[1]
                        version = parts[2]
                        deps.append(DepInfo(
                            name=name,
                            dep_type=DepType.PACKAGE,
                            version=version,
                            install_command=f"go get {name}@{version}",
                            check_command=f"go list -m {name}",
                        ))
                elif in_require:
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        version = parts[1]
                        deps.append(DepInfo(
                            name=name,
                            dep_type=DepType.PACKAGE,
                            version=version,
                            install_command=f"go get {name}@{version}",
                            check_command=f"go list -m {name}",
                        ))

        return deps
