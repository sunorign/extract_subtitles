# extract_subtitles

批量提取视频字幕工具。如果视频有内嵌字幕就直接提取，没有就用 OpenAI Whisper 语音转文字生成字幕。输出保存为和视频同名的 `.txt` 文本文件。

## 功能特性

- ✅ 自动检测视频是否有内嵌字幕
- ✅ 有内嵌字幕 → 直接提取转换为纯文本
- ✅ 没有内嵌字幕 → 使用 Whisper 语音转文字
- ✅ 批量处理当前目录下所有 `.mp4` 文件
- ✅ 跳过已生成的 `.txt` 文件（不重复处理）
- ✅ 自动查找 ffmpeg（支持放在当前目录，不需要添加到系统 PATH）

## 安装依赖

### 1. 安装 ffmpeg

**Windows:**
- 下载: https://github.com/BtbN/FFmpeg-Builds/releases
- 下载 `ffmpeg-master-latest-win64-gpl.zip`
- 解压后把 `ffmpeg.exe` 和 `ffprobe.exe` 放到本目录

或者用包管理器:
```bash
# winget
winget install ffmpeg

# Chocolatey
choco install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

### 2. 安装 Python 依赖

```bash
pip install openai-whisper
```

## 使用方法

### 基本用法

```bash
python extract_subtitles.py
```

### 选项

```bash
# 使用更大模型提高准确率 (默认: base)
python extract_subtitles.py --model large

# 指定语言 (默认: 自动检测)
python extract_subtitles.py --language zh
```

**可用模型:** `tiny`, `base`, `small`, `medium`, `large`

| 模型  | 下载大小 | 说明 |
|-------|---------|------|
| tiny  | ~75MB   | 最快，准确率较低 |
| base  | ~142MB  | 平衡，默认选择 |
| small | ~466MB  | 更好准确率，较慢 |
| medium | ~1.5GB  | 准确率不错，很慢 |
| large | ~2.9GB  | 最高准确率，非常慢 |

## 输出

处理完成后，每个 `.mp4` 视频会生成一个同名的 `.txt` 文件:
- `video.mp4` → `video.txt`

## 示例

当前目录处理结果:
- 三个 Bilibili 查理·芒格主题视频已处理
- 生成了对应的 `.txt` 字幕文件
- Whisper base 模型中文识别效果良好

## 工作流程

```
扫描当前目录 → 找到所有 .mp4
   ↓
对每个视频:
   ↓
   检测是否有内嵌字幕?
   ↙        ↘
有               无
↓               ↓
提取字幕 → 转纯文本    Whisper 语音转文字
   ↓               ↓
保存为 .txt        保存为 .txt
   ↓
跳过已存在的输出文件
```

## 许可证

MIT
