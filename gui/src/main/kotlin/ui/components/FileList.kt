package ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import model.FileItem
import model.ProcessingStatus

@Composable
fun FileList(
    files: List<FileItem>,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier
            .fillMaxWidth()
            .heightIn(max = 200.dp)
            .background(Color.LightGray.copy(alpha = 0.2f), RoundedCornerShape(8.dp))
            .padding(8.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        if (files.isEmpty()) {
            item {
                Box(
                    modifier = Modifier.fillMaxWidth().padding(16.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text("没有文件，拖放视频文件开始", color = Color.Gray, fontSize = 14.sp)
                }
            }
        } else {
            items(files) { file ->
                FileItemRow(file)
            }
        }
    }
}

@Composable
fun FileItemRow(file: FileItem) {
    val statusColor = when (file.status) {
        ProcessingStatus.PENDING -> Color.Gray
        ProcessingStatus.PROCESSING -> Color(0xFFE6A800) // Orange
        ProcessingStatus.DONE -> Color(0xFF008000) // Green
        ProcessingStatus.FAILED -> Color(0xFFCC0000) // Red
    }

    val statusText = when (file.status) {
        ProcessingStatus.PENDING -> "等待中"
        ProcessingStatus.PROCESSING -> "处理中..."
        ProcessingStatus.DONE -> "完成"
        ProcessingStatus.FAILED -> "失败"
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.White, RoundedCornerShape(4.dp))
            .padding(horizontal = 8.dp, vertical = 6.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = file.fileName,
            fontSize = 14.sp,
            modifier = Modifier.weight(1f)
        )
        Text(
            text = statusText,
            color = statusColor,
            fontSize = 13.sp
        )
    }
}
