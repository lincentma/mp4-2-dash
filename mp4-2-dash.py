# -*- coding:utf-8 -*-

################################################################################
#
# MP4-2-DASH
#
################################################################################
"""
@FileName: mp4-2-dash.py

@Author：lincentma  

@Create date: 2018/04/28

@description：通过FFmpeg和MpdBox工具生成MPEG-DASH视频文件的python脚本  

@Update date：
"""

import sys
import os

import argparse
import configparser
import subprocess


def get_args():
    """get args"""

    # 创建解析对象
    parser = argparse.ArgumentParser(description="MP4-2-DASH")
    parser.add_argument('-version', '-v', action='version',
                        version='%(prog)s 1.0')
    # 输入文件路径
    parser.add_argument('-input-dir', '-id', action='store',
                        dest='input_dir', help='input file dir')
    # 输入文件名称
    parser.add_argument('-input-name', '-if', action='store',
                        dest='input_file_name', help='input file name')
    # FFmpeg参数：视频尺寸集合（逗号分隔）
    parser.add_argument('-scale', '-s', action='store',
                        dest='video_scale', help='video scale')
    # FFmpeg参数：视频码率集合（读取配置文件获取）
    parser.add_argument('-bitrates', '-b', action='store',
                        dest='video_bitrates', help='video bitrates')
    # FFmpeg参数：x264-视频关键帧间隔
    parser.add_argument('-keyint', '-k', action='store',
                        dest='video_keyint', type=int, help='video keyint or gop')
    # MP4Box参数：dash分片长度
    parser.add_argument('-dash', '-d', action='store',
                        dest='segment_duration', type=int, help='segment duration')
    # MP4Box参数：类型名称
    parser.add_argument('-profile', '-p', action='store', dest='profile_name',
                        help='profile name: onDemand, live, main, simple, full, and two profiles from the DASH-IF: dashavc264:live, dashavc264:onDemand')
    # MP4Box参数：输出MPD文件名称
    parser.add_argument('-out', '-o', action='store',
                        dest='mpd_name', help='output file name for MPD')
    # MP4Box参数：视频分片名称
    parser.add_argument('-segment-name', '-sn', action='store', dest='segment_name',
                        help='sets the segment name for generated segments. can use like $RepresentationID$, $Number$, $Bandwidth$ and $Time')
    # MP4Box参数：BaseURL名称
    parser.add_argument('-base-url ', '-bu', action='store',
                        dest='base_url', help='sets the base url at MPD level')
    # 进行解析
    args = parser.parse_args()

    return args


def parse_args(args):
    """parse args"""

    

    input_dir = args.input_dir
    # 拼接处理文件的绝对路径
    input_file_name = input_dir + '\\' + args.input_file_name
    # 获取文件的当前路径（绝对路径）
    cur_path = os.path.dirname(os.path.realpath(__file__))
    # 获取config.ini的路径
    config_path = os.path.join(cur_path, 'config.ini')
    conf = configparser.ConfigParser()
    conf.read(config_path)

    video_scale = args.video_scale.split(',')
    video_scale_bitrates = {}

    # 读取配置文件信息，获取对应视频尺寸的视频码率
    for i in video_scale:
        scale = conf.get('scale', i)
        bitrates = conf.get('bitrates', i).split(',')
        video_scale_bitrates[scale] = bitrates
    video_keyint = args.video_keyint
    segment_duration = args.segment_duration
    profile_name = args.profile_name
    mpd_name = input_dir + '\\' + args.mpd_name
    segment_name = args.segment_name
    base_url = args.base_url
    
    return input_dir,input_file_name,video_scale_bitrates, video_keyint, segment_duration, profile_name, mpd_name, segment_name, base_url


