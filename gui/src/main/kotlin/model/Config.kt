package model

data class SubtitleConfig(
    val outputDir: String? = null,
    val whisperModel: String = "base",
    val language: String? = null
)

data class AiConfig(
    val enabled: Boolean = false,
    val apiUrl: String = "https://api.openai.com/v1/chat/completions",
    val model: String = "",
    val apiKey: String = "",
    val promptTemplate: String = "请总结以下字幕内容，整理成清晰的要点，输出为 Markdown 格式："
) {
    fun isValid(): Boolean {
        return apiUrl.isNotBlank() && model.isNotBlank() && apiKey.isNotBlank()
    }
}
