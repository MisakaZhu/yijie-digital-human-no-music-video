# 本机近期来源索引与查重

`scripts/recent_sources.py` 只读指定 `RUN_ROOT` 的 `*/task-checkpoint.json`；`refresh` 另写指定 MD。没有网络调用、历史硬编码、后台接口和私人素材补录。首次空目录只说明尚无本机记录。

```bash
python SCRIPT_PATH/recent_sources.py refresh --runs-dir RUN_ROOT --output INDEX_PATH
python SCRIPT_PATH/recent_sources.py check --runs-dir RUN_ROOT --source-url SOURCE_URL --exclude-run RUN_ID
```

`SCRIPT_PATH` 换为已安装 skill 的 `scripts` 绝对路径。可见稳定 ID 可另传 `--video-id`；默认滚动窗口 168 小时。`--now` 仅供确定性测试，实际制作不要伪造检查时间。

## 核验记录字段

来源记录保存 `source_url` 与可知的 `source_video_id`。已完成记录还需：

- `generation_status = verified` 或 `completed`，且 `result_identity_evidence` 非空；
- `local_validation_status = passed` 时，本地成片已验证；或 `preview_status = verified` 且 `result_origin`、`result_preview_clicked_at` 完整时，已核到平台成片；
- `completed_at` 为有时区的真实核验时间。兼容旧记录可使用 `result_verified_at`、`completion_at` 或 `generated_at`，但不从文件修改时间虚构完成时间。

仅有现存文件、按钮点击、提交成功、进度、标题或 `phase` 文本都不足以计入已核验生成。已核验生成后本机文件缺失仍登记并标注；提交后尚无结果计入进行中检查。已结束的失败、取消、已跳过重复任务不计作进行中。

脚本会核对 JSON、来源 ID、带时区时间及最少状态。无效记录、ID 冲突、缺少必要时间或成片证据使检查返回 `evidence_incomplete`，不会忽略错误而宣称未匹配。其他任务只读这些最少字段，不采用其 checkpoint 作当前任务记录。

## 结果与退出码

| check 结果 | 退出码 | 下一步 |
| --- | ---: | --- |
| `duplicate` | 10 | 近 168 小时有核验来源或有进行中任务；自动跳过，除非已明确要求重做该条 |
| `no_match` | 0 | 在指定本机记录中未匹配；不代表平台全历史唯一 |
| `unknown_identity` | 11 | 短链没有可确认 ID，也没有精确链接匹配；取得稳定 ID 或按实际使用者明确授权处理可能重复风险 |
| `evidence_incomplete` | 12 | 记录损坏/缺失关键证据，修复或说明实际缺项，不能宣称查重通过 |
| 输入/写入错误 | 2 | 检查命令参数、目录权限等实际故障 |

ID 相同的 `/video/{id}`、`modal_id={id}` 属于同一来源；没有 ID 时精确链接相同可以证明匹配，没有精确匹配不能证明不同。记录中的 URL 对外只输出去掉查询、片段和用户信息后的地址；来源 ID 单列保留。遇到签名下载链接时不得把它当来源写入记录。

批次逐条检查；运行记录尚未写入前也维护本批来源集合，避免同批重复。只有包装成片实际核验后才设置完成字段。结束后刷新是登记本次完成记录，不再对本次重新执行排除判定。
