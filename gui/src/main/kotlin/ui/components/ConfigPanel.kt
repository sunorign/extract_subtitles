package ui.components

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import model.AiConfig
import model.SubtitleConfig
import java.awt.FileDialog
import java.awt.Frame
import java.nio.file.Paths

@Composable
fun ConfigPanel(
    subtitleConfig: SubtitleConfig,
    aiConfig: AiConfig,
    onSubtitleConfigChanged: (SubtitleConfig) -> Unit,
    onAiConfigChanged: (AiConfig) -> Unit,
    onTestAi: () -> Unit,
    isTesting: Boolean,
    testResult: String?,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(Color.LightGray.copy(alpha = 0.2f), RoundedCornerShape(8.dp))
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text("字幕提取设置", fontSize = 16.sp, fontWeight = FontWeight.Bold)

        // Output directory
        OutputDirectorySelector(
            currentPath = subtitleConfig.outputDir,
            onPathSelected = { path ->
                onSubtitleConfigChanged(subtitleConfig.copy(outputDir = path))
            }
        )

        // Whisper model selection
        WhisperModelSelector(
            selectedModel = subtitleConfig.whisperModel,
            onModelSelected = { model ->
            onSubtitleConfigChanged(subtitleConfig.copy(whisperModel = model))
        }
        )

        // Language selection
        LanguageSelector(
            selectedLanguage = subtitleConfig.language,
            onLanguageSelected = { lang ->
                onSubtitleConfigChanged(subtitleConfig.copy(language = lang))
            }
        )

        Divider()

        // AI Summary settings
        Text("AI 总结设置", fontSize = 16.sp, fontWeight = FontWeight.Bold)

        Row(
            verticalAlignment = Alignment.CenterVertically
        ) {
            Checkbox(
                checked = aiConfig.enabled,
                onCheckedChange = { enabled ->
                    onAiConfigChanged(aiConfig.copy(enabled = enabled))
                }
            )
            Text("启用 AI 总结")
        }

        if (aiConfig.enabled) {
            // API URL
            OutlinedTextField(
                value = aiConfig.apiUrl,
                onValueChange = { onAiConfigChanged(aiConfig.copy(apiUrl = it)) },
                label = { Text("API URL") },
                placeholder = { Text("https://api.openai.com/v1/chat/completions") },
                modifier = Modifier.fillMaxWidth()
            )

            // Model name (manual input)
            OutlinedTextField(
                value = aiConfig.model,
                onValueChange = { onAiConfigChanged(aiConfig.copy(model = it)) },
                label = { Text("模型名称") },
                placeholder = { Text("gpt-4o-mini 或 claude-3-5-sonnet-latest") },
                modifier = Modifier.fillMaxWidth()
            )

            // API Key (password)
            OutlinedTextField(
                value = aiConfig.apiKey,
                onValueChange = { onAiConfigChanged(aiConfig.copy(apiKey = it)) },
                label = { Text("API Key") },
                placeholder = { Text("sk-... 或 sk-ant-...") },
                modifier = Modifier.fillMaxWidth(),
                visualTransformation = PasswordVisualTransformation()
            )

            // Prompt template
            OutlinedTextField(
                value = aiConfig.promptTemplate,
                onValueChange = { onAiConfigChanged(aiConfig.copy(promptTemplate = it)) },
                label = { Text("总结提示词") },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(80.dp),
                maxLines = 3
            )

            // Test button and result
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Button(
                    onClick = onTestAi,
                    enabled = !isTesting && aiConfig.isValid()
                ) {
                    if (isTesting) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(16.dp),
                            color = Color.White
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                    }
                    Text("测试连接")
                }

                if (testResult != null) {
                    val color = if (testResult.startsWith("Connection OK")) Color(0xFF008000) else Color(0xFFCC0000)
                    Text(
                        text = testResult,
                        color = color,
                        fontSize = 12.sp,
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        }
    }
}

@Composable
fun OutputDirectorySelector(
    currentPath: String?,
    onPathSelected: (String?) -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text("输出目录:", fontSize = 14.sp, modifier = Modifier.width(80.dp))
        val displayText = when {
            currentPath.isNullOrBlank() -> "默认（和视频同目录）"
            else -> currentPath
        }
        Text(
            text = displayText,
            fontSize = 13.sp,
            color = if (currentPath.isNullOrBlank()) Color.Gray else Color.Black,
            modifier = Modifier.weight(1f)
        )
        Button(
            onClick = {
                val frame = Frame()
                val dialog = FileDialog(frame, "选择输出目录", FileDialog.LOAD)
                dialog.isVisible = true
                val directory = dialog.directory
                frame.dispose()
                if (directory != null) {
                    onPathSelected(directory)
                }
            },
            modifier = Modifier.height(36.dp)
        ) {
            Text("浏览...", fontSize = 12.sp)
        }
        Button(
            onClick = { onPathSelected(null) },
            modifier = Modifier.height(36.dp),
            colors = ButtonDefaults.buttonColors(
                backgroundColor = if (currentPath != null) Color.LightGray else Color.LightGray.copy(alpha = 0.5f)
            )
        ) {
            Text("默认", fontSize = 12.sp)
        }
    }
}

@Composable
fun WhisperModelSelector(
    selectedModel: String,
    onModelSelected: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val models = listOf("tiny", "base", "small", "medium", "large")
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text("Whisper 模型:", fontSize = 14.sp, modifier = Modifier.width(80.dp))
        models.forEach { model ->
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                RadioButton(
                    selected = selectedModel == model,
                    onClick = { onModelSelected(model) }
                )
                Text(model, fontSize = 13.sp)
            }
        }
    }
}

@Composable
fun LanguageSelector(
    selectedLanguage: String?,
    onLanguageSelected: (String?) -> Unit,
    modifier: Modifier = Modifier
) {
    val languages = listOf(
        null to "自动检测",
        "zh" to "中文",
        "en" to "英文",
        "ja" to "日文",
        "ko" to "韩文"
    )
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text("语言:", fontSize = 14.sp, modifier = Modifier.width(80.dp))
        languages.forEach { (code, name) ->
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                RadioButton(
                    selected = selectedLanguage == code,
                    onClick = { onLanguageSelected(code) }
                )
                Text(name, fontSize = 13.sp)
            }
        }
    }
}
