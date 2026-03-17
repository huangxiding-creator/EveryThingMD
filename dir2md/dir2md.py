#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dir2md - 递归目录文件转Markdown工具
基于 Microsoft MarkItDown 开发

功能：
- 递归遍历指定目录
- 将所有支持的文件转换为Markdown格式
- 保持原有目录结构
- 支持并行处理
- 完善的日志和错误处理
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
import traceback

# 尝试导入markitdown
try:
    from markitdown import MarkItDown
except ImportError:
    print("错误: 未安装 markitdown，请运行: pip install 'markitdown[all]'")
    sys.exit(1)


# 支持的文件格式
SUPPORTED_EXTENSIONS = {
    # 文档格式
    '.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls',
    # 网页格式
    '.html', '.htm', '.xhtml',
    # 电子书格式
    '.epub',
    # 文本格式
    '.txt', '.csv', '.json', '.xml',
    # 图片格式 (OCR)
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp',
    # 音频格式 (转录)
    '.mp3', '.wav', '.m4a', '.flac',
    # 压缩格式
    '.zip',
}

# 跳过的目录
SKIP_DIRS = {
    '__pycache__', '.git', '.svn', '.hg', 'node_modules',
    '.venv', 'venv', 'env', '.env', '.tox', '.pytest_cache',
    'build', 'dist', '.eggs', '*.egg-info', '.mypy_cache',
    '.idea', '.vscode', '.vs', 'Thumbs.db', '.DS_Store',
}


@dataclass
class ConversionResult:
    """转换结果"""
    source_path: str
    target_path: str
    success: bool
    error_message: str = ""
    file_size_source: int = 0
    file_size_target: int = 0
    processing_time: float = 0.0


