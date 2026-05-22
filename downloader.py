#!/usr/bin/env python3
"""Interactive YouTube downloader powered by yt-dlp."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from shutil import which

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_DOWNLOAD_DIR = PROJECT_DIR / "downloads"


def ask_non_empty(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("输入不能为空，请重新输入。")


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        value = input(f"{prompt} {suffix}：").strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("无效输入，请输入 y 或 n。")


def ask_main_action() -> str:
    while True:
        print("\n请选择功能：")
        print("1. 升级与维护")
        print("2. 下载")
        print("3. 退出")
        choice = input("请输入选项 [1/2/3]：").strip()
        if choice == "1":
            return "maintenance"
        if choice == "2":
            return "download"
        if choice == "3":
            return "exit"
        print("无效选项，请输入 1、2 或 3。")


def ask_maintenance_action() -> str:
    while True:
        print("\n请选择维护操作：")
        print("1. 更新 yt-dlp")
        print("2. 重新执行完整安装")
        print("3. 返回上一级")
        choice = input("请输入选项 [1/2/3]：").strip()
        if choice == "1":
            return "update"
        if choice == "2":
            return "reinstall"
        if choice == "3":
            return "back"
        print("无效选项，请输入 1、2 或 3。")


def ask_download_profile() -> str:
    while True:
        print("\n请选择下载类型：")
        print("1. 自动最佳视频（不限制分辨率，自动合并为 MP4）")
        print("2. 1080p 视频（不超过 1080p，自动合并为 MP4）")
        print("3. 4K 视频（不超过 4K，自动合并为 MP4）")
        print("4. 仅音频（提取并转换为 MP3）")
        print("5. 返回上一级")
        choice = input("请输入选项 [1/2/3/4/5]：").strip()
        if choice == "1":
            return "best"
        if choice == "2":
            return "1080p"
        if choice == "3":
            return "4k"
        if choice == "4":
            return "audio"
        if choice == "5":
            return "back"
        print("无效选项，请输入 1、2、3、4 或 5。")


def ask_output_dir() -> Path:
    raw_value = input(
        f"下载目录（直接回车使用默认目录：{DEFAULT_DOWNLOAD_DIR}）："
    ).strip()
    target_dir = Path(raw_value).expanduser() if raw_value else DEFAULT_DOWNLOAD_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def build_options(profile: str, output_dir: Path) -> dict:
    base_options = {
        "outtmpl": str(output_dir / "%(title).200B [%(id)s].%(ext)s"),
        "noplaylist": True,
        "restrictfilenames": False,
    }

    if profile in {"best", "1080p", "4k"}:
        format_selector = "bestvideo*+bestaudio/best"
        if profile == "1080p":
            format_selector = "bestvideo*[height<=1080]+bestaudio/best[height<=1080]"
        elif profile == "4k":
            format_selector = "bestvideo*[height<=2160]+bestaudio/best[height<=2160]"
        base_options.update(
            {
                "format": format_selector,
                "merge_output_format": "mp4",
            }
        )
    else:
        base_options.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
        )

    return base_options


def ensure_dependencies(profile: str) -> None:
    if profile in {"best", "1080p", "4k", "audio"} and which("ffmpeg") is None:
        print("警告：未检测到 ffmpeg。视频合并或音频转换可能失败。")
        install_now = ask_yes_no(
            "是否现在自动运行 Debian/Ubuntu 安装脚本安装 ffmpeg？",
            default=True,
        )
        if install_now:
            print("\n开始执行安装脚本，请稍候...\n")
            subprocess.run(
                ["bash", str(PROJECT_DIR / "install.sh"), "--install-only"],
                check=True,
                cwd=PROJECT_DIR,
            )
            if which("ffmpeg") is not None:
                print("\nffmpeg 安装完成，继续下载。\n")
            else:
                print("\n安装脚本执行完成，但仍未检测到 ffmpeg。\n")
        else:
            print("已跳过自动安装，你也可以稍后手动执行：bash install.sh")


def warn_python_version() -> None:
    if sys.version_info < (3, 10):
        current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        print(
            "提示：当前 Python 版本为 "
            f"{current}，`yt-dlp` 新版本要求 Python 3.10+。"
        )
        print("如果更新后版本没有变化，请先升级 Python 再重新安装项目环境。")


def update_yt_dlp() -> None:
    warn_python_version()
    print("\n开始更新 yt-dlp，请稍候...\n")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip", "yt-dlp"],
        check=True,
    )
    subprocess.run([sys.executable, "-m", "yt_dlp", "--version"], check=True)
    print("\nyt-dlp 更新完成。\n")


def run_full_install() -> None:
    print("\n开始执行完整安装，请稍候...\n")
    subprocess.run(
        ["bash", str(PROJECT_DIR / "install.sh"), "--install-only"],
        check=True,
        cwd=PROJECT_DIR,
    )
    print("\n完整安装执行完成。\n")


def download(url: str, profile: str, output_dir: Path) -> None:
    options = build_options(profile, output_dir)
    ensure_dependencies(profile)

    with YoutubeDL(options) as ydl:
        ydl.download([url])


def handle_maintenance() -> None:
    while True:
        action = ask_maintenance_action()
        if action == "back":
            return
        if action == "update":
            update_yt_dlp()
            continue
        run_full_install()


def handle_download() -> None:
    while True:
        profile = ask_download_profile()
        if profile == "back":
            return

        url = ask_non_empty("请输入 YouTube 视频/音频链接：")
        output_dir = ask_output_dir()

        print("\n开始下载，请稍候...\n")
        download(url, profile, output_dir)
        print(f"\n下载完成，文件已保存到：{output_dir}\n")

        again = ask_yes_no("是否继续下载下一个链接？", default=False)
        if not again:
            return


def main() -> int:
    print("YouTube 下载工具（基于 yt-dlp）")
    print("按 Ctrl+C 可以随时退出。\n")

    while True:
        try:
            action = ask_main_action()
            if action == "maintenance":
                handle_maintenance()
                continue
            if action == "download":
                handle_download()
                continue
            if action == "exit":
                print("已退出。")
                return 0
        except KeyboardInterrupt:
            print("\n用户已取消，程序退出。")
            return 130
        except subprocess.CalledProcessError as exc:
            print(f"\n命令执行失败（退出码 {exc.returncode}）：{exc.cmd}\n")
        except DownloadError as exc:
            print(f"\n下载失败：{exc}\n")
        except Exception as exc:  # pragma: no cover - defensive CLI guard
            print(f"\n发生未知错误：{exc}\n")


if __name__ == "__main__":
    sys.exit(main())
