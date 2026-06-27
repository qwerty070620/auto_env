#!/usr/bin/env python3
"""AutoEnv 独立入口 — 任何目录下均可运行
用法:
    python run.py                        交互模式
    python run.py <路径或URL>             直接检测
    python run.py <路径或URL> -y          全自动安装
    python run.py <路径或URL> --no-install  仅报告
    python run.py <路径或URL> --json       JSON输出
    python run.py <路径或URL> --generate   生成Dockerfile
    双击 启动.bat                          菜单模式
"""
import sys
import os

# 确保父目录在路径中，使 'import auto_env' 可用
_here = os.path.dirname(os.path.abspath(__file__))
_parent = os.path.dirname(_here)
if _parent not in sys.path:
    sys.path.insert(0, _parent)

# 将 sys.argv 中的 "run.py" 替换为占位符，其余参数原样传递给 auto_env
sys.argv = ['auto_env'] + sys.argv[1:]

from auto_env.auto_env import main
main()
