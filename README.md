# iqihang-cli
用于iqihang爱启航视频播放和下载的命令行工具

本工具使用mpv播放器播放视频，使用ffmpeg下载视频。欲使用对应功能，需要事先自行安装和配置好mpv或ffmpeg，或者自行修改调用mpv和ffmpeg的部分的命令。

https://github.com/Tony15246/iqihang-cli/blob/35de5c16a34836c65378edee0764296c38d801ff/test.py#L189-L196

https://github.com/Tony15246/iqihang-cli/blob/35de5c16a34836c65378edee0764296c38d801ff/test.py#L199-L209

## 使用方法
在`test.py`同级目录下创建`config.json`文件，本件内容为账号的手机号和密码、以及mpv播放器的路径和ffmpeg的路径，格式如下。
``` json
{
    "phone": "xxxxxxxxxxx",
    "password": "xxxxxxxx",
    "mpv_path": "/your/path/to/mpv",
    "ffmpeg_path": "/your/path/to/ffmpeg"
}
```
使用如下命令安装依赖
```
pip install -r requirements.txt
```
使用如下命令运行脚本
```
python test.py
```
