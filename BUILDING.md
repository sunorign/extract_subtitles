# 字幕提取工具 - 构建指南

## 开发环境

- JDK 17+
- Gradle 8.4+ (wrapper included)

## 目录结构

```
.
├── backend/           # Python FastAPI 后端
├── gui/               # Kotlin Compose Desktop 前端
│   ├── build.gradle.kts
│   ├── gradlew / gradlew.bat
│   └── src/main/kotlin/
├── python/            # 嵌入式 Python (需要手动准备 - 见下文)
├── extract_subtitles.py
├── ffmpeg.exe         # 项目根目录
├── ffprobe.exe
├── *.dll              # FFmpeg 依赖库
```

## 嵌入式 Python 准备

**注意：python/ 目录较大（约 1.6GB），不包含在 git 中。**

### 手动准备步骤：

1. **下载 Python 3.11 嵌入式 Windows 包**
   - https://www.python.org/downloads/windows/
   - 下载 "Windows embeddable package (64-bit)"

2. **解压到 python/**
   ```
   .worktrees/gui-dev/python/
   ├── python.exe
   ├── python311.dll
   ├── python311.zip
   └── ...
   ```

3. **启用 pip**
   - 编辑 `python/python311._pth`
   - 取消注释 `#import site` → `import site`

4. **安装 pip**
   ```bash
   cd python
   curl -L -o get-pip.py https://bootstrap.pypa.io/get-pip.py
   python.exe get-pip.py
   ```

5. **安装依赖**
   ```bash
   cd ..  # 回到项目根目录
   ./python/python.exe -m pip install -r backend/requirements.txt
   ```

## 开发运行

### 1. 运行后端（可选 - 用于单独测试）
```bash
cd backend
python main.py
```

健康检查：http://127.0.0.1:8765/health

### 2. 运行 GUI（会自动启动后端）
```bash
cd gui
./gradlew run
```

## 打包 EXE

```bash
cd gui
./gradlew packageExe
```

输出位置：
```
gui/build/compose/binaries/main/exe/SubtitleExtractor-1.0.0.exe
```

## 打包内容

最终 EXE 安装后包含：
- JVM 运行时
- Python 3.11 运行时 + 所有依赖
- FFmpeg（ffmpeg.exe, ffprobe.exe, *.dll）
- 字幕提取脚本
- GUI 应用
- FastAPI 后端

所有依赖完全内置，用户无需安装任何东西。

## 常见问题

### 1. Gradle 下载慢
配置国内镜像，在 `~/.gradle/gradle.properties` 添加：
```properties
systemProp.http.proxyHost=127.0.0.1
systemProp.http.proxyPort=7890
systemProp.https.proxyHost=127.0.0.1
systemProp.https.proxyPort=7890
```

### 2. 找不到 Python
确保：
- 打包后 python.exe 在安装目录的 python/ 下
- 开发时 python.exe 在项目根目录 python/ 下
- 或系统 PATH 中有可用的 Python

### 3. ffmpeg 找不到
确保项目根目录（或安装后根目录）有：
- ffmpeg.exe
- ffprobe.exe
- 相关的 *.dll 文件
