# B 站 UP 主视频抓取与下载工具

一键抓取某 UP 主全部投稿的**元数据**并**下载视频**，结果导出 **CSV + Excel** 双格式。

- **零运行时依赖**：纯 Python 标准库实现，无需安装任何第三方包。
- **免安装交付**：用 PyInstaller 打包成可执行文件，macOS / Windows 用户**无需安装 Python 和 ffmpeg**（ffmpeg 已内置）。
- **多线程下载**：`ThreadPoolExecutor` 并发下载，音视频流自动用 ffmpeg 合并为 mp4。
- **wbi 签名**：兼容 B 站 wbi 接口，带 Cookie / UA / Referer、请求限速与失败重试。

---

## 抓取的数据字段

BV号、标题、UP主、发布时间、时长、播放、弹幕、点赞、投币、收藏、分享、评论、视频链接、本地文件路径。

---

## 获取 Cookie（扫码登录）

不想手动从浏览器复制 Cookie？用内置的扫码登录脚本，App 扫码后自动提取 SESSDATA：

```bash
pip install qrcode            # 仅此脚本需要（终端画二维码用），主程序零依赖
python3 get_cookie.py         # 终端扫码，打印 Cookie
python3 get_cookie.py --save .env
```

扫码成功后脚本会打印 `export BILI_COOKIE="..."`，复制到终端执行即可。

---

## 使用方式

### 方式一：源码运行（需要本机有 Python 3.10+，ffmpeg 可选）

```bash
# 设置 Cookie（二选一）
export BILI_SESSDATA="你的SESSDATA值"        # 只填 SESSDATA
export BILI_COOKIE="SESSDATA=xxx; bili_jct=yyy"  # 或完整 Cookie 串

# 抓取 UP 主全部投稿并下载（1080P，4 线程）
python3 run.py 495585242

# 也可以直接给主页链接
python3 run.py https://space.bilibili.com/495585242

# 只采集元数据、不下载视频
python3 run.py 495585242 --no-download

# 调整清晰度 / 并发 / 间隔 / 输出目录
python3 run.py 495585242 --qn 80 --workers 4 --interval 1.0 --out ./output
```

### 方式二：打包后的可执行文件（无需任何环境）

- **macOS**：`./bilibili-spider` 或 `./bilibili-spider 495585242`
- **Windows**：`bilibili-spider.exe` 或 `bilibili-spider.exe 495585242`
- 不带参数运行时，会**交互式提示输入 UID**（双击即用）。

---

## 参数说明

| 参数 | 默认 | 说明 |
|------|------|------|
| `uid` | 必填（留空则交互输入） | UP 主 UID 或主页链接 |
| `--qn` | 80 | 目标清晰度：80=1080P，64=720P，32=480P，16=360P |
| `--workers` | 4 | 并发下载数 |
| `--interval` | 1.0 | 请求间隔（秒），防风控 |
| `--out` | ./output | 输出目录 |
| `--cookie` | 空 | 完整 Cookie 串（默认读环境变量） |
| `--no-download` | 关 | 只采集元数据，不下载视频 |
| `--limit` | 0（全部） | 只抓取最新 N 个视频，如 `--limit 20` |

> 双击运行时（交互模式）也会**提示输入爬取数量**（留空 = 全部）。

> 未登录时部分接口受限、画质可能降级。高画质（1080P+）建议提供登录后的 `SESSDATA`。

---

## 打包

### 本机打包

```bash
pip install pyinstaller
# 1) 把静态 ffmpeg 放到 bin/ 下（macOS: bin/ffmpeg，Windows: bin/ffmpeg.exe）
# 2) 打包
pyinstaller build.spec --clean --noconfirm
# 产物在 dist/bilibili-spider/
```

> 说明：PyInstaller 不能交叉编译。mac 版需在 macOS 上打、Windows 版需在 Windows 上打。
> 本仓库已内置 GitHub Actions（`.github/workflows/build.yml`），推到 GitHub 后
> 手动触发或打 `v*` tag 即可**自动产出 mac + Windows 双平台包**。

### 静态 ffmpeg 来源

- macOS：`https://github.com/eugeneware/ffmpeg-static/releases` 的 `ffmpeg-darwin-arm64` / `ffmpeg-darwin-x64`
- Windows：`https://github.com/BtbN/FFmpeg-Builds/releases` 的 `ffmpeg-master-latest-win64-gpl.zip`

---

## 合规说明

本工具仅供**个人学习、备份自用**。请遵守 B 站相关协议与 robots 规则，控制抓取频率，
**不要**将下载内容用于传播或商业用途。
