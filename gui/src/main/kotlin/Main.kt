import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material.MaterialTheme
import androidx.compose.material.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Window
import androidx.compose.ui.window.application
import androidx.compose.ui.window.rememberWindowState
import api.BackendClient
import kotlinx.coroutines.GlobalScope
import ui.MainScreen
import java.io.File
import java.io.IOException
import java.net.ServerSocket
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

fun main() = application {
    // Find an available port
    val port = findAvailablePort()
    // Start Python backend in a separate process
    val pythonProcess = startPythonBackend(port)
    // Wait a moment for server to start
    Thread.sleep(1500)
    // Create backend client
    val client = BackendClient(baseUrl = "http://127.0.0.1:$port")

    Window(
        onCloseRequest = {
            // Close client and terminate Python process
            client.close()
            pythonProcess?.destroy()
            exitApplication()
        },
        title = "字幕提取工具",
        state = rememberWindowState(width = 600.dp, height = 800.dp)
    ) {
        MaterialTheme {
            Surface(
                modifier = Modifier.fillMaxSize(),
                color = MaterialTheme.colors.background
            ) {
                AppContent(client)
            }
        }
    }

    // Shutdown hook to clean up Python process
    Runtime.getRuntime().addShutdownHook(Thread {
        pythonProcess?.destroy()
    })
}

@Composable
fun AppContent(client: BackendClient) {
    MainScreen(
        backendClient = client,
        scope = GlobalScope,
        modifier = Modifier.fillMaxSize()
    )
}

fun findAvailablePort(): Int {
    return try {
        ServerSocket(0).use { socket ->
            socket.localPort
        }
    } catch (e: IOException) {
        8765 // default
    }
}

fun startPythonBackend(port: Int): Process? {
    return try {
        // Get current working directory (should be gui/ during development)
        val currentDir = File(System.getProperty("user.dir"))
        println("Current working directory: ${currentDir.absolutePath}")

        // Find project root by searching for backend/ directory
        var projectRoot = currentDir
        var foundBackend = File(projectRoot, "backend/main.py").exists()
        var searchDepth = 0
        while (!foundBackend && searchDepth < 5) {
            val parent = projectRoot.parentFile
            if (parent != null) {
                projectRoot = parent
                foundBackend = File(projectRoot, "backend/main.py").exists()
                searchDepth++
            } else {
                break
            }
        }

        println("Project root: ${projectRoot.absolutePath}")

        // Create logs directory inside gui/
        val logsDir = File(projectRoot, "gui/logs")
        logsDir.mkdirs()

        // Create log file with timestamp
        val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
        val logFile = File(logsDir, "backend_${timestamp}.log")

        // Path to the backend main script
        val backendScript = File(projectRoot, "backend/main.py")
        println("Backend script: ${backendScript.absolutePath}, exists: ${backendScript.exists()}")

        // Try to find Python executable in embedded location
        val pythonCmd = findPythonExecutable(projectRoot)
        println("Using Python: $pythonCmd")

        val command = listOf(
            pythonCmd,
            backendScript.absolutePath,
            port.toString(),
        )

        println("Starting Python backend: $command with port $port")
        println("Log file: ${logFile.absolutePath}")

        val processBuilder = ProcessBuilder(command)
        processBuilder.environment()["PATH"] =
            "${projectRoot.absolutePath}${File.pathSeparator}${projectRoot.absolutePath}/ffmpeg-master-latest-win64-gpl-shared/bin${File.pathSeparator}${System.getenv("PATH")}"
        // Redirect output to log file instead of discarding
        processBuilder.redirectOutput(logFile)
        processBuilder.redirectErrorStream(true) // Merge stderr into stdout

        val process = processBuilder.start()
        println("Python backend started with PID ${process.pid()}")
        process
    } catch (e: Exception) {
        println("Failed to start Python backend: ${e.message}")
        e.printStackTrace()
        null
    }
}

fun findPythonExecutable(projectRoot: File): String {
    // Check for embedded Python first (for packaged app)
    val embeddedPython = File(projectRoot, "python/python.exe")
    println("Checking embedded Python: ${embeddedPython.absolutePath}, exists: ${embeddedPython.exists()}")
    if (embeddedPython.exists()) {
        return embeddedPython.absolutePath
    }

    // Check in common locations
    val candidates = listOf(
        "python",
        "python3",
        "py",
        "C:/Python311/python.exe",
        "C:/Python310/python.exe",
    )

    for (candidate in candidates) {
        try {
            val process = Runtime.getRuntime().exec("$candidate --version")
            val exitCode = process.waitFor()
            if (exitCode == 0) {
                return candidate
            }
        } catch (e: Exception) {
            continue
        }
    }

    // Fallback to just "python" and hope for the best during development
    return "python"
}
