package ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import api.BackendClient
import model.AiConfig
import model.FileItem
import model.ProcessingStatus
import model.SubtitleConfig
import ui.components.ConfigPanel
import ui.components.DropZone
import ui.components.FileList
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import java.awt.Desktop
import java.nio.file.Path
import java.nio.file.Paths

@Composable
fun MainScreen(
    backendClient: BackendClient,
    scope: CoroutineScope,
    modifier: Modifier = Modifier
) {
    var files by remember { mutableStateOf<List<FileItem>>(emptyList()) }
    var subtitleConfig by remember { mutableStateOf(SubtitleConfig()) }
    var aiConfig by remember { mutableStateOf(AiConfig()) }
    var isProcessing by remember { mutableStateOf(false) }
    var isTestingAi by remember { mutableStateOf(false) }
    var aiTestResult by remember { mutableStateOf<String?>(null) }
    var statusMessage by remember { mutableStateOf("就绪") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("字幕提取工具") }
            )
        },
        bottomBar = {
            BottomAppBar(
                contentPadding = PaddingValues(horizontal = 16.dp)
            ) {
                Text(
                    text = statusMessage,
                    color = if (isProcessing) Color(0xFFE6A800) else Color.Gray,
                    modifier = Modifier.weight(1f)
                )
            }
        },
        modifier = modifier
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Drop Zone
            DropZone(
                onFilesDropped = { newPaths ->
                    val newFiles = newPaths
                        .filter { it.toString().lowercase().endsWith(".mp4") }
                        .filter { path -> files.none { it.path == path } }
                        .map { FileItem(it) }
                    files = files + newFiles
                    if (newFiles.isEmpty() && newPaths.isNotEmpty()) {
                        statusMessage = "已跳过非 MP4 文件或重复文件"
                    } else {
                        statusMessage = "添加了 ${newFiles.size} 个文件"
                    }
                },
                modifier = Modifier.fillMaxWidth()
            )

            // File List
            FileList(files = files, modifier = Modifier.fillMaxWidth())

            // Action buttons for list
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.align(Alignment.End)
            ) {
                Button(
                    onClick = { files = emptyList(); statusMessage = "已清空文件列表" },
                    colors = ButtonDefaults.buttonColors(backgroundColor = Color.LightGray)
                ) {
                    Text("清空列表")
                }
            }

            // Config Panel
            ConfigPanel(
                subtitleConfig = subtitleConfig,
                aiConfig = aiConfig,
                onSubtitleConfigChanged = { subtitleConfig = it },
                onAiConfigChanged = { aiConfig = it },
                onTestAi = {
                    scope.launch {
                        isTestingAi = true
                        aiTestResult = null
                        val result = backendClient.testAi(aiConfig)
                        if (result.isSuccess) {
                            aiTestResult = result.getOrNull() ?: "连接成功"
                        } else {
                            aiTestResult = "测试失败: ${result.exceptionOrNull()?.message}"
                        }
                        isTestingAi = false
                    }
                },
                isTesting = isTestingAi,
                testResult = aiTestResult,
                modifier = Modifier.fillMaxWidth()
            )

            // Main action buttons
            Row(
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Button(
                    onClick = {
                        val outputDir = subtitleConfig.outputDir
                        if (!outputDir.isNullOrBlank()) {
                            val path = Paths.get(outputDir)
                            if (path.toFile().exists()) {
                                Desktop.getDesktop().open(path.toFile())
                            }
                        } else if (files.isNotEmpty()) {
                            val firstFile = files.first().path
                            val parent = firstFile.parent
                            if (parent != null) {
                                Desktop.getDesktop().open(parent.toFile())
                            }
                        }
                    },
                    enabled = files.isNotEmpty(),
                    modifier = Modifier.weight(1f)
                ) {
                    Text("打开输出目录")
                }

                Button(
                    onClick = {
                        scope.launch {
                            processFiles(
                                files = files,
                                subtitleConfig = subtitleConfig,
                                aiConfig = aiConfig,
                                backendClient = backendClient,
                                onProgress = { updatedFiles, msg ->
                                    files = updatedFiles
                                    statusMessage = msg
                                },
                                onComplete = {
                                    isProcessing = false
                                }
                            )
                        }
                    },
                    enabled = !isProcessing && files.isNotEmpty(),
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(
                        backgroundColor = if (!isProcessing) MaterialTheme.colors.primary else Color.Gray
                    )
                ) {
                    if (isProcessing) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(16.dp),
                            color = Color.White
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                    }
                    Text(if (isProcessing) "处理中..." else "开始处理")
                }
            }
        }
    }
}

suspend fun processFiles(
    files: List<FileItem>,
    subtitleConfig: SubtitleConfig,
    aiConfig: AiConfig,
    backendClient: BackendClient,
    onProgress: (List<FileItem>, String) -> Unit,
    onComplete: () -> Unit
) {
    val updatedFiles = files.toMutableList()
    var successCount = 0
    var failCount = 0

    for ((index, fileItem) in updatedFiles.withIndex()) {
        if (fileItem.status == ProcessingStatus.DONE) {
            successCount++
            continue
        }

        updatedFiles[index] = fileItem.copy(status = ProcessingStatus.PROCESSING)
        onProgress(updatedFiles, "正在处理 ${fileItem.fileName} (${index + 1}/${updatedFiles.size})")

        val result = backendClient.processVideo(
            videoPath = fileItem.path,
            subtitleConfig = subtitleConfig,
            aiConfig = aiConfig
        )

        if (result.isSuccess) {
            val response = result.getOrNull()
            if (response != null && response.success) {
                updatedFiles[index] = fileItem.copy(
                    status = ProcessingStatus.DONE,
                    subtitlePath = response.subtitle_path?.let { Paths.get(it) },
                    summaryPath = response.summary_path?.let { Paths.get(it) },
                    message = "OK"
                )
                successCount++
            } else {
                updatedFiles[index] = fileItem.copy(
                    status = ProcessingStatus.FAILED,
                    message = response?.message ?: "未知错误"
                )
                failCount++
            }
        } else {
            updatedFiles[index] = fileItem.copy(
                status = ProcessingStatus.FAILED,
                message = result.exceptionOrNull()?.message ?: "未知错误"
            )
            failCount++
        }

        onProgress(updatedFiles, "正在处理 ${fileItem.fileName} (${index + 1}/${updatedFiles.size})")
    }

    onProgress(updatedFiles, "处理完成: 成功 $successCount, 失败 $failCount")
    onComplete()
}