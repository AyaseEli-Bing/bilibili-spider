# B 站 UP 主数据量检测工具

一键检测某 UP 主的投稿数据量：抓取前概览（粉丝数 / 投稿总数）+ 逐条元数据 + 汇总统计 + 维度分布分析，结果导出 **CSV + Excel** 双格式。

- **零运行时依赖**：纯 Python 标准库实现，无需安装任何第三方包。
- **免安装交付**：用 PyInstaller 打包成可执行文件，macOS / Windows 用户**无需安装 Python**。
- **数据量检测**：抓取前概览 + 汇总统计（总播放/总点赞/总时长/平均播放）+ 时长/发布时间分布。
- **wbi 签名**：兼容 B 站 wbi 接口，带 Cookie / UA / Referer、请求限速与失败重试。

---

## 检测的数据字段

BV号、标题、UP主、发布时间、时长、播放、弹幕、点赞、投币、收藏、分享、评论、视频链接。

## 检测报告内容

1. **抓取前概览**：UP 主粉丝数、投稿总数
2. **汇总统计**：视频总数、总播放量、平均播放、总点赞、总投币、总收藏、总弹幕、总评论、总分享、总时长、平均时长
3. **维度分布**：时长分布（1分钟内 / 1-5分钟 / 5-10分钟 / 10-30分钟 / 30分钟以上）、发布时间分布（按年份）

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

### 方式一：源码运行（需要本机有 Python 3.10+）

```bash
# 设置 Cookie（二选一）
export BILI_SESSDATA="你的SESSDATA值"        # 只填 SESSDATA
export BILI_COOKIE="SESSDATA=xxx; bili_jct=yyy"  # 或完整 Cookie 串

# 检测 UP 主全部投稿数据量
python3 run.py 495585242

# 也可以直接给主页链接
python3 run.py https://space.bilibili.com/495585242

# 只检测最新 20 个视频
python3 run.py 495585242 --limit 20

# 自定义间隔 / 输出目录
python3 run.py 495585242 --interval 1.0 --out ./output
```

### 方式二：打包后的可执行文件（无需任何环境）

- **macOS**：`./bilibili-spider` 或 `./bilibili-spider 495585242`
- **Windows**：`bilibili-spider.exe` 或 `bilibili-spider.exe 495585242`
- 不带参数运行时，会**交互式提示输入 UID 和检测数量**（双击即用）。

---

## 参数说明

| 参数 | 默认 | 说明 |
|------|------|------|
| `uid` | 必填（留空则交互输入） | UP 主 UID 或主页链接 |
| `--interval` | 1.0 | 请求间隔（秒），防风控 |
| `--out` | ./output | 输出目录 |
| `--cookie` | 空 | 完整 Cookie 串（默认读环境变量） |
| `--limit` | 0（全部） | 只检测最新 N 个视频，如 `--limit 20` |
| `--about` | - | 显示项目介绍 |
| `--version` | - | 显示版本号 |

> 双击运行时（交互模式）也会**提示输入检测数量**（留空 = 全部）。

> 未登录时部分接口受限。建议扫码登录或提供 `SESSDATA` 获取完整数据。

---

## 打包

### 本机打包

```bash
pip install pyinstaller
pyinstaller build.spec --clean --noconfirm
# 产物在 dist/bilibili-spider
```

> 说明：PyInstaller 不能交叉编译。mac 版需在 macOS 上打、Windows 版需在 Windows 上打。
> 本仓库已内置 GitHub Actions（`.github/workflows/build.yml`），推到 GitHub 后
> 手动触发或打 `v*` tag 即可**自动产出 mac + Windows 双平台包**，Release 说明自动带上该版本更新内容。

---

## 合规说明

本工具仅供**个人学习、数据统计自用**。请遵守 B 站相关协议与 robots 规则，控制抓取频率。
