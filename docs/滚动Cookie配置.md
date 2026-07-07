# 滚动 Cookie（自动续期）配置说明

## 为什么需要它

抖音近期收紧了会话安全（`bd_ticket_guard` 等）：**一份导出的 cookie 成功登录一次后就会失效**。
所以"在 GitHub 密钥里存一份固定 cookie"的老办法现在跑不长——今天能成一次，明天定时任务再用那份就变登录页了。

**滚动 cookie** 解决这个问题：每次运行成功登录后，抓取抖音**轮换出的最新 cookie**，
在运行结束时自动**回写到 GitHub 密钥**，下次运行就用这份新的接力，如此循环，长期不掉线。

- 抓取：`core/tasks.py` 的 `save_fresh_cookies()`，仅在**登录成功**后把最新 cookie 落盘到 `cookie_refresh/COOKIES_<ID>.json`（失败绝不写，避免把登录页的坏 cookie 回写）。
- 回写：workflow 的 `Roll refreshed cookies back to secrets` 步骤，用 `gh secret set` 把它写回对应密钥。

## 需要你做的：配置一个 PAT

回写密钥需要一个有 **secrets 写权限** 的令牌（默认的 `GITHUB_TOKEN` 没有这个权限）。

### 1. 创建 Fine-grained PAT（推荐，权限最小）

打开 GitHub → `Settings` → `Developer settings` → `Personal access tokens` → `Fine-grained tokens` → `Generate new token`：

- **Repository access**：只选本仓库 `DouYinSparkFlow-Auto`
- **Permissions** → `Repository permissions`：
  - `Secrets` → **Read and write**
  - `Environments` → **Read and write**
  - `Metadata` → Read（必选，默认就有）
- 过期时间按需（建议尽量长，避免又要手动换）

> 也可以用 Classic token 勾 `repo` 权限，但那个权限过大，不推荐。

### 2. 把令牌存成密钥 `GH_PAT`

进入仓库 `Settings` → `Environments` → `user-data` → `Environment secrets` → `Add secret`：

- Name：`GH_PAT`
- Value：粘贴上一步生成的令牌

配好后，workflow 会自动启用滚动 cookie；**没配 `GH_PAT` 时该步骤会自动跳过**，不影响其它功能。

## 使用流程

1. 配好 `GH_PAT`（一次性）。
2. 手动刷新一次 `COOKIES_XINXI0821`（用 60 天长会话那种 cookie）——这是"火种"，之后就交给滚动机制自动续了。
3. 之后每天定时任务会自己把 cookie 续上。

## 风险与验证

唯一不确定点：如果抖音把会话**绑定到具体客户端指纹**，那么在 A 机器轮换出的 cookie 换到 B 机器（每次 runner 都是新的虚拟机）可能仍被拒。
这个只能实测——刷新火种后连续触发两次运行：

- 第 1 次用火种登录、成功、回写；
- 第 2 次若用**回写后的 cookie** 仍然成功 → 滚动机制成立，长期可用；
- 若第 2 次失败 → 说明有客户端绑定，需要再想别的办法。
