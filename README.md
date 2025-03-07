# 高性能视频处理工具
A Quick Python Scripts allows you to use ffmpeg to download &amp; trans online .m3u8 videos to .mp4
这是一个基于FFmpeg的高性能视频处理工具集，支持GPU加速（NVIDIA CUDA），包含以下功能：

- M3U8视频下载与转换
- 字幕嵌入视频

## 前提条件

- 安装 [FFmpeg](https://ffmpeg.org/download.html) 并添加到系统环境变量
- （可选）NVIDIA GPU 和 CUDA 支持，用于硬件加速

## 功能模块

### 1. M3U8视频下载器 (downloader.py)

将M3U8格式的视频流下载并转换为MP4格式。

#### 特性：
- 自动检测并利用NVIDIA GPU加速（如可用）
- 高质量视频编码
- 实时显示下载和转换进度
- 自动创建video目录存储输出文件

#### 使用方法：

```bash
python downloader.py <M3U8链接> <输出文件名>
```

参数说明：
- <M3U8链接> : 要下载的M3U8视频URL
- <输出文件名> : 输出的MP4文件名（如不包含.mp4后缀会自动添加） 
示例：
```bash
python downloader.py https://example.com/video.m3u8 我的视频
 ```

输出文件将保存在项目目录下的 video 文件夹中。

### 2. 字幕嵌入工具 (embedder.py)

将外部字幕文件嵌入到视频中。

#### 特性：
- 支持多种字幕格式（SRT, ASS等）
- 自动检测并利用NVIDIA GPU加速（如可用）
- 保持原视频质量
- 实时显示处理进度

#### 使用方法：

```bash
python embedder.py <视频文件路径> <字幕文件路径> [-o <输出文件路径>]
```

参数说明：
- <视频文件路径> : 原始视频文件的路径
- <字幕文件路径> : 字幕文件的路径
- -o, --output : （可选）输出文件路径，如不指定则在原文件名后添加"_with_subtitle" 示例：
```bash
python embedder.py "C:\Videos\movie.mp4" "C:\Subtitles\movie.srt"
```

或指定输出路径：

```bash
python embedder.py "C:\Videos\movie.mp4" "C:\Subtitles\movie.srt" -o "C:\Output\movie_subbed.mp4"
```

## 性能优化
两个工具都会自动检测系统中是否有可用的NVIDIA GPU：

- 如果检测到GPU，将使用NVIDIA NVENC硬件编码器进行加速
- 如果没有GPU，将使用高效的CPU编码设置
## 注意事项
- 确保FFmpeg已正确安装并添加到系统环境变量
- 对于GPU加速，需要安装NVIDIA驱动和CUDA支持
- 处理大型视频文件可能需要较长时间，请耐心等待