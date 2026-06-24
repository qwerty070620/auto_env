"""Haskell 项目检测器"""

import os
import re
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class HaskellDetector(BaseDetector):
    NAME = "haskell"
    CONFIG_FILES = ["stack.yaml", "stack.yaml.lock", "*.cabal",
                    "cabal.project", "cabal.project.freeze", "hie.yaml"]

    @classmethod
    def detect(cls, project_dir: str):
        return super().detect(project_dir)

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []
        deps.append(DepInfo(
            name="ghc", dep_type=DepType.RUNTIME,
            install_command="请从 https://haskell.org/ghcup 安装 GHCup (含 GHC + Cabal)",
            check_command="ghc --version",
        ))

        has_stack = any("stack" in f for f in matched_files)
        if has_stack:
            deps.append(DepInfo(
                name="stack", dep_type=DepType.BUILD_TOOL,
                install_command="ghcup install stack 或从 https://haskellstack.org 安装",
                check_command="stack --version",
            ))

        # 解析 .cabal 文件中的依赖
        import re
        cabal_files = [f for f in matched_files if f.endswith(".cabal")]
        if not cabal_files:
            cabal_files = [f.name for f in Path(project_dir).glob("*.cabal")]
        for cf in cabal_files:
            fpath = os.path.join(project_dir, cf)
            if os.path.isfile(fpath):
                content = Path(fpath).read_text(encoding="utf-8", errors="ignore")
                for m in re.finditer(r'build-depends:\s*(.*)', content):
                    pkgs = m.group(1).split(",")
                    for pkg in pkgs:
                        pkg = pkg.strip()
                        if pkg:
                            name = pkg.split()[0] if pkg.split() else pkg
                            deps.append(DepInfo(
                                name=name, dep_type=DepType.PACKAGE,
                                install_command=f"cabal install {name}",
                            ))
        return deps
