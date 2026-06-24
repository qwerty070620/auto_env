"""Dart / Flutter 项目检测器"""

import os
import platform
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class DartDetector(BaseDetector):
    NAME = "dart"
    CONFIG_FILES = ["pubspec.yaml", "pubspec.lock", "analysis_options.yaml",
                    ".dart_tool", "flutter.yaml"]

    @classmethod
    def _parse_project_name(cls, project_dir: str, matched_files: list[str]) -> str:
        pubspec = os.path.join(project_dir, "pubspec.yaml")
        if os.path.isfile(pubspec):
            content = Path(pubspec).read_text(encoding="utf-8", errors="ignore")
            import re
            m = re.search(r'^name:\s*(\S+)', content, re.MULTILINE)
            if m:
                return m.group(1)
        return super()._parse_project_name(project_dir, matched_files)

    @classmethod
    def _detect_framework(cls, project_dir: str, matched_files: list[str]) -> str | None:
        pubspec = os.path.join(project_dir, "pubspec.yaml")
        if os.path.isfile(pubspec):
            content = Path(pubspec).read_text(encoding="utf-8", errors="ignore").lower()
            if "flutter" in content:
                return "Flutter"
        return None

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []
        grep = "findstr" if platform.system() == "Windows" else "grep"
        deps.append(DepInfo(
            name="dart", dep_type=DepType.RUNTIME,
            install_command="请从 https://dart.dev/get-dart 安装 Dart SDK (或安装 Flutter SDK 自带)",
            check_command="dart --version",
        ))

        pubspec = os.path.join(project_dir, "pubspec.yaml")
        if os.path.isfile(pubspec):
            content = Path(pubspec).read_text(encoding="utf-8", errors="ignore")
            import re
            in_deps = False
            for line in content.splitlines():
                line = line.rstrip()
                if re.match(r'^dependencies\s*:', line):
                    in_deps = True
                    continue
                if re.match(r'^dev_dependencies\s*:', line):
                    in_deps = True
                    continue
                if line and not line.startswith(" ") and not line.startswith("\t") and in_deps:
                    in_deps = False
                if in_deps and re.match(r'\s{2}(\w+):', line):
                    name = re.match(r'\s{2}(\w+):', line).group(1)
                    if name not in ("flutter", "sdk"):
                        deps.append(DepInfo(
                            name=name, dep_type=DepType.PACKAGE,
                            install_command=f"dart pub add {name}",
                            check_command=f"dart pub deps | {grep} {name}",
                        ))
        return deps
