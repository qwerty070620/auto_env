"""CV/Kaggle竞赛项目检测器"""

import os
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class JuliaDetector(BaseDetector):
    NAME = "julia"
    CONFIG_FILES = ["Project.toml", "Manifest.toml", "JuliaProject.toml"]

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []
        deps.append(DepInfo(
            name="julia", dep_type=DepType.RUNTIME,
            install_command="请从 https://julialang.org/downloads 安装 Julia",
            check_command="julia --version",
        ))

        proj = os.path.join(project_dir, "Project.toml")
        if os.path.isfile(proj):
            import re
            content = Path(proj).read_text(encoding="utf-8", errors="ignore")
            in_deps = False
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("[deps]"):
                    in_deps = True
                    continue
                if line.startswith("[") and in_deps:
                    in_deps = False
                if in_deps and "=" in line:
                    name = line.split("=")[0].strip()
                    deps.append(DepInfo(
                        name=name, dep_type=DepType.PACKAGE,
                        install_command=f'julia -e \'using Pkg; Pkg.add("{name}")\'',
                        check_command=f'julia -e "using {name}"',
                    ))
        return deps
