# dir2md - 递归目录文件转Markdown工具

基于 Microsoft MarkItDown 开发的批量文件转换工具。

## 功能特性

- 递归遍历指定目录
- 将所有支持的文件转换为Markdown格式
- 保持原有目录结构
- 支持并行处理
- 完善的日志和错误处理
- 转换报告生成

## 支持的文件格式

| 类别 | 格式 |
|------|------|
| 文档 | PDF, DOCX, DOC, PPTX, PPT, XLSX, XLS |
| 网页 | HTML, HTM, XHTML |
| 电子书 | EPUB |
| 文本 | TXT, CSV, JSON, XML |
| 图片 | PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP |
| 音频 | MP3, WAV, M4A, FLAC |
| 压缩 | ZIP |

## 安装

```bash
# 安装依赖
pip install 'markitdown[all]'
```

## 使用方法

```bash
# 基本用法：转换当前目录
python dir2md.py .

# 转换指定目录到输出目录
python dir2md.py ./documents -o ./markdown

# 使用8个线程并行转换
python dir2md.py ./documents -w 8

# 只转换PDF和Word文件
python dir2md.py ./documents -e .pdf .docx .doc

# 详细输出模式
python dir2md.py ./documents -v

# 覆盖已存在的文件
python dir2md.py ./documents --overwrite

# 不保持目录结构（所有文件输出到同一目录）
python dir2md.py ./documents --flat
```

## 参数说明

| 参数 | 说明 |
|------|------|
| `input_dir` | 输入目录路径（必需）|
| `-o, --output` | 输出目录路径（默认: input_dir/markdown_output）|
| `-w, --workers` | 并行工作线程数（默认: 4）|
| `--overwrite` | 覆盖已存在的输出文件 |
| `--flat` | 不保持目录结构 |
| `-v, --verbose` | 详细输出模式 |
| `-e, --extensions` | 只转换指定扩展名的文件 |
| `--exclude` | 排除匹配模式的文件/目录 |

## 输出

转换完成后会在输出目录生成：
- 转换后的 `.md` 文件（保持原有目录结构）
- `conversion_report.json` 转换报告

## 许可证

MIT License
