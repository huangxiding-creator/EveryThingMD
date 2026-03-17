#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dir2md_dual - 双工具对比转换器
同时使用 MarkItDown 和 PaddleOCR 转换文件，对比质量后保留最优结果

质量评估标准:
- 准确度 (60%): 文字正确转换比例，乱码检测，编码质量
- 完整度 (40%): 内容覆盖比例，字数统计，结构完整性

Author: Enhanced by Super-Skill V3.10
"""

import os
import sys
import argparse
import logging
import json
import re
import time
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

# 尝试导入 PaddleOCR
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    print("警告: 未安装 paddleocr，将仅使用 MarkItDown。请运行: pip install paddleocr paddlepaddle")

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

# OCR 优先的格式（图片和扫描PDF）
OCR_PREFERRED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}

# MarkItDown 优先的格式（数字文档）
MARKDOWN_PREFERRED_EXTENSIONS = {'.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls', '.html', '.epub', '.txt'}

# 跳过的目录
SKIP_DIRS = {
    '__pycache__', '.git', '.svn', '.hg', 'node_modules',
    '.venv', 'venv', 'env', '.env', '.tox', '.pytest_cache',
    'build', 'dist', '.eggs', '*.egg-info', '.mypy_cache',
    '.idea', '.vscode', '.vs', 'Thumbs.db', '.DS_Store',
}


@dataclass
class QualityScore:
    """质量评分"""
    accuracy: float  # 准确度 (0-100)
    completeness: float  # 完整度 (0-100)
    weighted_score: float  # 综合加权分数
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversionResult:
    """转换结果"""
    source_path: str
    target_path: str
    success: bool
    tool_used: str = ""  # "markitdown", "paddleocr", or "both_compared"
    error_message: str = ""
    file_size_source: int = 0
    file_size_target: int = 0
    processing_time: float = 0.0
    quality_score: Optional[QualityScore] = None
    markitdown_score: Optional[float] = None
    ocr_score: Optional[float] = None


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
    tool_wins: Dict[str, int] = field(default_factory=lambda: {"markitdown": 0, "paddleocr": 0, "single_option": 0})

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
            "tool_wins": self.tool_wins,
            "errors": self.errors[:10] if self.errors else []
        }


class QualityEvaluator:
    """质量评估器 - 评估转换文本的准确度和完整度"""

    # 乱码特征模式
    GARBAGE_PATTERNS = [
        r'[\x00-\x08\x0b\x0c\x0e-\x1f]',  # 控制字符
        r'(�+)',  # 替换字符
        r'(\w)\1{4,}',  # 重复字符 (如 aaaaa)
        r'[^\x00-\xff]{50,}',  # 长串非ASCII（可能是编码错误）
    ]

    # 中文常见字范围
    CHINESE_PATTERN = r'[\u4e00-\u9fff]'

    # 有效句子模式
    SENTENCE_PATTERN = r'[。！？.!?]'

    def __init__(self, source_file: Path):
        self.source_file = source_file
        self.source_size = source_file.stat().st_size if source_file.exists() else 0
        self.ext = source_file.suffix.lower()

    def evaluate(self, text: str) -> QualityScore:
        """评估文本质量"""
        if not text or not text.strip():
            return QualityScore(accuracy=0, completeness=0, weighted_score=0,
                              details={"error": "空文本"})

        accuracy = self._calculate_accuracy(text)
        completeness = self._calculate_completeness(text)

        # 加权计算: 准确度60% + 完整度40%
        weighted_score = accuracy * 0.6 + completeness * 0.4

        return QualityScore(
            accuracy=accuracy,
            completeness=completeness,
            weighted_score=weighted_score,
            details={
                "char_count": len(text),
                "chinese_ratio": self._get_chinese_ratio(text),
                "sentence_count": len(re.findall(self.SENTENCE_PATTERN, text)),
                "garbage_ratio": self._get_garbage_ratio(text)
            }
        )

    def _calculate_accuracy(self, text: str) -> float:
        """计算准确度 (0-100)

        评估标准:
        1. 无乱码/控制字符
        2. 字符分布合理
        3. 编码正确性
        """
        score = 100.0

        # 检测乱码
        garbage_ratio = self._get_garbage_ratio(text)
        if garbage_ratio > 0:
            score -= garbage_ratio * 100  # 每减少乱码比例扣分

        # 检测异常字符重复
        repeat_pattern = r'(\S)\1{5,}'
        repeat_matches = re.findall(repeat_pattern, text)
        if repeat_matches:
            score -= min(len(repeat_matches) * 5, 30)  # 每处扣5分，最多30分

        # 检测有效的中文内容
        chinese_ratio = self._get_chinese_ratio(text)
        if self.ext in {'.pdf', '.docx', '.doc'} or chinese_ratio > 0.1:
            # 预期有中文内容的文档
            if chinese_ratio < 0.05:
                score -= 20  # 中文文档缺少中文字符，扣分

        # 检测句子结构完整性
        sentence_count = len(re.findall(self.SENTENCE_PATTERN, text))
        char_per_sentence = len(text) / max(sentence_count, 1)
        if char_per_sentence > 500:  # 平均每句太长，可能缺少标点
            score -= 15

        return max(0, min(100, score))

    def _calculate_completeness(self, text: str) -> float:
        """计算完整度 (0-100)

        评估标准:
        1. 文本长度相对源文件大小的合理性
        2. 内容结构完整性
        3. 段落/句子数量
        """
        if self.source_size == 0:
            return 50  # 无法评估时给中等分数

        score = 100.0

        # 计算文本长度与源文件大小的比例
        # 一般文档: 每1KB源文件应有约200-500字符
        size_ratio = len(text) / max(self.source_size, 1)

        # 根据文件类型调整期望比例
        if self.ext in OCR_PREFERRED_EXTENSIONS:
            # 图片OCR: 期望比例较低
            expected_min, expected_max = 0.0001, 0.01
        elif self.ext == '.pdf':
            # PDF: 期望中等比例
            expected_min, expected_max = 0.001, 0.1
        else:
            # 其他文档: 期望较高比例
            expected_min, expected_max = 0.01, 0.5

        if size_ratio < expected_min:
            # 文本太少，可能转换不完整
            score -= 40
        elif size_ratio > expected_max:
            # 文本过多，可能有重复或错误
            score -= 20

        # 检查段落结构
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        if len(paragraphs) < 2:
            score -= 15  # 缺少段落结构

        # 检查句子数量
        sentence_count = len(re.findall(self.SENTENCE_PATTERN, text))
        if sentence_count < 3 and len(text) > 500:
            score -= 10  # 长文本但缺少句子分隔

        return max(0, min(100, score))

    def _get_garbage_ratio(self, text: str) -> float:
        """获取乱码字符比例"""
        if not text:
            return 1.0

        garbage_count = 0
        for pattern in self.GARBAGE_PATTERNS:
            garbage_count += len(re.findall(pattern, text))

        return garbage_count / max(len(text), 1)

    def _get_chinese_ratio(self, text: str) -> float:
        """获取中文字符比例"""
        if not text:
            return 0

        chinese_chars = len(re.findall(self.CHINESE_PATTERN, text))
        return chinese_chars / max(len(text), 1)


class DualConverter:
    """双工具对比转换器"""

    # PDF页数阈值：超过此页数的PDF仅使用MarkItDown转换
    PDF_PAGE_THRESHOLD = 20

    def __init__(
        self,
        input_dir: str,
        output_dir: Optional[str] = None,
        workers: int = 2,  # 降低并行度，因为每个文件会运行两个工具
        overwrite: bool = False,
        preserve_structure: bool = True,
        verbose: bool = False,
        extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        prefer_tool: str = "auto",  # "markitdown", "paddleocr", "auto"
    ):
        self.input_dir = Path(input_dir).resolve()
        self.output_dir = Path(output_dir).resolve() if output_dir else self.input_dir / "markdown_output"
        self.workers = max(1, workers)
        self.overwrite = overwrite
        self.preserve_structure = preserve_structure
        self.verbose = verbose
        self.extensions = set(extensions) if extensions else SUPPORTED_EXTENSIONS
        self.exclude_patterns = exclude_patterns or []
        self.prefer_tool = prefer_tool

        # 初始化工具
        self.markitdown = MarkItDown()
        self.paddleocr = None

        if PADDLEOCR_AVAILABLE:
            try:
                # 初始化 PaddleOCR，使用中英文模型
                self.paddleocr = PaddleOCR(lang='ch')
                logging.info("PaddleOCR 初始化成功")
            except Exception as e:
                logging.warning(f"PaddleOCR 初始化失败: {e}")
                self.paddleocr = None

        # 设置日志
        self._setup_logging()

        # 统计
        self.stats = ConversionStats()

        # 临时目录用于存储对比结果
        self.temp_dir = self.output_dir / ".temp_compare"

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
        ext = file_path.suffix.lower()
        if ext not in self.extensions:
            return True

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

    def _convert_with_markitdown(self, file_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """使用 MarkItDown 转换"""
        try:
            result = self.markitdown.convert(str(file_path))
            if result and result.text_content:
                return result.text_content, None
            return None, "转换结果为空"
        except Exception as e:
            return None, f"{type(e).__name__}: {str(e)}"

    def _get_pdf_page_count(self, file_path: Path) -> int:
        """获取PDF文件的页数"""
        try:
            import fitz  # PyMuPDF
            pdf_document = fitz.open(str(file_path))
            page_count = len(pdf_document)
            pdf_document.close()
            return page_count
        except ImportError:
            self.logger.warning("需要安装 PyMuPDF 才能获取PDF页数: pip install pymupdf")
            return 0
        except Exception as e:
            self.logger.warning(f"获取PDF页数失败: {file_path.name} - {e}")
            return 0

    def _convert_with_paddleocr(self, file_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """使用 PaddleOCR 转换"""
        if not self.paddleocr:
            return None, "PaddleOCR 未初始化"

        try:
            ext = file_path.suffix.lower()

            if ext in OCR_PREFERRED_EXTENSIONS:
                # 直接处理图片
                result = self.paddleocr.ocr(str(file_path))
                text = self._extract_paddleocr_text(result)
                return text, None
            elif ext == '.pdf':
                # PDF需要先转图片
                return self._convert_pdf_with_ocr(file_path)
            else:
                # 其他格式暂不支持OCR
                return None, "PaddleOCR 仅支持图片和PDF"

        except Exception as e:
            return None, f"{type(e).__name__}: {str(e)}"

    def _convert_pdf_with_ocr(self, file_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """使用OCR处理PDF（需要先转换为图片）"""
        try:
            import fitz  # PyMuPDF

            pdf_document = fitz.open(str(file_path))
            all_text = []

            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                # 将页面转换为图片
                mat = fitz.Matrix(2, 2)  # 2x缩放提高OCR质量
                pix = page.get_pixmap(matrix=mat)

                # 保存临时图片
                temp_img = self.temp_dir / f"temp_page_{page_num}.png"
                self.temp_dir.mkdir(parents=True, exist_ok=True)
                pix.save(str(temp_img))

                # OCR处理
                result = self.paddleocr.ocr(str(temp_img))
                if result and result[0]:
                    page_text = self._extract_paddleocr_text(result)
                    all_text.append(f"--- 第 {page_num + 1} 页 ---\n{page_text}")

                # 清理临时文件
                temp_img.unlink(missing_ok=True)

            pdf_document.close()
            return "\n\n".join(all_text), None

        except ImportError:
            return None, "需要安装 PyMuPDF: pip install pymupdf"
        except Exception as e:
            return None, f"{type(e).__name__}: {str(e)}"

    def _extract_paddleocr_text(self, ocr_result: List) -> str:
        """从 PaddleOCR 结果中提取文本

        PaddleOCR V3.4+ 返回格式: [{'rec_texts': [...], 'rec_scores': [...], ...}]
        旧版本格式: [[[bbox, (text, confidence)], ...], ...]
        """
        texts = []
        if ocr_result and ocr_result[0]:
            first_result = ocr_result[0]

            # 新版本格式: dict with 'rec_texts' key
            if isinstance(first_result, dict) and 'rec_texts' in first_result:
                texts = first_result['rec_texts']
            # 旧版本格式: list of [bbox, (text, confidence)]
            elif isinstance(first_result, list):
                for line in first_result:
                    if line and len(line) >= 2:
                        text_info = line[1]
                        if isinstance(text_info, tuple) and len(text_info) >= 1:
                            text = text_info[0]
                            texts.append(text)

        return "\n".join(texts) if texts else ""

    def _convert_file(self, file_path: Path) -> ConversionResult:
        """转换单个文件（双工具对比）"""
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
                result.success = True
                result.error_message = "已存在，跳过"
                result.tool_used = "cached"
                return result

            # 创建输出目录
            output_path.parent.mkdir(parents=True, exist_ok=True)
            self.temp_dir.mkdir(parents=True, exist_ok=True)

            ext = file_path.suffix.lower()

            # 决定使用哪些工具
            use_markitdown = True
            use_paddleocr = PADDLEOCR_AVAILABLE and self.paddleocr is not None

            # 图片文件：仅使用PaddleOCR，跳过MarkItDown
            if ext in OCR_PREFERRED_EXTENSIONS:
                use_markitdown = False
                use_paddleocr = PADDLEOCR_AVAILABLE and self.paddleocr is not None
                self.logger.info(f"[优化] 图片文件，仅使用PaddleOCR: {file_path.name}")
            # PDF文件：对于超过20页的，跳过PaddleOCR（性能优化）
            elif ext == '.pdf' and use_paddleocr:
                page_count = self._get_pdf_page_count(file_path)
                if page_count > self.PDF_PAGE_THRESHOLD:
                    self.logger.info(
                        f"[优化] PDF页数({page_count}) > {self.PDF_PAGE_THRESHOLD}页，"
                        f"跳过PaddleOCR，仅使用MarkItDown: {file_path.name}"
                    )
                    use_paddleocr = False

            # 根据文件类型和偏好调整
            if self.prefer_tool == "markitdown":
                use_paddleocr = ext in OCR_PREFERRED_EXTENSIONS
            elif self.prefer_tool == "paddleocr":
                use_markitdown = ext not in OCR_PREFERRED_EXTENSIONS

            markitdown_text = None
            paddleocr_text = None
            markitdown_error = None
            paddleocr_error = None

            # 使用 MarkItDown 转换
            if use_markitdown:
                self.logger.debug(f"[MarkItDown] 转换: {file_path.name}")
                markitdown_text, markitdown_error = self._convert_with_markitdown(file_path)

            # 使用 PaddleOCR 转换
            if use_paddleocr:
                self.logger.debug(f"[PaddleOCR] 转换: {file_path.name}")
                paddleocr_text, paddleocr_error = self._convert_with_paddleocr(file_path)

            # 评估和选择最佳结果
            evaluator = QualityEvaluator(file_path)

            best_text = None
            best_tool = None
            markitdown_score = None
            ocr_score = None

            if markitdown_text and paddleocr_text:
                # 两个都有结果，对比质量
                md_quality = evaluator.evaluate(markitdown_text)
                ocr_quality = evaluator.evaluate(paddleocr_text)

                markitdown_score = md_quality.weighted_score
                ocr_score = ocr_quality.weighted_score

                self.logger.info(
                    f"质量对比 [{file_path.name}]: "
                    f"MarkItDown={md_quality.weighted_score:.1f} "
                    f"(准确:{md_quality.accuracy:.0f}/完整:{md_quality.completeness:.0f}) vs "
                    f"PaddleOCR={ocr_quality.weighted_score:.1f} "
                    f"(准确:{ocr_quality.accuracy:.0f}/完整:{ocr_quality.completeness:.0f})"
                )

                if md_quality.weighted_score >= ocr_quality.weighted_score:
                    best_text = markitdown_text
                    best_tool = "markitdown"
                    result.quality_score = md_quality
                else:
                    best_text = paddleocr_text
                    best_tool = "paddleocr"
                    result.quality_score = ocr_quality

            elif markitdown_text:
                best_text = markitdown_text
                best_tool = "markitdown"
                result.quality_score = evaluator.evaluate(markitdown_text)
                markitdown_score = result.quality_score.weighted_score

            elif paddleocr_text:
                best_text = paddleocr_text
                best_tool = "paddleocr"
                result.quality_score = evaluator.evaluate(paddleocr_text)
                ocr_score = result.quality_score.weighted_score

            # 写入最佳结果
            if best_text:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(best_text)

                result.success = True
                result.tool_used = best_tool
                result.markitdown_score = markitdown_score
                result.ocr_score = ocr_score
                result.file_size_target = output_path.stat().st_size

                self.logger.info(
                    f"✓ 转换成功: {file_path.name} -> {best_tool} "
                    f"(综合分:{result.quality_score.weighted_score:.1f})"
                )
            else:
                errors = []
                if markitdown_error:
                    errors.append(f"MarkItDown: {markitdown_error}")
                if paddleocr_error:
                    errors.append(f"PaddleOCR: {paddleocr_error}")
                result.error_message = "; ".join(errors)
                self.logger.error(f"✗ 转换失败: {file_path} - {result.error_message}")

        except Exception as e:
            result.error_message = f"{type(e).__name__}: {str(e)}"
            self.logger.error(f"✗ 转换异常: {file_path} - {result.error_message}")
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
            dirs[:] = [d for d in dirs if not self._should_skip_dir(root_path / d)]

            for filename in filenames:
                file_path = root_path / filename
                if not self._should_skip_file(file_path):
                    files.append(file_path)

        self.logger.info(f"发现 {len(files)} 个可转换文件")
        return files

    def convert(self) -> ConversionStats:
        """执行转换"""
        start_time = time.time()

        self.output_dir.mkdir(parents=True, exist_ok=True)

        files = self.collect_files()
        self.stats.total_files = len(files)

        if not files:
            self.logger.warning("没有找到可转换的文件")
            return self.stats

        self.logger.info(f"开始双工具对比转换，使用 {self.workers} 个工作线程...")
        self.logger.info(f"工具状态: MarkItDown=可用, PaddleOCR={'可用' if self.paddleocr else '不可用'}")

        # 并行转换
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self._convert_file, f): f for f in files}

            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    result = future.result()

                    if result.success:
                        if result.tool_used == "cached":
                            self.stats.skipped_files += 1
                        else:
                            self.stats.converted_files += 1
                            # 统计工具胜出次数
                            if result.tool_used == "markitdown":
                                self.stats.tool_wins["markitdown"] += 1
                            elif result.tool_used == "paddleocr":
                                self.stats.tool_wins["paddleocr"] += 1
                            else:
                                self.stats.tool_wins["single_option"] += 1

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

        # 清理临时目录
        if self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)

        self._print_summary()
        self._save_report()

        return self.stats

    def _print_summary(self):
        """打印摘要"""
        print("\n" + "=" * 70)
        print("双工具对比转换完成!")
        print("=" * 70)
        print(f"总文件数:       {self.stats.total_files}")
        print(f"成功转换:       {self.stats.converted_files}")
        print(f"跳过文件:       {self.stats.skipped_files}")
        print(f"失败文件:       {self.stats.failed_files}")
        print(f"成功率:         {(self.stats.converted_files / max(self.stats.total_files, 1)) * 100:.1f}%")
        print(f"总耗时:         {self.stats.total_time:.2f} 秒")
        print(f"\n工具胜出统计:")
        print(f"  MarkItDown:   {self.stats.tool_wins['markitdown']} 次")
        print(f"  PaddleOCR:    {self.stats.tool_wins['paddleocr']} 次")
        print(f"  单一选项:     {self.stats.tool_wins['single_option']} 次")
        print(f"\n输出目录:       {self.output_dir}")

        if self.stats.errors:
            print(f"\n错误列表 (前10个):")
            for path, error in self.stats.errors[:10]:
                print(f"  - {Path(path).name}: {error}")

        print("=" * 70)

    def _save_report(self):
        """保存转换报告"""
        report_path = self.output_dir / "conversion_report.json"
        try:
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "input_dir": str(self.input_dir),
                "output_dir": str(self.output_dir),
                "mode": "dual_tool_comparison",
                "tools": ["markitdown", "paddleocr"],
                "quality_weights": {
                    "accuracy": 0.6,
                    "completeness": 0.4
                },
                "stats": self.stats.to_dict()
            }
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"报告已保存: {report_path}")
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='dir2md_dual - 双工具对比转换器 (MarkItDown + PaddleOCR)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用双工具对比转换
  python dir2md_dual.py ./documents -o ./markdown

  # 强制重新转换（覆盖已存在文件）
  python dir2md_dual.py ./documents --overwrite

  # 优先使用 MarkItDown
  python dir2md_dual.py ./documents --prefer markitdown

  # 详细输出模式
  python dir2md_dual.py ./documents -v

质量评估标准:
  - 准确度 (60%): 无乱码、编码正确、字符分布合理
  - 完整度 (40%): 内容覆盖完整、结构完整

支持的文件格式:
  PDF, Word, PowerPoint, Excel, HTML, EPUB, TXT, CSV, JSON, XML,
  图片 (PNG, JPG等), 音频 (MP3, WAV等), ZIP
        """
    )

    parser.add_argument('input_dir', help='输入目录路径')
    parser.add_argument('-o', '--output', help='输出目录路径 (默认: input_dir/markdown_output)')
    parser.add_argument('-w', '--workers', type=int, default=2, help='并行工作线程数 (默认: 2)')
    parser.add_argument('--overwrite', action='store_true', help='覆盖已存在的输出文件')
    parser.add_argument('--flat', action='store_true', help='不保持目录结构')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出模式')
    parser.add_argument('-e', '--extensions', nargs='+', help='只转换指定扩展名的文件')
    parser.add_argument('--exclude', nargs='+', help='排除匹配模式的文件/目录')
    parser.add_argument('--prefer', choices=['markitdown', 'paddleocr', 'auto'],
                       default='auto', help='优先使用的工具 (默认: auto)')

    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print(f"错误: 输入目录不存在: {args.input_dir}")
        sys.exit(1)

    converter = DualConverter(
        input_dir=args.input_dir,
        output_dir=args.output,
        workers=args.workers,
        overwrite=args.overwrite,
        preserve_structure=not args.flat,
        verbose=args.verbose,
        extensions=args.extensions,
        exclude_patterns=args.exclude,
        prefer_tool=args.prefer,
    )

    stats = converter.convert()

    sys.exit(0 if stats.failed_files == 0 else 1)


if __name__ == '__main__':
    main()
