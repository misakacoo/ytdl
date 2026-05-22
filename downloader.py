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
DEFAULT_BATCH_URL_FILE = PROJECT_DIR / "url.txt"


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
        print("2. 单个下载")
        print("3. 批量下载")
        print("4. 退出")
        choice = input("请输入选项 [1/2/3/4]：").strip()
        if choice == "1":
            return "maintenance"
        if choice == "2":
            return "single"
        if choice == "3":
            return "batch"
        if choice == "4":
            return "exit"
        print("无效选项，请输入 1、2、3 或 4。")


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


def ask_batch_profile() -> str:
    while True:
        print("\n请选择批量下载类型：")
        print("1. 批量下载视频（自动最佳，合并为 MP4）")
        print("2. 批量下载音频（提取并转换为 MP3）")
        print("3. 返回上一级")
        choice = input("请输入选项 [1/2/3]：").strip()
        if choice == "1":
            return "best"
        if choice == "2":
            return "audio"
        if choice == "3":
            return "back"
        print("无效选项，请输入 1、2 或 3。")


def ask_output_dir() -> Path:
    raw_value = input(
        f"下载目录（直接回车使用默认目录：{DEFAULT_DOWNLOAD_DIR}）："
    ).strip()
    target_dir = Path(raw_value).expanduser() if raw_value else DEFAULT_DOWNLOAD_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def print_cli_usage() -> None:
    print("用法：")
    print("  ytdl                  启动交互式主菜单")
    print("  ytdl <YouTube链接>    直接进入下载选项")
    print("  ytdl batch            直接进入批量下载")
    print("")
    print(f"批量下载链接文件：{DEFAULT_BATCH_URL_FILE}")


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


def is_probable_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def read_batch_urls(url_file: Path) -> list[str]:
    url_file.parent.mkdir(parents=True, exist_ok=True)

    if not url_file.exists():
        url_file.touch()
        raise FileNotFoundError(
            f"未检测到批量链接文件，已自动创建：{url_file}\n"
            "请将多个 YouTube 链接写入该文件，每行一个链接后再重试。"
        )

    urls: list[str] = []
    for line in url_file.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        urls.append(value)

    if not urls:
        raise ValueError(
            f"批量链接文件为空：{url_file}\n"
            "请将多个 YouTube 链接写入该文件，每行一个链接后再重试。"
        )

    return urls


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


def download_many(urls: list[str], profile: str, output_dir: Path) -> tuple[int, list[tuple[str, str]]]:
    ensure_dependencies(profile)

    success_count = 0
    failures: list[tuple[str, str]] = []
    total = len(urls)

    for index, url in enumerate(urls, start=1):
        print(f"\n[{index}/{total}] 正在下载：{url}\n")
        try:
            options = build_options(profile, output_dir)
            with YoutubeDL(options) as ydl:
                ydl.download([url])
            success_count += 1
        except DownloadError as exc:
            failures.append((url, str(exc)))
            print(f"\n[{index}/{total}] 下载失败，已跳过：{exc}\n")

    return success_count, failures


def handle_maintenance() -> None:
    while True:
        action = ask_maintenance_action()
        if action == "back":
            return
        if action == "update":
            update_yt_dlp()
            continue
        run_full_install()


def handle_single_download(preset_url: str | None = None) -> None:
    while True:
        profile = ask_download_profile()
        if profile == "back":
            return

        url = preset_url or ask_non_empty("请输入 YouTube 视频/音频链接：")
        output_dir = ask_output_dir()

        print("\n开始下载，请稍候...\n")
        download(url, profile, output_dir)
        print(f"\n下载完成，文件已保存到：{output_dir}\n")

        if preset_url is not None:
            return

        again = ask_yes_no("是否继续下载下一个链接？", default=False)
        if not again:
            return


def handle_batch_download() -> None:
    while True:
        profile = ask_batch_profile()
        if profile == "back":
            return

        urls = read_batch_urls(DEFAULT_BATCH_URL_FILE)
        output_dir = ask_output_dir()

        print(f"\n已读取 {len(urls)} 个链接，开始批量下载，请稍候...\n")
        success_count, failures = download_many(urls, profile, output_dir)

        print(f"\n批量下载完成，成功 {success_count} 个，失败 {len(failures)} 个。")
        print(f"文件保存目录：{output_dir}")

        if failures:
            print("\n失败链接列表：")
            for failed_url, reason in failures:
                print(f"- {failed_url}")
                print(f"  原因：{reason}")
            print("")

        again = ask_yes_no("是否继续执行批量下载？", default=False)
        if not again:
            return


def run_cli_mode(argv: list[str]) -> int | None:
    if not argv:
        return None

    if argv[0] in {"-h", "--help", "help"}:
        print_cli_usage()
        return 0

    if len(argv) != 1:
        print(f"参数数量不正确：{' '.join(argv)}\n")
        print_cli_usage()
        return 1

    if argv[0] == "batch":
        print("检测到批量下载命令，将直接进入批量下载。")
        handle_batch_download()
        return 0

    url = argv[0]
    if not is_probable_url(url):
        print(f"不支持的参数：{' '.join(argv)}\n")
        print_cli_usage()
        return 1

    print("检测到命令行传入链接，将直接进入下载选项。")
    handle_single_download(preset_url=url)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]

    print("YouTube 下载工具（基于 yt-dlp）")
    print("按 Ctrl+C 可以随时退出。\n")

    try:
        cli_result = run_cli_mode(argv)
        if cli_result is not None:
            return cli_result
    except KeyboardInterrupt:
        print("\n用户已取消，程序退出。")
        return 130
    except subprocess.CalledProcessError as exc:
        print(f"\n命令执行失败（退出码 {exc.returncode}）：{exc.cmd}\n")
        return exc.returncode
    except DownloadError as exc:
        print(f"\n下载失败：{exc}\n")
        return 1
    except (FileNotFoundError, ValueError) as exc:
        print(f"\n{exc}\n")
        return 1
    except Exception as exc:  # pragma: no cover - defensive CLI guard
        print(f"\n发生未知错误：{exc}\n")
        return 1

    while True:
        try:
            action = ask_main_action()
            if action == "maintenance":
                handle_maintenance()
                continue
            if action == "single":
                handle_single_download()
                continue
            if action == "batch":
                handle_batch_download()
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
        except (FileNotFoundError, ValueError) as exc:
            print(f"\n{exc}\n")
        except Exception as exc:  # pragma: no cover - defensive CLI guard
            print(f"\n发生未知错误：{exc}\n")


if __name__ == "__main__":
    sys.exit(main())