@dataclass
class ConversionStats:
    """转换统计"""
    total_files: int = 0
    converted_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    total_size_source: int = 0
    total_size_target: int = 0
    total_time: float = 0.0
    errors: List[Tuple[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_files": self.total_files,
            "converted_files": self.converted_files,
            "failed_files": self.failed_files,
            "skipped_files": self.skipped_files,
            "total_size_source": self.total_size_source,
            "total_size_target": self.total_size_target,
            "total_time": round(self.total_time, 2),
            "success_rate": f"{(self.converted_files / max(self.total_files, 1)) * 100:.1f}%",
            "errors": self.errors[:10] if self.errors else []  # 只显示前10个错误
        }


class Dir2MdConverter:
    """目录转Markdown转换器"""

    def __init__(
        self,
        input_dir: str,
        output_dir: Optional[str] = None,
        workers: int = 4,
        overwrite: bool = False,
        preserve_structure: bool = True,
        verbose: bool = False,
        extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ):
        self.input_dir = Path(input_dir).resolve()
        self.output_dir = Path(output_dir).resolve() if output_dir else self.input_dir / "markdown_output"
        self.workers = max(1, workers)
        self.overwrite = overwrite
        self.preserve_structure = preserve_structure
        self.verbose = verbose
        self.extensions = set(extensions) if extensions else SUPPORTED_EXTENSIONS
        self.exclude_patterns = exclude_patterns or []

        # 初始化MarkItDown
        self.markitdown = MarkItDown()

        # 设置日志
        self._setup_logging()

        # 统计
        self.stats = ConversionStats()

    def _setup_logging(self):
        """设置日志"""
        log_level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

    def _should_skip_dir(self, dir_path: Path) -> bool:
        """判断是否应该跳过目录"""
        dir_name = dir_path.name.lower()
        return dir_name in SKIP_DIRS or dir_name.startswith('.')

    def _should_skip_file(self, file_path: Path) -> bool:
        """判断是否应该跳过文件"""
        # 检查扩展名
        ext = file_path.suffix.lower()
        if ext not in self.extensions:
            return True

        # 检查排除模式
        file_str = str(file_path)
        for pattern in self.exclude_patterns:
            if pattern.lower() in file_str.lower():
                return True

        return False

    def _get_output_path(self, file_path: Path) -> Path:
        """获取输出文件路径"""
        if self.preserve_structure:
            relative_path = file_path.relative_to(self.input_dir)
            output_path = self.output_dir / relative_path.parent / f"{file_path.stem}.md"
        else:
            output_path = self.output_dir / f"{file_path.stem}.md"

        return output_path

    def _convert_file(self, file_path: Path) -> ConversionResult:
        """转换单个文件"""
        import time
        start_time = time.time()

        output_path = self._get_output_path(file_path)

        result = ConversionResult(
            source_path=str(file_path),
            target_path=str(output_path),
            success=False,
            file_size_source=file_path.stat().st_size if file_path.exists() else 0
        )

        try:
            # 检查输出文件是否已存在
            if output_path.exists() and not self.overwrite:
                self.logger.debug(f"跳过已存在: {output_path}")
                result.success = True
                result.error_message = "已存在，跳过"
                return result

            # 创建输出目录
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 转换文件
            self.logger.debug(f"转换: {file_path} -> {output_path}")

            conversion_result = self.markitdown.convert(str(file_path))

            if conversion_result and conversion_result.text_content:
                # 写入输出文件
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(conversion_result.text_content)

                result.success = True
                result.file_size_target = output_path.stat().st_size
                self.logger.info(f"✓ 转换成功: {file_path.name}")
            else:
                result.error_message = "转换结果为空"
                self.logger.warning(f"⚠ 转换结果为空: {file_path}")

        except Exception as e:
            result.error_message = f"{type(e).__name__}: {str(e)}"
            self.logger.error(f"✗ 转换失败: {file_path} - {result.error_message}")
            if self.verbose:
                self.logger.debug(traceback.format_exc())

        result.processing_time = time.time() - start_time
        return result

    def collect_files(self) -> List[Path]:
        """收集所有需要转换的文件"""
        files = []

        self.logger.info(f"扫描目录: {self.input_dir}")

        for root, dirs, filenames in os.walk(self.input_dir):
            root_path = Path(root)

            # 过滤目录
            dirs[:] = [d for d in dirs if not self._should_skip_dir(root_path / d)]

            # 收集文件
            for filename in filenames:
                file_path = root_path / filename
                if not self._should_skip_file(file_path):
                    files.append(file_path)

        self.logger.info(f"发现 {len(files)} 个可转换文件")
        return files

    def convert(self) -> ConversionStats:
        """执行转换"""
        import time
        start_time = time.time()

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 收集文件
        files = self.collect_files()
        self.stats.total_files = len(files)

        if not files:
            self.logger.warning("没有找到可转换的文件")
            return self.stats

        self.logger.info(f"开始转换，使用 {self.workers} 个工作线程...")

        # 并行转换
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self._convert_file, f): f for f in files}

            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    result = future.result()

                    if result.success:
                        if "已存在" in result.error_message:
                            self.stats.skipped_files += 1
                        else:
                            self.stats.converted_files += 1
                        self.stats.total_size_source += result.file_size_source
                        self.stats.total_size_target += result.file_size_target
                    else:
                        self.stats.failed_files += 1
                        self.stats.errors.append((str(file_path), result.error_message))

                except Exception as e:
                    self.logger.error(f"处理异常: {file_path} - {e}")
                    self.stats.failed_files += 1
                    self.stats.errors.append((str(file_path), str(e)))

        self.stats.total_time = time.time() - start_time

        # 输出统计
        self._print_summary()

        # 保存统计报告
        self._save_report()

        return self.stats

    def _print_summary(self):
        """打印摘要"""
        print("\n" + "=" * 60)
        print("转换完成!")
        print("=" * 60)
        print(f"总文件数:     {self.stats.total_files}")
        print(f"成功转换:     {self.stats.converted_files}")
        print(f"跳过文件:     {self.stats.skipped_files}")
        print(f"失败文件:     {self.stats.failed_files}")
        print(f"成功率:       {(self.stats.converted_files / max(self.stats.total_files, 1)) * 100:.1f}%")
        print(f"总耗时:       {self.stats.total_time:.2f} 秒")
        print(f"输出目录:     {self.output_dir}")

        if self.stats.errors:
            print(f"\n错误列表 (前10个):")
            for path, error in self.stats.errors[:10]:
                print(f"  - {path}: {error}")

        print("=" * 60)

    def _save_report(self):
        """保存转换报告"""
        report_path = self.output_dir / "conversion_report.json"
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "input_dir": str(self.input_dir),
                    "output_dir": str(self.output_dir),
                    "stats": self.stats.to_dict()
                }, f, ensure_ascii=False, indent=2)
            self.logger.info(f"报告已保存: {report_path}")
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='dir2md - 递归目录文件转Markdown工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 转换当前目录
  python dir2md.py .

  # 转换指定目录到输出目录
  python dir2md.py ./documents -o ./markdown

  # 使用8个线程并行转换
  python dir2md.py ./documents -w 8

  # 只转换PDF和Word文件
  python dir2md.py ./documents -e .pdf .docx .doc

  # 详细输出模式
  python dir2md.py ./documents -v

支持的文件格式:
  PDF, Word, PowerPoint, Excel, HTML, EPUB, TXT, CSV, JSON, XML,
  图片 (PNG, JPG等), 音频 (MP3, WAV等), ZIP
        """
    )

    parser.add_argument('input_dir', help='输入目录路径')
    parser.add_argument('-o', '--output', help='输出目录路径 (默认: input_dir/markdown_output)')
    parser.add_argument('-w', '--workers', type=int, default=4, help='并行工作线程数 (默认: 4)')
    parser.add_argument('--overwrite', action='store_true', help='覆盖已存在的输出文件')
    parser.add_argument('--flat', action='store_true', help='不保持目录结构，所有文件输出到同一目录')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出模式')
    parser.add_argument('-e', '--extensions', nargs='+', help='只转换指定扩展名的文件')
    parser.add_argument('--exclude', nargs='+', help='排除匹配模式的文件/目录')

    args = parser.parse_args()

    # 验证输入目录
    if not os.path.isdir(args.input_dir):
        print(f"错误: 输入目录不存在: {args.input_dir}")
        sys.exit(1)

    # 创建转换器并执行
    converter = Dir2MdConverter(
        input_dir=args.input_dir,
        output_dir=args.output,
        workers=args.workers,
        overwrite=args.overwrite,
        preserve_structure=not args.flat,
        verbose=args.verbose,
        extensions=args.extensions,
        exclude_patterns=args.exclude,
    )

    stats = converter.convert()

    # 返回退出码
    sys.exit(0 if stats.failed_files == 0 else 1)


if __name__ == '__main__':
    main()
