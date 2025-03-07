import argparse
import subprocess
import sys
import os

def check_ffmpeg():
    """检查是否安装了ffmpeg"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True)
        return True
    except FileNotFoundError:
        print('错误：未找到ffmpeg。请确保ffmpeg已安装并添加到系统环境变量中。')
        return False

def check_gpu():
    """检查是否有可用的NVIDIA GPU"""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def download_and_convert(m3u8_url, output_name):
    """下载m3u8视频并转换为mp4格式"""
    # 确保video文件夹存在
    video_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'video')
    if not os.path.exists(video_dir):
        os.makedirs(video_dir)

    # 处理输出文件名
    if not output_name.endswith('.mp4'):
        output_name += '.mp4'
    output_path = os.path.join(video_dir, output_name)

    # 检查是否有GPU可用
    use_gpu = check_gpu()
    
    # 基础命令参数
    ffmpeg_command = [
        'ffmpeg',
        '-y',  # 自动覆盖输出文件
        '-threads', '0',  # 自动选择最优线程数
    ]

    # GPU加速相关参数
    if use_gpu:
        ffmpeg_command.extend([
            '-hwaccel', 'cuda',
            '-hwaccel_device', '0',
            '-extra_hw_frames', '3',
        ])

    # 输入参数
    ffmpeg_command.extend([
        '-i', m3u8_url,
    ])

    # 输出参数
    if use_gpu:
        ffmpeg_command.extend([
            '-c:v', 'h264_nvenc',
            '-preset', 'p7',
            '-rc', 'vbr',
            '-cq', '20',
            '-b:v', '8M',
            '-maxrate', '10M',
            '-bufsize', '16M',
            '-vsync', '0',  # 处理可变帧率
        ])
    else:
        ffmpeg_command.extend([
            '-c:v', 'libx264',     # CPU编码器
            '-preset', 'faster',    # 较快的预设
            '-crf', '23',          # 质量参数
        ])

    # 音频参数和输出文件
    ffmpeg_command.extend([
        '-c:a', 'aac',            # 音频编码器
        '-b:a', '192k',           # 音频比特率
        output_path              # 使用完整路径
    ])

    try:
        print(f'开始下载并转换视频: {m3u8_url}')
        print(f'使用{"GPU" if use_gpu else "CPU"}进行编码')
        print(f'视频将保存到: {output_path}')
        
        process = subprocess.Popen(
            ffmpeg_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # 实时显示下载进度
        while True:
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        if process.returncode == 0:
            print(f'\n成功！视频已保存为: {output_path}')
        else:
            print('\n错误：视频下载或转换失败')

    except Exception as e:
        print(f'发生错误: {str(e)}')

def main():
    parser = argparse.ArgumentParser(description='M3U8视频下载器和转换器')
    parser.add_argument('url', help='M3U8视频链接')
    parser.add_argument('output', help='输出文件名（.mp4格式）')
    args = parser.parse_args()

    if not check_ffmpeg():
        sys.exit(1)

    download_and_convert(args.url, args.output)

if __name__ == '__main__':
    main()