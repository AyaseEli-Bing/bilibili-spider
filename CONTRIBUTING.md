# 参与贡献

先说结论：**提 PR 之前请先开一个 issue（或在已有 issue 下留言认领）**，说明你打算怎么改。
这样能避免两个人同时做同一条，也能让维护者在你花几小时之前指出方向不对。

## 环境准备

```bash
python3 -V                         # 需要 3.11+（CI 与本地都用 3.12 验证过）
pip install -r requirements-dev.txt
pip install pytest ruff            # 目前 requirements-dev.txt 里还没有这两项
```

## 本地验证（提交前必跑）

```bash
pytest -q                          # 全部用例必须离线通过
python3 tests/test_smoke.py        # 无 pytest 时的兜底跑法
ruff check <你改动的文件>           # 见下方「不要顺手全仓格式化」
```

- **测试必须离线**：不要在任何测试里请求 B 站的真实接口。需要响应数据时用 stub / fixture。
- **不要顺手全仓格式化**：`ruff check .` 在当前 `HEAD` 上有 12 处告警（其中 7 处可自动修）。
  请只 lint 你改过的文件，把全仓清理单独开一个 PR。
- 改了输出格式或参数行为时，同步更新 `README.md` 的参数表——文档与代码不一致是最常见的被打回原因。

## 提交与分支

- 分支名用 `feat/xxx`、`fix/xxx`、`docs/xxx`。
- Commit message 用 Conventional Commits 前缀，主题可以是中文：

  ```text
  feat: 新增 --limit 参数控制抓取条数
  fix: 修复 up 主信息接口返回 data=null 时崩溃
  ```

  常用类型：`feat`、`fix`、`docs`、`refactor`、`chore`、`test`、`ci`。
  `scripts/gen_changelog.py` 按 `feat`/`fix`/其他 三种桶生成更新日志，前缀写错会让条目落到「其他」里。
- 版本号在 `src/config.py` 的 `VERSION`，与 git tag 是**两处独立维护**的。改版本时两边都要动，
  发版由打 `v*` tag 触发（`.github/workflows/build.yml` 会产出 mac + Windows 双平台包并建 Release）。

## PR 要求

- 一个 PR 只做一件事；重构和功能改动分开。
- 描述里写清：改了什么、为什么、**怎么验证的**（贴 `pytest -q` 的输出即可）。
- 修 bug 时先加一个能复现该 bug 的测试，确认它在没修复时会失败。
- 当前 PR 上没有自动测试（CI 只在打 tag 时构建），所以「怎么验证的」这一栏是维护者唯一的依据，请写实。

## 许可

提交即表示同意本项目以 MIT 许可发布你的改动（见 `LICENSE`）。
