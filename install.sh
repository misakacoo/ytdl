#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_URL="https://github.com/misakacoo/ytdl"
REPO_REF="${YTDL_GITHUB_REF:-main}"
ARCHIVE_URL="${REPO_URL}/archive/refs/heads/${REPO_REF}.tar.gz"
RAW_INSTALL_URL="https://raw.githubusercontent.com/misakacoo/ytdl/${REPO_REF}/install.sh"
INSTALL_DIR="${YTDL_HOME:-/opt/ytdl}"
VENV_DIR="$SCRIPT_DIR/.venv"
YTDL_COMMAND="/usr/local/bin/ytdl"
PYTHON_MIN_VERSION="3.10.0"
PYTHON_LATEST_VERSION="3.14.5"
PYTHON_LATEST_MM="3.14"
PYTHON_BIN=""
INSTALL_ONLY=0
TARGET_USER="${SUDO_USER:-$(id -un)}"
TARGET_GROUP="$(id -gn "$TARGET_USER")"

if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
else
  SUDO=""
fi

ask_yes_no() {
  local prompt default suffix answer
  prompt="$1"
  default="${2:-Y}"

  if [[ "$default" == "Y" ]]; then
    suffix="[Y/n]"
  else
    suffix="[y/N]"
  fi

  while true; do
    read -r -p "$prompt $suffix " answer
    answer="${answer:-$default}"
    case "${answer,,}" in
      y|yes) return 0 ;;
      n|no) return 1 ;;
      *) echo "请输入 y 或 n。" ;;
    esac
  done
}

version_lt() {
  [[ "$(printf '%s\n' "$1" "$2" | sort -V | head -n 1)" != "$2" ]]
}

has_project_files() {
  local base_dir
  base_dir="$1"
  [[ -f "$base_dir/downloader.py" ]] &&
    [[ -f "$base_dir/run.sh" ]] &&
    [[ -f "$base_dir/requirements.txt" ]] &&
    [[ -f "$base_dir/install.sh" ]]
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --install-only)
        INSTALL_ONLY=1
        shift
        ;;
      *)
        echo "不支持的参数：$1"
        exit 1
        ;;
    esac
  done
}

ensure_project_files() {
  if has_project_files "$SCRIPT_DIR"; then
    return
  fi

  echo "当前执行的是独立安装脚本，未检测到完整项目文件。"
  bootstrap_project "$@"
  exit 0
}

ensure_supported_os() {
  if [[ ! -f /etc/os-release ]]; then
    echo "未检测到 /etc/os-release，当前系统不在支持范围内。"
    exit 1
  fi

  # shellcheck disable=SC1091
  source /etc/os-release
  local os_family="${ID_LIKE:-}"
  if [[ "${ID:-}" != "debian" && "${ID:-}" != "ubuntu" && "$os_family" != *debian* ]]; then
    echo "当前仅支持 Debian / Ubuntu 系系统。"
    exit 1
  fi
}

download_file() {
  local url output_path
  url="$1"
  output_path="$2"

  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url" -o "$output_path"
    return
  fi

  if command -v wget >/dev/null 2>&1; then
    wget -qO "$output_path" "$url"
    return
  fi

  echo "未检测到 curl 或 wget，无法下载项目文件。"
  exit 1
}

validate_install_dir() {
  $SUDO mkdir -p "$(dirname "$INSTALL_DIR")"
  if [[ -e "$INSTALL_DIR" && ! -d "$INSTALL_DIR" ]]; then
    echo "目标路径已存在且不是目录：$INSTALL_DIR"
    exit 1
  fi
  if [[ -d "$INSTALL_DIR" ]] && ! has_project_files "$INSTALL_DIR"; then
    if find "$INSTALL_DIR" -mindepth 1 -print -quit | grep -q .; then
      echo "目标目录已存在且不是 ytdl 项目目录：$INSTALL_DIR"
      echo "请清理该目录，或使用环境变量 YTDL_HOME 指定其他安装位置。"
      exit 1
    fi
  fi
}

