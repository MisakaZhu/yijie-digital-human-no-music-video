# 使用者本机配置

先确定本次可写工作目录 `WORKSPACE`。配置放在该目录的 `.yijie-config.json`，由 [config.example.json](../config.example.json) 复制；不要把真实配置写入已安装 skill 或提交仓库。

本次明确指令优先于本机配置，未设置的可选参数使用模板默认值。相对路径相对于 `WORKSPACE`；运行时解析为绝对路径并记录到本次 checkpoint。不可写目录按当前工具权限处理，不自行换成作者的目录。

| JSON 字段 | 运行时字段 | 规则 |
| --- | --- | --- |
| `workbench_url` | `WORKBENCH_URL` | 必填，使用者自己的 HTTP(S) 后台地址；不含嵌入账号/密码或凭证查询，不从分享链接推断 |
| `download_dir` | `DOWNLOAD_DIR` | 默认 `./output`，新文件不能覆盖旧文件 |
| `runs_dir` | `RUN_ROOT` | 默认 `./.yijie-runs`，每条任务建立独立 UUID 子目录 |
| `recent_sources_file` | `INDEX_PATH` | 默认 `./抖音已生成来源_近7天.md`，本机滚动索引 |
| `allowed_voice_models` | `ALLOWED_VOICE_MODELS` | 使用者有权使用且允许的声音名称列表；生成前不能为空，核对页面真实名称 |
| `avatar_names` | `AVATAR_NAMES` | 使用者允许的形象列表；生成前不能为空，批量在列表内适度轮换 |
| `persona` | `PERSONA` | 可空，空值关闭人设开关；有值则选择该实际人设，缺失时不猜近似人设 |
| `required_topic` | `REQUIRED_TOPIC` | 可空，有值为一个 `#` 开头且无空白的固定话题，计入总数 |
| `topic_count` | — | 此版本要求 5；不同数字须作为明确流程修改处理 |
| `audio_speed` / `audio_pitch` / `audio_volume` | `AUDIO_SPEED` / `AUDIO_PITCH` / `AUDIO_VOLUME` | 默认 `1.1` / `1.0` / `100`，按页面可用范围核对 |
| `packaging_volume` | `VOLUME` | 默认 `10`，不同于口播音量 |
| `background_music` | `BGM` | 默认 `无音乐`，页面回读确认；明确要求配乐时标注输出类型变化 |

第一次可一次取得后台地址、声音与形象，保存本机配置后后续复用。仅地址/模型名称是参数，不是任何付费、权限变更或外部发布授权。下载授权依据是当前使用者实际任务指令或其尚未撤回的既有授权，不能在模板预填为作者已授权。

配置中不得加入密码、验证码、Cookie、API key、访问令牌、签名下载 URL 或真实历史作品。不自动安装额外软件；本机 Python 3.10+ 用于索引，FFmpeg/ffprobe 用于完整媒体检查。缺少时报告具体缺项，已生成作品仍保留。

工具句柄、浏览器占用与登录态以当前环境为准。没有支持按任务绑定 Chrome 标签的工具时，说明该具体缺项，不把普通聊天 agent 描述成能直接操作网站。
