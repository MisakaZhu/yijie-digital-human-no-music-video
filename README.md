# 数字人无音乐视频 Agent Skill

把视频分享链接或口播文案，在兼容的营销智脑网页工作台中制作成数字人视频，完成智能包装、成片核对和本地下载。此仓库是 `yijie-digital-human-no-music-video` 的公开分发版。

**适用环境：** 支持本地 skills、Chrome 网页控制和本机文件工具的 Codex。其他 agent 需要自行具备等效能力。本 skill 是操作说明和本机辅助脚本，视频制作由使用者自己的平台账号完成。

## Agent 一键安装提示词

复制下面整段给你的 agent，即可让它检查仓库并安装：

```text
请帮我安装这个数字人无音乐视频 skill：
https://github.com/MisakaZhu/yijie-digital-human-no-music-video

1. 只使用上述原仓库，不替换为 fork 或其他镜像。先只读检查仓库身份、默认分支、README、SKILL.md、references、scripts 和依赖，确认没有凭证、异常二进制、隐藏联网、安装时执行或与工作流无关的操作。发现实际问题时说明并停止。
2. 需要安装的目录是 skills/yijie-digital-human-no-music-video。优先使用你环境自带的 skill-installer，从该目录安装；若没有安装器，就按该 agent 官方支持的本地 skills 机制复制完整目录。Codex 使用 CODEX_HOME/skills；未设置 CODEX_HOME 时使用 ~/.codex/skills。
3. 如果已经有同名 skill，先读取并比较版本，保留现有文件、私人配置和运行记录，不直接覆盖。内容一致则报告已安装；内容不同则给出具体差异和保留原版的升级方案，由我决定。
4. 安装时只复制 skill 文件，不执行视频工作流、不登录平台、不提交生成、不发布，也不自动安装额外软件。安装后核对 YAML 名称、全部相对引用、配置模板和辅助脚本，读取目标目录中的 SKILL.md，报告真实安装路径与仓库提交 SHA。
5. 告诉我该 skill 何时可被当前 agent 发现，并给一条 $yijie-digital-human-no-music-video 的调用示例。后台地址、声音、形象和保存目录由我首次使用时配置；不要索取密码、验证码或 Cookie。需要浏览器控制、Python 或 FFmpeg 时列出实际缺项即可。
```

安装提示词只负责安装。生成视频时仍需你提供自己的工作台配置和任务输入。

## 能做什么

- 链接提取文案、网页改写、生成音频和数字人视频。
- 每条视频使用独立运行目录与标签页，断点恢复沿用本次记录。
- 优先从作品库选择本次原片，选择模板并设置无背景音乐。
- 生成前检查最近 168 小时已核验来源和正在进行的任务；批次自动跳过重复项。
- 实际激活本次历史预览或作品库详情，再核对包装成片、下载并检查 MP4。
- 正常下载失败时，在使用者已有下载授权内使用真实可见结果地址保存；不因下载故障自动重做。

适配的典型页面路线为 `生产部门 → 爆款大师 → 一键追爆`，再进入 `剪辑高手 → 智能包装`。平台改版或不同账号的模块、声音、形象可能不同，以实际页面为准。

## 首次使用

1. 安装 skill。把 [config.example.json](skills/yijie-digital-human-no-music-video/config.example.json) 复制到你的工作目录，命名为 `.yijie-config.json`。
2. 填写自己的 `workbench_url`、允许的 `allowed_voice_models` 和 `avatar_names`。可修改保存目录、人设和固定话题；相对路径相对于当前工作目录，配置和任务记录留在本机。
3. 在 Chrome 登录你自己的兼容工作台；向 agent 提供链接或文案：

```text
使用 $yijie-digital-human-no-music-video。
工作目录使用当前目录，读取其中的 .yijie-config.json。
根据这个视频分享链接制作一条无音乐数字人视频：粘贴你的链接。
可以按标准流程提取和改写文案、生成音频与数字人、选择模板、包装及下载本次最终成片；本机备用下载也包含在本次下载授权中。
```

直接文案也支持：

```text
使用 $yijie-digital-human-no-music-video，读取当前工作目录的 .yijie-config.json。
用下面这份文案制作无音乐视频，保持文意；需要修改时先给我看修改稿。
文案：粘贴你的口播正文。
```

后台账号、视频生成额度及平台许可需要使用者自行准备。声音与形象只使用你有权使用的资源。安装 skill 不会创建账号或获得视频制作额度。

## 配置与工具

完整配置规则见 [configuration.md](skills/yijie-digital-human-no-music-video/references/configuration.md)。默认不含后台地址、个人声音名称、个人形象或下载预授权。固定话题可设置，也可留空；最终始终为 5 个不重复话题。人设未配置时关闭人设开关。

辅助脚本使用 Python 3.10+ 标准库，无需 pip 安装依赖：

```bash
python skills/yijie-digital-human-no-music-video/scripts/recent_sources.py refresh --runs-dir .yijie-runs --output 抖音已生成来源_近7天.md
python skills/yijie-digital-human-no-music-video/scripts/recent_sources.py check --runs-dir .yijie-runs --source-url "https://www.douyin.com/video/1000000000000000001" --exclude-run YOUR_RUN_ID
python skills/yijie-digital-human-no-music-video/scripts/verify_media.py /path/to/your-video.mp4
```

上述来源 ID 是测试示例，不是候选素材。Windows 没有 `python` 命令时，可由 agent 使用已经安装的 Python 绝对路径。媒体验证还需要已安装的 `ffprobe` 和 `ffmpeg`；可使用 `--ffprobe`、`--ffmpeg` 指定路径。脚本不会自动安装它们，也不会调用平台接口。

来源索引只覆盖本机所指定运行目录的可核验记录；空索引和“未匹配”都不是平台全历史唯一性证明。文件检查和解码不证明无背景音乐，听音与内容抽查范围要按实际情况说明。

## 仓库结构

```text
README.md
LICENSE
.gitignore
skills/yijie-digital-human-no-music-video/
  SKILL.md
  agents/openai.yaml
  config.example.json
  references/                 配置、操作流程与核验规则
  scripts/                    本机查重与媒体验证
tests/                        离线行为测试
tools/audit_package.py         打包前文件与引用检查
```

只安装 `skills/yijie-digital-human-no-music-video`，仓库根目录的测试与发布检查工具不必安装。

## 维护与验证

```bash
python tools/audit_package.py
python -m unittest discover -s tests -v
```

这些检查验证分发内容和本机辅助脚本；不代替使用者账号上的网页端到端实测。不要上传 `.yijie-config.json`、运行记录、视频、截图、私人文案、签名下载地址或凭证。`.gitignore` 已忽略常见本机产物，发布前仍应运行检查。

本仓库采用 [MIT License](LICENSE)。许可适用于本仓库说明与代码；平台、声音、形象和源视频的使用权由相应权利人和使用者约定。
