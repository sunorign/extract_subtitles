package ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerHoverIcon
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.awt.LocalWindow
import java.awt.Cursor
import java.awt.datatransfer.DataFlavor
import java.awt.dnd.DnDConstants
import java.awt.dnd.DropTarget
import java.awt.dnd.DropTargetDropEvent
import java.io.File
import java.nio.file.Path
import kotlin.collections.List

@Composable
fun DropZone(
    onFilesDropped: (List<Path>) -> Unit,
    modifier: Modifier = Modifier
) {
    val isDragging = remember { mutableStateOf(false) }
    val window = LocalWindow.current

    DisposableEffect(window) {
        val dropTarget = object : DropTarget() {
            override fun dragEnter(dtde: DropTargetDropEvent?) {
                isDragging.value = true
                super.dragEnter(dtde)
            }

            override fun dragExit(p0: java.awt.dnd.DropTargetEvent?) {
                isDragging.value = false
                super.dragExit(p0)
            }

            override fun drop(dtde: DropTargetDropEvent) {
                dtde.acceptDrop(DnDConstants.ACTION_COPY)
                val transferable = dtde.transferable
                @Suppress("UNCHECKED_CAST")
                val files = transferable.getTransferData(DataFlavor.javaFileListFlavor) as List<File>
                val paths = files.map { it.toPath() }
                onFilesDropped(paths)
                dtde.dropComplete(true)
                isDragging.value = false
            }
        }
        window.addDropTarget(dropTarget)

        onDispose {
            dropTarget.removeDropTargetListener(dropTarget)
        }
    }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(120.dp)
            .border(
                width = 2.dp,
                color = if (isDragging.value) Color.Blue else Color.Gray,
                shape = RoundedCornerShape(8.dp)
            )
            .background(
                if (isDragging.value) Color.Blue.copy(alpha = 0.1f) else Color.LightGray.copy(alpha = 0.3f),
                RoundedCornerShape(8.dp)
            )
            .pointerHoverIcon(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR)),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = if (isDragging.value) "释放文件开始处理" else "拖放视频文件到这里",
            fontSize = 18.sp,
            color = if (isDragging.value) Color.Blue else Color.DarkGray
        )
    }
}
