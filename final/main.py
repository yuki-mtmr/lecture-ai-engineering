#!/usr/bin/env python3
"""
講義スライド作成をサポートするCopilot - メインエントリーポイント
"""

import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cli import cli

if __name__ == '__main__':
    cli()