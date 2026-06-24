"""Elixir / Erlang 项目检测器"""

import os
import platform
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class ElixirDetector(BaseDetector):
    NAME = "elixir"
    CONFIG_FILES = ["mix.exs", "mix.lock", "rebar.config", "rebar.lock"]

    @classmethod
    def _parse_project_name(cls, project_dir: str, matched_files: list[str]) -> str:
        mix = os.path.join(project_dir, "mix.exs")
        if os.path.isfile(mix):
            content = Path(mix).read_text(encoding="utf-8", errors="ignore")
            import re
            m = re.search(r'app:\s*:(\w+)', content)
            if m:
                return m.group(1)
        return super()._parse_project_name(project_dir, matched_files)

    @classmethod
    def _detect_framework(cls, project_dir: str, matched_files: list[str]) -> str | None:
        mix = os.path.join(project_dir, "mix.exs")
        if os.path.isfile(mix):
            content = Path(mix).read_text(encoding="utf-8", errors="ignore").lower()
            if "phoenix" in content:
                return "Phoenix"
            if "nerves" in content:
                return "Nerves"
        return None

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []
        grep = "findstr" if platform.system() == "Windows" else "grep"
        deps.append(DepInfo(
            name="elixir", dep_type=DepType.RUNTIME,
            install_command="请从 https://elixir-lang.org/install.html 安装 Elixir (自带 Erlang)",
            check_command="elixir --version",
        ))

        has_mix = any("mix" in f for f in matched_files)
        if has_mix:
            deps.append(DepInfo(
                name="mix", dep_type=DepType.BUILD_TOOL,
                install_command="Elixir 自带",
                check_command="mix --version",
            ))
            mix_exs = os.path.join(project_dir, "mix.exs")
            if os.path.isfile(mix_exs):
                import re
                content = Path(mix_exs).read_text(encoding="utf-8", errors="ignore")
                # {:package, "~> 1.0"}
                for m in re.finditer(r'\{:(\w+)\s*,\s*"[^"]*"', content):
                    name = m.group(1)
                    if name not in ("path", "git", "in_umbrella", "only", "optional", "runtime"):
                        deps.append(DepInfo(
                            name=name, dep_type=DepType.PACKAGE,
                            install_command=f"mix deps.get",
                            check_command=f"mix deps | {grep} {name}",
                        ))
        return deps