def parse_ffmpeg(input_dir, input_file_name, video_scale_bitrates, video_keyint):
    """parse ffmpeg command"""

    ffmpeg_cmd = []
    ffmpeg_files = []

    # 音频处理
    audio_file = input_dir + '\\' + 'video_audio.mp4'
    # audio_cmd = 'ffmpeg' + ' ' + '-i ' + input_file_name + ' ' + '-c:a copy -vn' + ' ' + audio_file
    audio_cmd = ['ffmpeg', '-i', input_file_name,
                 '-c:a', 'copy', '-vn', audio_file]
    ffmpeg_cmd.append(audio_cmd)
    ffmpeg_files.append(audio_file)

    # 视频处理
    for scale in video_scale_bitrates:
        for bitrate in video_scale_bitrates[scale]:
            output_file = input_dir + '\\' + 'video_' + bitrate + '.mp4'
            # cmd = 'ffmpeg' + ' ' + '-i ' + input_file_name + ' ' + '-an -c:v  -x264opts keyint=%d:min-keyint=%d:no-scenecut' % (video_keyint, video_keyint) + ' ' + '-b:v %s -maxrate %s -bufsize %dk' % (bitrate, bitrate, int(bitrate[:-1]) // 2) + ' ' + '-vf scale=%s' % (scale) + ' ' + output_file
            keyint = 'keyint=%d:min-keyint=%d:no-scenecut' % (
                video_keyint, video_keyint)
            cmd = ['ffmpeg', '-i', input_file_name, '-y', '-c:v', 'libx264', '-x264opts', keyint, '-b:v', bitrate,
                   '-maxrate', bitrate, '-bufsize', str(int(bitrate[:-1]) // 2) + 'k', '-vf', 'scale=%s' % (scale), output_file]
            ffmpeg_files.append(output_file)
            ffmpeg_cmd.append(cmd)

    print(ffmpeg_cmd)
    return ffmpeg_files, ffmpeg_cmd


def parse_mp4box(ffmpeg_files, segment_duration, profile_name, segment_name, mpd_name):
    """parse mp4box command"""

    mp4box_cmd = ['MP4Box', '-dash', str(segment_duration), '-rap', '-frag-rap',
                  '-profile', profile_name, '-segment-name', segment_name, '-out', mpd_name]
    for file in ffmpeg_files:
        mp4box_cmd.append(file)

    print(mp4box_cmd)
    return mp4box_cmd


def run_cmd(cmd):
    """run command"""
    f = open("run.log", "a")
    proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT,
                            universal_newlines=True, shell=True, bufsize=0)
    stdoutdata, stderrdata = proc.communicate()
    if proc.returncode == 0:
        print("Job done.")
    else:
        print("ERROR")
        print(stdoutdata)
    f.close()
    proc.wait()

def main():
    """
    脚本处理主要流程：
    1.获取输入参数并校验。
    2.拼接FFmpeg和MP4Box语句命令。
    3.执行FFmpeg命令创建不同视频码率的mp4文件。
    4.执行MP4Box命令生成MPD文件和m4s视频分片文件。
    5.获取输出结果。

    脚本参数示例：
    python3 mp4-2-dash.py -id E:\GraduationProject\tools\BigBuckBunny\0428 -if BigBuckBunny_320x180.mp4 -s 90p,144p,180p -k 24 -d 2000 -p live -o test.mpd -sn BigBuckBunny_$Bandwidth$/BigBuckBunny_$Bandwidth$_segment_
    """
    print('================MP4-2-DASH begin==========================')
    args = get_args()
    input_dir,input_file_name,video_scale_bitrates, video_keyint, segment_duration, profile_name, mpd_name, segment_name, base_url = parse_args(args)
    ffmpeg_files, ffmpeg_cmd = parse_ffmpeg(input_dir,input_file_name,video_scale_bitrates, video_keyint)
    mp4box_cmd = parse_mp4box(ffmpeg_files, segment_duration, profile_name, segment_name, mpd_name)

    # for cmd in ffmpeg_cmd:
    #     run_cmd(cmd)
    
    run_cmd(mp4box_cmd)
    print('================MP4-2-DASH end============================')


if __name__ == '__main__':
    main()
    
