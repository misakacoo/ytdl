# ytdl

一个面向 Debian / Ubuntu 的 YouTube 下载工具，基于 `yt-dlp`，提供交互式菜单、一键安装、项目更新和卸载能力。

- GitHub：`https://github.com/misakacoo/ytdl`
- 一键安装：`https://raw.githubusercontent.com/misakacoo/ytdl/main/install.sh`

## 快速开始

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/misakacoo/ytdl/main/install.sh)
```

如果没有 `curl`：

```bash
bash <(wget -qO- https://raw.githubusercontent.com/misakacoo/ytdl/main/install.sh)
```

安装完成后可直接使用：

```bash
ytdl
ytdl "https://www.youtube.com/watch?v=xxxxxxxxxxx"
ytdl batch
```

## 功能概览

- 支持自动最佳、`1080p`、`4K`、仅音频四种下载模式
- 支持批量下载，默认读取 `/opt/ytdl/url.txt`
- 视频自动合并为 `mp4`
- 音频自动提取并转换为 `mp3`
- 支持修改默认下载路径
- 支持更新 `yt-dlp`
- 支持更新 `ytdl` 项目本身
- 支持卸载项目，并按需删除下载目录或静态版 `ffmpeg`

## 安装与目录

- 默认安装目录：`/opt/ytdl`
- 默认下载目录：`/opt/ytdl/download`
- 下载目录配置：`/opt/ytdl/download_path.txt`
- 批量链接文件：`/opt/ytdl/url.txt`

首次安装时会自动：

- 安装或升级 `ffmpeg`、Python 运行环境和依赖
- 创建虚拟环境 `.venv`
- 提示设置默认下载路径
- 注册全局命令 `ytdl`

如需自定义安装路径，可先设置：

```bash
export YTDL_HOME=/your/custom/path
bash <(curl -fsSL https://raw.githubusercontent.com/misakacoo/ytdl/main/install.sh)
```

## 菜单说明

主菜单：

1. `升级与维护`
2. `单个下载`
3. `批量下载`
4. `修改下载路径`
5. `退出`

`升级与维护` 菜单：

1. 更新 `yt-dlp`
2. 更新 `ytdl`
3. 重新执行完整安装
4. 卸载 `ytdl`
5. 返回上一级

`单个下载` 菜单：

1. 自动最佳视频
2. 1080p 视频
3. 4K 视频
4. 仅音频
5. 返回上一级

`批量下载` 菜单：

1. 批量下载视频
2. 批量下载音频
3. 返回上一级

## 批量下载

批量下载读取 `/opt/ytdl/url.txt`，一行一个链接。

- 空行会忽略
- 以 `#` 开头的行会忽略

示例：

```text
https://www.youtube.com/watch?v=video_a
https://www.youtube.com/watch?v=video_b
# 注释
https://www.youtube.com/watch?v=video_c
```

## 更新与卸载

更新说明：

- 更新 `yt-dlp`：只升级当前虚拟环境里的 `yt-dlp`
- 更新 `ytdl`：从 GitHub 拉取最新项目代码，保留 `.venv`、`url.txt`、`download_path.txt` 和下载目录，完成后自动重启程序加载新版本

卸载默认删除：

- 当前安装的项目目录
- 全局命令 `/usr/local/bin/ytdl`

卸载可选删除：

- 项目目录外的下载目录
- `/usr/local/bin/ffmpeg`
- `/usr/local/bin/ffprobe`

卸载默认不会删除：

- `python3`
- `python3-venv`
- `apt` 安装的系统工具和构建依赖
- 其他项目可能共用的 Python 版本

## 注意事项

- 当前仅支持 Debian / Ubuntu 系系统
- 下载视频合并和音频转 `mp3` 依赖 `ffmpeg`
- 如果系统 Python 低于 `3.10`，安装脚本会提示升级
- 单个下载默认只处理单个视频链接，不下载整个播放列表
- 某些视频可能受地区、年龄、登录或平台限制，`yt-dlp` 可能无法下载
