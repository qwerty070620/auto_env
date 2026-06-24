"""基础检测器 - 所有语言检测器的抽象基类"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from pathlib import Path
import os
import glob as _glob
import fnmatch


class DepType(Enum):
    """依赖类型"""
    RUNTIME = "runtime"           # 运行时（如 Node.js、Python 解释器）
    PACKAGE = "package"           # 包依赖（如 requests, express）
    SYSTEM = "system"             # 系统级（如 ffmpeg, openssl）
    SERVICE = "service"           # 外部服务（如 Redis, PostgreSQL）
    BUILD_TOOL = "build_tool"     # 构建工具（如 gcc, cargo）


@dataclass
class DepInfo:
    """单个依赖信息"""
    name: str                           # 包名/工具名
    dep_type: DepType                   # 依赖类型
    version: Optional[str] = None       # 需要的版本
    install_command: Optional[str] = None   # 安装命令
    check_command: Optional[str] = None     # 检查是否已安装的命令
    is_installed: bool = False          # 是否已安装


@dataclass
class DetectionResult:
    """检测结果"""
    project_type: str = ""              # 项目类型：python / nodejs / rust / ...
    project_name: str = ""              # 项目名称
    framework: Optional[str] = None     # 框架：Django, React, Spring Boot...
    deps: list[DepInfo] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class BaseDetector(ABC):
    """检测器基类 — 支持精确匹配和通配符 glob 模式"""

    # 子类必须定义的属性
    NAME: str = ""                      # 检测器名称
    CONFIG_FILES: list[str] = []        # 标识性配置文件（支持 * 通配符，匹配任一即触发）
    EXCLUDE_FILES: list[str] = []       # 排除文件

    @classmethod
    def detect(cls, project_dir: str) -> Optional[DetectionResult]:
        """
        扫描项目目录，判断是否匹配此检测器。
        支持精确文件名和 glob 通配符（如 *.tf / *.csproj）。
        返回 DetectionResult 或 None（不匹配）。
        """
        matched_files: list[str] = []

        for pattern in cls.CONFIG_FILES:
            # 判断是否包含通配符
            if any(c in pattern for c in "*?["):
                for fpath in _glob.glob(os.path.join(project_dir, pattern)):
                    fname = os.path.basename(fpath)
                    if os.path.isfile(fpath) and fname not in matched_files:
                        matched_files.append(fname)
            else:
                fpath = os.path.join(project_dir, pattern)
                if os.path.isfile(fpath):
                    matched_files.append(pattern)

        # 去重并排除（支持 glob 模式）
        def _matches_exclude(fname: str) -> bool:
            for exclude_pattern in cls.EXCLUDE_FILES:
                if any(c in exclude_pattern for c in "*?["):
                    if fnmatch.fnmatch(fname, exclude_pattern):
                        return True
                elif fname == exclude_pattern:
                    return True
            return False
        matched_files = [f for f in matched_files if not _matches_exclude(f)]
        matched_files = sorted(set(matched_files))

        if not matched_files:
            return None

        result = DetectionResult(
            project_type=cls.NAME,
            config_files=matched_files,
        )

        # 解析项目名
        try:
            result.project_name = cls._parse_project_name(project_dir, matched_files)
        except Exception:
            result.project_name = os.path.basename(os.path.abspath(project_dir))

        # 解析依赖
        try:
            result.deps = cls._parse_deps(project_dir, matched_files)
        except Exception as e:
            result.notes.append(f"依赖解析出错: {e}")

        # 检测框架
        try:
            result.framework = cls._detect_framework(project_dir, matched_files)
        except Exception:
            pass

        return result

    @classmethod
    @abstractmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        """解析项目依赖列表"""
        ...

    @classmethod
    def _parse_project_name(cls, project_dir: str, matched_files: list[str]) -> str:
        """解析项目名，默认用目录名"""
        return os.path.basename(os.path.abspath(project_dir))

    @classmethod
    def _detect_framework(cls, project_dir: str, matched_files: list[str]) -> Optional[str]:
        """检测使用的框架"""
        return None
