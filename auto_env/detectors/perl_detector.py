"""Perl 项目检测器"""

import os
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class PerlDetector(BaseDetector):
    NAME = "perl"
    CONFIG_FILES = ["Makefile.PL", "Build.PL", "cpanfile", "META.json",
                    "META.yml", "MYMETA.json", "MYMETA.yml", "dist.ini"]

    @classmethod
    def _parse_project_name(cls, project_dir: str, matched_files: list[str]) -> str:
        meta = os.path.join(project_dir, "META.json")
        if os.path.isfile(meta):
            import json
            try:
                data = json.loads(Path(meta).read_text(encoding="utf-8", errors="ignore"))
                return data.get("name", "") or super()._parse_project_name(project_dir, matched_files)
            except Exception:
                pass
        return super()._parse_project_name(project_dir, matched_files)

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []
        deps.append(DepInfo(
            name="perl", dep_type=DepType.RUNTIME,
            install_command="Linux/macOS 通常自带；Windows 请从 https://strawberryperl.com 安装",
            check_command="perl --version",
        ))

        # cpanfile
        cpanfile = os.path.join(project_dir, "cpanfile")
        if os.path.isfile(cpanfile):
            import re
            content = Path(cpanfile).read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r"requires\s+'([^']+)'\s*,\s*'([^']*)'", content):
                deps.append(DepInfo(
                    name=m.group(1), dep_type=DepType.PACKAGE,
                    version=m.group(2),
                    install_command=f"cpanm {m.group(1)}",
                    check_command=f"perl -M{m.group(1)} -e 1",
                ))

        # Makefile.PL
        makefile_pl = os.path.join(project_dir, "Makefile.PL")
        if os.path.isfile(makefile_pl):
            content = Path(makefile_pl).read_text(encoding="utf-8", errors="ignore")
            import re
            for m in re.finditer(r"'([^']+)'\s*=>\s*'([^']*)'", content):
                deps.append(DepInfo(
                    name=m.group(1), dep_type=DepType.PACKAGE,
                    version=m.group(2) if m.group(2) != "0" else None,
                    install_command=f"cpanm {m.group(1)}",
                ))
        return deps
