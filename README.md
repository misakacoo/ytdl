# ytdl

一个面向 Debian / Ubuntu 系的 YouTube 下载工具，基于 `yt-dlp`，提供更适合日常使用的交互式菜单、完整安装引导和 GitHub 一键安装体验。

适合希望在服务器、VPS 或日常 Linux 环境里快速完成 YouTube 视频和音频下载的用户。安装完成后，可以直接通过菜单执行下载、更新和维护操作，不需要手动拼接复杂命令。

- GitHub 仓库：`https://github.com/misakacoo/ytdl`
- 一键安装脚本：`https://raw.githubusercontent.com/misakacoo/ytdl/main/install.sh`

## 功能特性

- 支持 GitHub 一键安装，首次执行即可自动拉取完整项目
- 自动检测是否已安装，已安装时再次运行会直接进入主菜单
- 自动安装或升级 `ffmpeg`、Python 运行环境和项目依赖
- 支持 `自动最佳`、`1080p`、`4K`、`仅音频` 四种常用下载模式
- 视频下载后自动合并为 `mp4`
- 音频下载后自动提取并转换为 `mp3`
- 内置 `yt-dlp` 更新入口和完整重装入口
- 默认安装目录固定为 `/opt/ytdl`
- 默认下载目录固定为 `/opt/ytdl/downloads`

## 快速开始

推荐直接使用一键安装命令：

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/misakacoo/ytdl/main/install.sh)
```

如果系统没有 `curl`，也可以使用：

```bash
bash <(wget -qO- https://raw.githubusercontent.com/misakacoo/ytdl/main/install.sh)
```

安装完成后，默认可以通过下面的命令启动：

```bash
ytdl
```

## 一键安装

执行一键安装时，脚本会自动完成以下流程：

1. 检测当前系统是否为 Debian / Ubuntu 系
2. 检测本机是否已经安装过 `ytdl`
3. 如果尚未安装，提示是否开始完整安装
4. 自动从 GitHub 下载项目到 `/opt/ytdl`
5. 安装 `ffmpeg`、Python 环境和项目依赖
6. 安装完成后自动进入主菜单

## 手动安装

如果你更喜欢先克隆仓库再安装，可以这样使用：

```bash
git clone https://github.com/misakacoo/ytdl.git
cd ytdl
bash install.sh
```

## 使用方式

安装完成后，可以直接执行：

```bash
ytdl
```

也可以执行：

```bash
bash /opt/ytdl/install.sh
```

如果项目已经安装完成，这条命令会直接进入主菜单，而不会重复首次安装流程。

主菜单分为两类功能：

1. `升级与维护`
2. `下载`
3. `退出`

`升级与维护` 菜单包含：

1. 更新 `yt-dlp`
2. 重新执行完整安装
3. 返回上一级

`下载` 菜单包含：

1. 自动最佳视频
2. 1080p 视频
3. 4K 视频
4. 仅音频
5. 返回上一级

## 安装内容

完整安装流程会自动完成这些事情：

- 安装 `python3`、`python3-venv` 和必要系统工具
- 检测当前 `python3` 版本，必要时提示编译安装更新版本
- 下载并安装最新 `ffmpeg` 与 `ffprobe`
- 创建项目虚拟环境 `.venv`
- 安装 `yt-dlp`
- 创建默认下载目录 `downloads/`
- 注册全局命令 `ytdl`

## 目录说明

- `downloader.py`：交互式下载主程序
- `install.sh`：统一入口安装脚本
- `run.sh`：直接启动程序的脚本
- `requirements.txt`：Python 依赖

默认项目目录：

```bash
/opt/ytdl
```

默认下载目录：

```bash
/opt/ytdl/downloads
```

如果安装后不手动修改下载路径，视频和音频文件默认都会保存到 `/opt/ytdl/downloads`。

如需自定义安装路径，可在执行前设置：

```bash
export YTDL_HOME=/your/custom/path
bash <(curl -fsSL https://raw.githubusercontent.com/misakacoo/ytdl/main/install.sh)
```

## 注意事项

- 当前仅支持 Debian / Ubuntu 系系统
- 下载视频合并和音频转 `mp3` 依赖 `ffmpeg`
- 下载时如果缺少 `ffmpeg`，程序会提示是否自动执行完整安装
- 如果系统 `Python` 低于 `3.10`，安装脚本会提示是否自动升级；如果不升级，安装会终止
- `更新 yt-dlp` 通常需要 `Python 3.10+`
- 本项目默认只处理单个视频链接，不下载整个播放列表
- 某些视频可能受地区、年龄、登录或平台限制，`yt-dlp` 可能无法下载

## 发布前提醒

在 GitHub 一键安装生效前，请先把这些文件上传到仓库默认分支 `main`：

- `install.sh`
- `run.sh`
- `downloader.py`
- `requirements.txt`
- `README.md`
