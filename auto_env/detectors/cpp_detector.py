"""C/C++ 项目检测器 (CMake / Makefile / Meson)"""

import os
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class CppDetector(BaseDetector):
    NAME = "cpp"
    CONFIG_FILES = [
        "CMakeLists.txt",
        "Makefile",
        "makefile",
        "GNUmakefile",
        "meson.build",
        "configure",
        "configure.ac",
        "SConstruct",
    ]

    @classmethod
    def _detect_framework(cls, project_dir: str, matched_files: list[str]) -> str | None:
        matched_set = set(matched_files)
        if "CMakeLists.txt" in matched_set:
            # 检查是否 Qt 项目
            cmake = os.path.join(project_dir, "CMakeLists.txt")
            content = Path(cmake).read_text(encoding="utf-8", errors="ignore")
            if "Qt" in content:
                return "Qt"
            return "CMake"
        if any(f in matched_set for f in ["meson.build"]):
            return "Meson"
        if any(f in matched_set for f in ["Makefile", "makefile", "GNUmakefile"]):
            return "Make"
        return None

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []

        # 构建工具
        matched_set = set(matched_files)
        if "CMakeLists.txt" in matched_set:
            deps.append(DepInfo(
                name="cmake",
                dep_type=DepType.BUILD_TOOL,
                install_command="请从 https://cmake.org 下载安装 CMake，或用 pip install cmake / choco install cmake",
                check_command="cmake --version",
            ))
        if any(f in matched_set for f in ["meson.build"]):
            deps.append(DepInfo(
                name="meson",
                dep_type=DepType.BUILD_TOOL,
                install_command="pip install meson ninja",
                check_command="meson --version",
            ))
            deps.append(DepInfo(
                name="ninja",
                dep_type=DepType.BUILD_TOOL,
                install_command="pip install ninja 或 choco install ninja",
                check_command="ninja --version",
            ))

        # C/C++ 编译器
        deps.append(DepInfo(
            name="gcc",
            dep_type=DepType.BUILD_TOOL,
            install_command="Windows: 安装 MinGW-w64 或 MSYS2; Linux: sudo apt install build-essential; macOS: xcode-select --install",
            check_command="gcc --version",
        ))

        # 解析 CMakeLists.txt 中的依赖
        cmake = os.path.join(project_dir, "CMakeLists.txt")
        if os.path.isfile(cmake):
            content = Path(cmake).read_text(encoding="utf-8", errors="ignore")
            import re

            # find_package(...)
            for m in re.finditer(r'find_package\s*\(\s*(\w+)', content):
                pkg = m.group(1)
                if pkg not in ("REQUIRED", "QUIET", "CONFIG"):
                    deps.append(DepInfo(
                        name=pkg,
                        dep_type=DepType.PACKAGE,
                        install_command=f"请安装 {pkg} 开发库 (apt install / brew install / vcpkg install)",
                        check_command=f"pkg-config --exists {pkg.lower()}",
                    ))

            # FetchContent / ExternalProject
            for m in re.finditer(r'FetchContent_Declare\s*\(\s*(\w+)', content):
                deps.append(DepInfo(
                    name=m.group(1),
                    dep_type=DepType.PACKAGE,
                    install_command=f"CMake FetchContent 自动下载",
                ))

        return deps