sync_project_to_install_dir() {
  local source_dir item item_name
  source_dir="$1"

  validate_install_dir
  echo "==> 正在同步项目到：$INSTALL_DIR"
  $SUDO mkdir -p "$INSTALL_DIR"

  shopt -s dotglob nullglob
  for item in "$source_dir"/* "$source_dir"/.[!.]* "$source_dir"/..?*; do
    item_name="$(basename "$item")"
    case "$item_name" in
      .|..|.git|.venv|downloads|__pycache__)
        continue
        ;;
    esac
    $SUDO cp -a "$item" "$INSTALL_DIR"/
  done
  shopt -u dotglob nullglob

  $SUDO chmod +x "$INSTALL_DIR/install.sh" "$INSTALL_DIR/run.sh" "$INSTALL_DIR/downloader.py"
  $SUDO chown -R "$TARGET_USER:$TARGET_GROUP" "$INSTALL_DIR"
}

bootstrap_project() {
  local tmp_dir archive_path extracted_dir

  if has_project_files "$INSTALL_DIR"; then
    echo "==> 检测到本地已存在项目目录：$INSTALL_DIR"
    echo "==> 正在切换到本地项目继续执行"
    exec "$INSTALL_DIR/install.sh" "$@"
  fi

  echo "==> GitHub 仓库：$REPO_URL"
  echo "==> 一键安装脚本：$RAW_INSTALL_URL"
  echo "==> 将把项目下载到：$INSTALL_DIR"
  if ! ask_yes_no "是否继续下载项目并开始安装？" "Y"; then
    echo "已取消安装。"
    exit 0
  fi

  tmp_dir="$(mktemp -d)"
  archive_path="$tmp_dir/ytdl.tar.gz"

  echo "==> 下载项目归档"
  download_file "$ARCHIVE_URL" "$archive_path"

  echo "==> 解压项目文件"
  tar -xzf "$archive_path" -C "$tmp_dir"
  extracted_dir="$(find "$tmp_dir" -mindepth 1 -maxdepth 1 -type d -name 'ytdl-*' | head -n 1)"
  if [[ -z "$extracted_dir" ]]; then
    echo "项目归档解压失败，请检查仓库是否已上传且默认分支为 ${REPO_REF}。"
    rm -rf "$tmp_dir"
    exit 1
  fi

  sync_project_to_install_dir "$extracted_dir"
  rm -rf "$tmp_dir"

  echo "==> 项目已下载完成：$INSTALL_DIR"
  echo "==> 后续也可以直接执行：bash $INSTALL_DIR/install.sh"
  exec "$INSTALL_DIR/install.sh" "$@"
}

ensure_install_location() {
  if [[ "$SCRIPT_DIR" == "$INSTALL_DIR" ]]; then
    return
  fi

  echo "==> 当前项目目录：$SCRIPT_DIR"
  echo "==> 标准安装目录：$INSTALL_DIR"
  sync_project_to_install_dir "$SCRIPT_DIR"
  echo "==> 已切换到标准安装目录继续执行"
  exec "$INSTALL_DIR/install.sh" "$@"
}

is_installed() {
  [[ -x "$VENV_DIR/bin/python" ]] || return 1
  "$VENV_DIR/bin/python" -c "import yt_dlp" >/dev/null 2>&1
}

install_python_build_deps() {
  $SUDO apt-get install -y \
    build-essential wget curl ca-certificates tar xz-utils \
    libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
    libncursesw5-dev tk-dev libxml2-dev libxmlsec1-dev libffi-dev \
    liblzma-dev uuid-dev libgdbm-dev libnss3-dev libdb5.3-dev
}

install_latest_python() {
  local tmp_dir archive_path source_dir

  install_python_build_deps

  tmp_dir="$(mktemp -d)"
  archive_path="$tmp_dir/Python-${PYTHON_LATEST_VERSION}.tgz"
  source_dir="$tmp_dir/Python-${PYTHON_LATEST_VERSION}"

  echo "==> 下载 Python ${PYTHON_LATEST_VERSION}"
  wget -O "$archive_path" \
    "https://www.python.org/ftp/python/${PYTHON_LATEST_VERSION}/Python-${PYTHON_LATEST_VERSION}.tgz"

  echo "==> 编译安装 Python ${PYTHON_LATEST_VERSION}"
  tar -xzf "$archive_path" -C "$tmp_dir"
  cd "$source_dir"
  ./configure --enable-optimizations
  make -j"$(nproc)"
  $SUDO make altinstall
  cd "$SCRIPT_DIR"

  rm -rf "$tmp_dir"
}

select_python() {
  local current_python current_version answer

  if command -v "python${PYTHON_LATEST_MM}" >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v "python${PYTHON_LATEST_MM}")"
    echo "==> 检测到已安装 $("$PYTHON_BIN" --version 2>&1)"
    return
  fi

  if command -v python3 >/dev/null 2>&1; then
    current_python="$(command -v python3)"
    current_version="$("$current_python" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
    if version_lt "$current_version" "$PYTHON_MIN_VERSION"; then
      echo "==> 当前 Python 版本过低：$current_version"
      echo "==> yt-dlp 最新版本需要 Python 3.10+"
      if ask_yes_no "是否自动安装最新稳定版 Python ${PYTHON_LATEST_VERSION}？" "Y"; then
        install_latest_python
        PYTHON_BIN="/usr/local/bin/python${PYTHON_LATEST_MM}"
      else
        echo "==> 已取消自动升级。"
        echo "==> 当前 Python 版本不满足安装要求，请先安装 Python 3.10+ 后重新执行安装。"
        exit 1
      fi
    else
      PYTHON_BIN="$current_python"
    fi
  else
    echo "==> 未检测到 python3，将安装最新稳定版 Python ${PYTHON_LATEST_VERSION}"
    install_latest_python
    PYTHON_BIN="/usr/local/bin/python${PYTHON_LATEST_MM}"
  fi
}

install_latest_ffmpeg() {
  local arch asset_url tmp_dir archive_path extracted_dir ffmpeg_path ffprobe_path

  arch="$(uname -m)"
  case "$arch" in
    x86_64|amd64)
      asset_url="https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
      ;;
    aarch64|arm64)
      asset_url="https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz"
      ;;
    *)
      echo "==> 当前架构 $arch 暂未配置静态包，回退到 apt 安装 ffmpeg"
      $SUDO apt-get install -y ffmpeg
      return
      ;;
  esac

  tmp_dir="$(mktemp -d)"
  archive_path="$tmp_dir/ffmpeg.tar.xz"
  extracted_dir="$tmp_dir/extracted"
  mkdir -p "$extracted_dir"

  echo "==> 下载最新 FFmpeg 静态包"
  wget -O "$archive_path" "$asset_url"

  echo "==> 安装 FFmpeg 到 /usr/local/bin"
  tar -xf "$archive_path" -C "$extracted_dir"
  ffmpeg_path="$(find "$extracted_dir" -type f -name ffmpeg | head -n 1)"
  ffprobe_path="$(find "$extracted_dir" -type f -name ffprobe | head -n 1)"

  if [[ -z "$ffmpeg_path" || -z "$ffprobe_path" ]]; then
    echo "未找到 ffmpeg/ffprobe 可执行文件，安装失败。"
    rm -rf "$tmp_dir"
    exit 1
  fi

  $SUDO install -m 0755 "$ffmpeg_path" /usr/local/bin/ffmpeg
  $SUDO install -m 0755 "$ffprobe_path" /usr/local/bin/ffprobe

  rm -rf "$tmp_dir"
}

print_versions() {
  local ffmpeg_bin
  echo "==> 当前版本"
  /bin/echo -n "Python: "
  "$VENV_DIR/bin/python" --version
  ffmpeg_bin="$(command -v ffmpeg)"
  "$ffmpeg_bin" -version | head -n 1
  "$VENV_DIR/bin/python" -m yt_dlp --version
}

perform_install() {
  echo "==> 安装系统依赖"
  $SUDO apt-get update
  $SUDO apt-get install -y python3 python3-venv wget tar xz-utils ca-certificates

  $SUDO mkdir -p "$SCRIPT_DIR"
  $SUDO chown -R "$TARGET_USER:$TARGET_GROUP" "$SCRIPT_DIR"

  install_latest_ffmpeg
  select_python

  if [[ -x "$VENV_DIR/bin/python" ]]; then
    echo "==> 更新 Python 虚拟环境"
    "$PYTHON_BIN" -m venv --upgrade "$VENV_DIR"
  else
    echo "==> 创建 Python 虚拟环境"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi

  echo "==> 安装 Python 依赖"
  "$VENV_DIR/bin/python" -m pip install --upgrade pip
  "$VENV_DIR/bin/python" -m pip install --upgrade -r "$SCRIPT_DIR/requirements.txt"

  mkdir -p "$SCRIPT_DIR/downloads"
  touch "$SCRIPT_DIR/url.txt"
  $SUDO chown -R "$TARGET_USER:$TARGET_GROUP" "$SCRIPT_DIR/downloads"
  $SUDO chown "$TARGET_USER:$TARGET_GROUP" "$SCRIPT_DIR/url.txt"
  chmod +x "$SCRIPT_DIR/install.sh" "$SCRIPT_DIR/run.sh" "$SCRIPT_DIR/downloader.py"
  $SUDO ln -sf "$SCRIPT_DIR/run.sh" "$YTDL_COMMAND"

  print_versions
}

launch_app() {
  exec "$SCRIPT_DIR/run.sh"
}

main() {
  parse_args "$@"
  ensure_supported_os
  ensure_project_files "$@"
  ensure_install_location "$@"

  if [[ "$INSTALL_ONLY" -eq 1 ]]; then
    perform_install
    exit 0
  fi

  if is_installed; then
    echo "==> 检测到已安装，正在启动主菜单"
    launch_app
  fi

  echo "==> 检测到当前为首次运行"
  if ask_yes_no "是否现在开始完整安装？" "Y"; then
    perform_install
    echo
    echo "安装完成，正在进入主菜单。"
    launch_app
  fi

  echo "已取消安装。"
}

main "$@"
