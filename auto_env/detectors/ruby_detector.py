"""Ruby 项目检测器"""

import os
import platform
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class RubyDetector(BaseDetector):
    NAME = "ruby"
    CONFIG_FILES = ["Gemfile", "Gemfile.lock", ".ruby-version", "*.gemspec"]

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []
        grep = "findstr" if platform.system() == "Windows" else "grep"

        deps.append(DepInfo(
            name="ruby",
            dep_type=DepType.RUNTIME,
            install_command="请从 https://ruby-lang.org 下载安装 Ruby",
            check_command="ruby --version",
        ))
        deps.append(DepInfo(
            name="bundler",
            dep_type=DepType.BUILD_TOOL,
            install_command="gem install bundler",
            check_command="bundler --version",
        ))

        gemfile = os.path.join(project_dir, "Gemfile")
        if os.path.isfile(gemfile):
            content = Path(gemfile).read_text(encoding="utf-8", errors="ignore")
            import re
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("#") or not line.startswith("gem"):
                    continue
                # gem "rails", "~> 7.0"
                m = re.search(r'gem\s+["\']([^"\']+)["\']\s*[,]?\s*["\']?([^"\']*)', line)
                if m:
                    name = m.group(1)
                    version = m.group(2).strip().strip("'").strip('"') if m.group(2) else None
                    deps.append(DepInfo(
                        name=name,
                        dep_type=DepType.PACKAGE,
                        version=version if version else None,
                        install_command=f"bundle add {name}",
                        check_command=f"bundle list | {grep} {name}",
                    ))

        return deps
