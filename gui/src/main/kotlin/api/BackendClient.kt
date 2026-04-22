package api

import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.annotations.SerializedName
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import model.AiConfig
import model.SubtitleConfig
import java.io.IOException
import java.nio.file.Path

data class ProcessRequest(
    val video_path: String,
    val output_dir: String?,
    val whisper_model: String,
    val language: String?,
    val enable_ai: Boolean,
    val ai_config: AiConfigRequest?
)

data class AiConfigRequest(
    val api_url: String,
    val model: String,
    val api_key: String,
    val prompt_template: String
)

data class ProcessResponse(
    val success: Boolean,
    val subtitle_path: String?,
    val summary_path: String?,
    val subtitle_text: String?,
    val summary_text: String?,
    val message: String
)

data class TestAIRequest(
    val ai_config: AiConfigRequest
)

data class TestAIResponse(
    val success: Boolean,
    val message: String
)

data class HealthResponse(
    val healthy: Boolean,
    val message: String
)

import java.util.concurrent.TimeUnit

class BackendClient(
    private val baseUrl: String = "http://127.0.0.1:8765"
) {
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.MINUTES)  // Whisper 转录可能需要很长时间
        .build()
    private val gson = Gson()
    private val contentType = "application/json".toMediaType()

    suspend fun checkHealth(): Result<HealthResponse> {
        return try {
            val request = Request.Builder()
                .url("$baseUrl/health")
                .get()
                .build()

            val response = client.newCall(request).execute()
            if (response.isSuccessful) {
                val body = response.body?.string() ?: return Result.failure(IOException("Empty response"))
                val health = gson.fromJson(body, HealthResponse::class.java)
                Result.success(health)
            } else {
                Result.failure(IOException("HTTP ${response.code}: ${response.message}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun testAi(aiConfig: AiConfig): Result<String> {
        return try {
            val requestAiConfig = AiConfigRequest(
                api_url = aiConfig.apiUrl,
                model = aiConfig.model,
                api_key = aiConfig.apiKey,
                prompt_template = aiConfig.promptTemplate
            )
            val requestBody = TestAIRequest(requestAiConfig)
            val json = gson.toJson(requestBody)
            val body = json.toRequestBody(contentType)

            val request = Request.Builder()
                .url("$baseUrl/test-ai")
                .post(body)
                .build()

            val response = client.newCall(request).execute()
            if (response.isSuccessful) {
                val bodyStr = response.body?.string() ?: return Result.failure(IOException("Empty response"))
                val result = gson.fromJson(bodyStr, TestAIResponse::class.java)
                if (result.success) {
                    Result.success(result.message)
                } else {
                    Result.failure(IOException(result.message))
                }
            } else {
                val errorBody = response.body?.string() ?: response.message
                Result.failure(IOException("HTTP ${response.code}: $errorBody"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun processVideo(
        videoPath: Path,
        subtitleConfig: SubtitleConfig,
        aiConfig: AiConfig
    ): Result<ProcessResponse> {
        return try {
            val requestAiConfig = if (aiConfig.enabled) {
                AiConfigRequest(
                    api_url = aiConfig.apiUrl,
                    model = aiConfig.model,
                    api_key = aiConfig.apiKey,
                    prompt_template = aiConfig.promptTemplate
                )
            } else {
                null
            }

            val request = ProcessRequest(
                video_path = videoPath.toAbsolutePath().toString(),
                output_dir = subtitleConfig.outputDir,
                whisper_model = subtitleConfig.whisperModel,
                language = subtitleConfig.language,
                enable_ai = aiConfig.enabled,
                ai_config = requestAiConfig
            )

            val json = gson.toJson(request)
            val body = json.toRequestBody(contentType)

            val httpRequest = Request.Builder()
                .url("$baseUrl/process")
                .post(body)
                .build()

            val response = client.newCall(httpRequest).execute()
            if (response.isSuccessful) {
                val bodyStr = response.body?.string() ?: return Result.failure(IOException("Empty response"))
                val result = gson.fromJson(bodyStr, ProcessResponse::class.java)
                Result.success(result)
            } else {
                val errorBody = response.body?.string() ?: response.message
                Result.failure(IOException("HTTP ${response.code}: $errorBody"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    fun close() {
        client.dispatcher.executorService.shutdown()
    }
}
