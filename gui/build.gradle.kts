import org.jetbrains.compose.desktop.application.dsl.TargetFormat

plugins {
    kotlin("jvm") version "1.9.20"
    id("org.jetbrains.compose") version "1.5.11"
}

group = "com.example"
version = "1.0.0"

dependencies {
    implementation(compose.desktop.currentOs)
    // OkHttp for HTTP client
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    // Gson for JSON parsing
    implementation("com.google.code.gson:gson:2.10.1")
    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
}

kotlin {
    jvmToolchain(17)
}

compose.desktop {
    application {
        mainClass = "MainKt"

        nativeDistributions {
            targetFormats(TargetFormat.Exe)
            packageName = "SubtitleExtractor"
            packageVersion = "1.0.0"
            vendor = "Local Build"

            // Include all dependencies for Windows
            modules("jdk.unsupported")
        }
    }
}
