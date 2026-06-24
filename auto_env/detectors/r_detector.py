"""R 语言项目检测器"""

import os
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class RDetector(BaseDetector):
    NAME = "r"
    CONFIG_FILES = ["DESCRIPTION", "NAMESPACE", ".Rbuildignore",
                    "renv.lock", "packrat.lock"]

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []
        deps.append(DepInfo(
            name="r", dep_type=DepType.RUNTIME,
            install_command="请从 https://cran.r-project.org 下载安装 R",
            check_command="R --version",
        ))

        desc = os.path.join(project_dir, "DESCRIPTION")
        if os.path.isfile(desc):
            import re
            content = Path(desc).read_text(encoding="utf-8", errors="ignore")
            in_imports = False
            for line in content.splitlines():
                line = line.strip()
                if line.lower().startswith("imports:") or line.lower().startswith("depends:"):
                    in_imports = True
                    continue
                if in_imports and line and not line.startswith(" "):
                    in_imports = False
                if in_imports and line.startswith(" "):
                    pkg = line.split("(")[0].strip().rstrip(",")
                    if pkg and pkg not in ("R",):
                        deps.append(DepInfo(
                            name=pkg, dep_type=DepType.PACKAGE,
                            install_command=f"install.packages('{pkg}')",
                            check_command=f"R -e 'library({pkg})'",
                        ))
        return deps
