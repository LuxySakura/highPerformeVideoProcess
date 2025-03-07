import argparse
import subprocess
import sys
import os
from pathlib import Path

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

def embed_subtitle(video_path, subtitle_path, output_path=None):
    """将字幕嵌入视频文件"""
    if not os.path.exists(video_path):
        print(f'错误：视频文件不存在: {video_path}')
        return False
    
    if not os.path.exists(subtitle_path):
        print(f'错误：字幕文件不存在: {subtitle_path}')
        return False

    # 如果未指定输出路径，在原文件名后添加_with_subtitle
    if output_path is None:
        video_file = Path(video_path)
        output_path = str(video_file.parent / f"{video_file.stem}_with_subtitle{video_file.suffix}")

    # 检查是否有GPU可用
    use_gpu = check_gpu()
    
    # 基础命令参数
    ffmpeg_command = [
        'ffmpeg',
        '-y',
        '-threads', '0',
    ]

    # GPU加速相关参数
    if use_gpu:
        ffmpeg_command.extend([
            '-hwaccel', 'cuda',
            '-hwaccel_output_format', 'cuda',
        ])

    # 输入参数
    ffmpeg_command.extend([
        '-i', video_path,
        '-i', subtitle_path,
    ])

    # 输出参数
    if use_gpu:
        ffmpeg_command.extend([
            '-c:v', 'h264_nvenc',
            '-preset', 'p7',
            '-tune', 'hq',
            '-rc', 'vbr',
            '-cq', '20',
            '-b:v', '8M',
            '-maxrate', '10M',
            '-bufsize', '16M',
        ])
    else:
        ffmpeg_command.extend([
            '-c:v', 'libx264',
            '-preset', 'faster',
            '-crf', '23',
        ])

    # 音频和字幕参数
    ffmpeg_command.extend([
        '-c:a', 'copy',
        '-c:s', 'mov_text',
        '-metadata:s:s:0', 'language=chi',
        output_path
    ])

    try:
        print(f'开始处理视频: {video_path}')
        print(f'使用{"GPU" if use_gpu else "CPU"}进行编码')
        
        process = subprocess.Popen(
            ffmpeg_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # 实时显示处理进度
        while True:
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        if process.returncode == 0:
            print(f'\n成功！视频已保存为: {output_path}')
            return True
        else:
            print('\n错误：字幕嵌入失败')
            return False

    except Exception as e:
        print(f'发生错误: {str(e)}')
        return False

def main():
    parser = argparse.ArgumentParser(description='视频字幕嵌入工具')
    parser.add_argument('video', help='视频文件路径')
    parser.add_argument('subtitle', help='字幕文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径（可选）')
    args = parser.parse_args()

    if not check_ffmpeg():
        sys.exit(1)

    embed_subtitle(args.video, args.subtitle, args.output)

if __name__ == '__main__':
    # python subtitle_embedder.py "视频文件路径" "字幕文件路径" -o "输出文件路径(可选)"
    main()
    