"""AutoEnv 检测器模块 - 自动识别项目类型和依赖"""

from .base import BaseDetector, DetectionResult, DepInfo
from .python_detector import PythonDetector
from .nodejs_detector import NodeJSDetector
from .rust_detector import RustDetector
from .go_detector import GoDetector
from .java_detector import JavaDetector
from .ruby_detector import RubyDetector
from .php_detector import PHPDetector
from .dotnet_detector import DotnetDetector
from .cpp_detector import CppDetector
from .docker_detector import DockerDetector
from .shell_detector import ShellDetector
from .r_detector import RDetector
from .perl_detector import PerlDetector
from .haskell_detector import HaskellDetector
from .elixir_detector import ElixirDetector
from .dart_detector import DartDetector
from .julia_detector import JuliaDetector
from .swift_detector import SwiftDetector
from .kotlin_detector import KotlinDetector
from .infra_detector import InfraDetector
from .deno_detector import DenoDetector

# 所有可用检测器（按优先级排序，共22个）
ALL_DETECTORS = [
    # 主流语言
    PythonDetector,
    NodeJSDetector,
    RustDetector,
    GoDetector,
    JavaDetector,
    KotlinDetector,
    RubyDetector,
    PHPDetector,
    DotnetDetector,
    CppDetector,
    # 容器 / 基础设施
    DockerDetector,
    InfraDetector,
    # 脚本 / 数据分析
    ShellDetector,
    RDetector,
    PerlDetector,
    # 新兴语言
    SwiftDetector,
    DartDetector,
    ElixirDetector,
    HaskellDetector,
    JuliaDetector,
    DenoDetector,
]

__all__ = [
    "BaseDetector", "DetectionResult", "DepInfo",
    "ALL_DETECTORS",
]
