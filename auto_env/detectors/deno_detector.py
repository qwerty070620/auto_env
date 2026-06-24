"""Deno 项目检测器"""

import os
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class DenoDetector(BaseDetector):
    NAME = "deno"
    CONFIG_FILES = ["deno.json", "deno.jsonc", "deno.lock",
                    "import_map.json", "import-map.json", "deps.ts"]

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []
        deps.append(DepInfo(
            name="deno", dep_type=DepType.RUNTIME,
            install_command="请从 https://deno.com 安装 Deno，或 choco install deno",
            check_command="deno --version",
        ))

        # 解析 deno.json / deno.jsonc 中的 import map
        import json
        for fname in ["deno.json", "deno.jsonc", "import_map.json", "import-map.json"]:
            fpath = os.path.join(project_dir, fname)
            if os.path.isfile(fpath):
                try:
                    content = Path(fpath).read_text(encoding="utf-8-sig")
                    # jsonc 注释剥离 — 仅移除行内 // 注释，保护 URL (L5)
                    if "//" in content:
                        import re
                        # 仅移除引号外的 //，避免误删 URL
                        content = re.sub(r'(?<!:)//.*', '', content)
                    data = json.loads(content)
                    imports = data.get("imports", data.get("import_map", {}))
                    if isinstance(imports, dict):
                        for alias, url in imports.items():
                            if isinstance(url, str) and not alias.startswith("@"):
                                deps.append(DepInfo(
                                    name=alias, dep_type=DepType.PACKAGE,
                                    version=url,
                                ))
                except Exception:
                    pass

        # deps.ts
        deps_ts = os.path.join(project_dir, "deps.ts")
        if os.path.isfile(deps_ts):
            import re
            content = Path(deps_ts).read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r'export\s+\*\s+from\s+"([^"]+)"', content):
                url = m.group(1)
                name = url.split("/")[-1].replace(".ts", "").replace(".js", "")
                deps.append(DepInfo(
                    name=url.split("/")[-2] if "/" in url else name,
                    dep_type=DepType.PACKAGE,
                    version=url,
                ))
        return deps
