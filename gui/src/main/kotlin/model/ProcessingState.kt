package model

import java.nio.file.Path

enum class ProcessingStatus {
    PENDING, PROCESSING, DONE, FAILED
}

data class FileItem(
    val path: Path,
    var status: ProcessingStatus = ProcessingStatus.PENDING,
    var message: String = "",
    var subtitlePath: Path? = null,
    var summaryPath: Path? = null
) {
    val fileName: String get() = path.fileName.toString()
}
