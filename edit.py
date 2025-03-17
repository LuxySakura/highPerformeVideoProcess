import argparse
import subprocess
import sys
import os
from pathlib import Path
import re

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

def get_video_duration(video_path):
    """获取视频总时长"""
    if not os.path.exists(video_path):
        print(f'错误：视频文件不存在: {video_path}')
        return None
    
    try:
        # 使用ffprobe获取视频时长
        cmd = [
            'ffprobe', 
            '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f'错误：无法获取视频时长: {result.stderr}')
            return None
        
        # 将秒转换为时:分:秒格式
        duration_seconds = float(result.stdout.strip())
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    except Exception as e:
        print(f'获取视频时长时发生错误: {str(e)}')
        return None

def time_to_seconds(time_str):
    """将时:分:秒格式转换为秒"""
    # 检查时间格式是否正确
    if not re.match(r'^\d{2}:\d{2}:\d{2}$', time_str):
        print(f'错误：时间格式不正确: {time_str}，应为HH:MM:SS格式')
        return None
    
    h, m, s = map(int, time_str.split(':'))
    return h * 3600 + m * 60 + s

def seconds_to_time(seconds):
    """将秒转换为时:分:秒格式"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def edit_video(video_path, from_end_start, from_end_end, output_name=None):
    """剪辑视频
    
    参数:
        video_path: 视频文件路径
        from_end_start: 距离视频结束的开始时间点 (HH:MM:SS格式)
        from_end_end: 距离视频结束的结束时间点 (HH:MM:SS格式)
        output_name: 输出文件名（可选）
    """
    if not os.path.exists(video_path):
        print(f'错误：视频文件不存在: {video_path}')
        return False
    
    # 获取视频总时长
    total_duration = get_video_duration(video_path)
    if not total_duration:
        return False
    
    # 将总时长转换为秒
    total_seconds = time_to_seconds(total_duration)
    if total_seconds is None:
        return False
    
    # 将距离结束的时间转换为距离开始的时间
    from_start_seconds = total_seconds - time_to_seconds(from_end_start)
    from_start_end_seconds = total_seconds - time_to_seconds(from_end_end)
    duration_seconds = from_start_end_seconds - from_start_seconds
    
    # 确保时间点有效
    if from_start_seconds < 0 or from_start_end_seconds < 0:
        print('错误：指定的时间点超出了视频总时长')
        return False
    
    if from_start_seconds >= from_start_end_seconds:
        print('错误：开始时间必须小于结束时间')
        return False
    
    # 转换为ffmpeg可用的时间格式
    start_time = seconds_to_time(from_start_seconds)
    end_time = seconds_to_time(from_start_end_seconds)
    duration_time = seconds_to_time(duration_seconds)
    
    # 如果未指定输出路径，在原文件名后添加_edited
    if output_name is None:
        video_file = Path(video_path)
        output_path = str(video_file.parent / f"{video_file.stem}_edited{video_file.suffix}")
    else:
        # 确保输出文件有正确的扩展名
        if not output_name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
            output_name += Path(video_path).suffix
        
        # 确保video文件夹存在
        video_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'video')
        if not os.path.exists(video_dir):
            os.makedirs(video_dir)
        
        output_path = os.path.join(video_dir, output_name)
    
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

    # 输入参数，包括剪辑时间
    ffmpeg_command.extend([
        '-ss', start_time,
        # '-to', end_time,
        '-i', video_path,
        '-t', duration_time,
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

    # 音频参数
    ffmpeg_command.extend([
        '-c:a', 'aac',
        '-b:a', '192k',
        output_path
    ])

    try:
        print(f'开始剪辑视频: {video_path}')
        print(f'剪辑时间段: {start_time} 到 {end_time}')
        print(f"使用{'GPU' if use_gpu else 'CPU'}进行编码")
        
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
            print(f'\n成功！剪辑后的视频已保存为: {output_path}')
            return True
        else:
            print('\n错误：视频剪辑失败')
            return False

    except Exception as e:
        print(f'发生错误: {str(e)}')
        return False

def main():
    parser = argparse.ArgumentParser(description='视频剪辑工具')
    parser.add_argument('video', help='视频文件路径')
    parser.add_argument('start', help='距离视频结束的开始时间点 (HH:MM:SS格式)')
    parser.add_argument('end', help='距离视频结束的结束时间点 (HH:MM:SS格式)')
    parser.add_argument('-o', '--output', help='输出文件名（可选）')
    args = parser.parse_args()

    if not check_ffmpeg():
        sys.exit(1)

    edit_video(args.video, args.start, args.end, args.output)

if __name__ == '__main__':
    # python edit.py "视频文件路径" "距离结束的开始时间" "距离结束的结束时间" -o "输出文件名(可选)"
    main()