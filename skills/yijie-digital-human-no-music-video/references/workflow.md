# 工作台完整流程

### 0. Route The Source Link Directly To The Workbench

1. Identify the source URL from the user's message locally. For a pasted Douyin share message, use its actual HTTP(S) video/share URL and omit surrounding hashtags, share codes, `mailto:` links, and promotional text. Preserve the URL path, capitalization, and parameters. Repeated copies of the same URL are one input; ask only if distinct source links are ambiguous.
2. Treat boilerplate such as `复制此链接，打开Dou音搜索，直接观看视频` as part of the shared text, not a request to open or watch Douyin. An actual user request to inspect the original video is separate and should be followed.
3. Proceed directly to the 香天下 workbench in step 1, then paste `SOURCE_URL` into `爆款大师 -> 一键追爆 -> 某音链接/抖音链接` and use `提取文案`. Do not first open/play the source video, search Douyin, visit the short link to resolve redirects, download the original clip, or require a Douyin login. Reading the original webpage is not a prerequisite for using its URL as a workbench input.
4. Visit the source platform only if the user explicitly requests original-video inspection, or a concrete extraction failure makes that inspection necessary for diagnosis. In the latter case first read the workbench error and verify the submitted URL, then explain the specific reason for the source-page check. Successful extraction continues from the returned text; any needed factual checks on that text are separate from source-page preflight.
5. If the user supplies only `COPY`, open the workbench and proceed to script preparation without asking for a source link or opening a source platform.

### 0A. 生成前检查近期来源与进行中任务

每条 `SOURCE_URL` 都执行；只有直接文案时记录 `not_applicable`。

1. 先读 [recent-sources.md](recent-sources.md)，运行本 skill 自带的 `scripts/recent_sources.py refresh --runs-dir RUN_ROOT --output INDEX_PATH`。参数使用配置解析后的绝对路径。首次使用且运行目录为空时生成空索引，不声称它覆盖平台历史。
2. 提取 `/video/{19位ID}`、`modal_id={19位ID}` 或页面可见的稳定 ID。只从用户输入或本次页面可见结果取得 ID，不为查重例行访问短链或抖音。
3. 用 `scripts/recent_sources.py check --runs-dir RUN_ROOT --source-url SOURCE_URL --exclude-run RUN_ID` 检查滚动 168 小时内已核验来源及其他进行中任务。已知 ID 另传 `--video-id`。核对脚本 JSON 与退出码。
4. `duplicate`：新付费生成前跳过；批量自动继续下一条，最终交付列表省略重复项并连续编号。用户明确要求重做这条来源时记录该授权再继续。文件后来缺失不抹去已核验生成证据。
5. `unknown_identity`、`evidence_incomplete` 或检查失败：保存缺项；取得完整 ID、修复记录，或按使用者已有明确授权决定是否继续，不能写成“确认未重复”。空索引只表示当前工作目录尚无可核验记录。
6. 在 checkpoint 记录检查时间、来源 ID、索引时间、结果与重做授权。每条完成后执行第 15 步登记，批次内来源也须去重。检查只读取其他任务的最少字段，不能接管它们的页或 checkpoint。

### 1. 打开已配置工作台并确认登录

1. 读取 [configuration.md](configuration.md)，解析 `WORKBENCH_URL`；未设置时先向使用者取得自己的后台地址，不猜作者地址。视频分享链接只作为输入。
2. 新运行在可用 Chrome 浏览器创建独立工作台标签并记录工具实际返回的浏览器/标签 ID。续做只接回本次 checkpoint 中的标签，按 [task-isolation.md](task-isolation.md) 核对内容。
3. 核对实际站点身份和已登录状态；兼容界面通常包含 `香天下集团/营销智脑`、`生产部门`、`爆款大师`、`剪辑高手` 等导航。贴牌界面以使用者指定站点和当前导航为准；模块缺失时报告实际差异。
4. 需要登录、验证码或账号授权时，让使用者在该标签完成。不要索取或保存密码、Cookie、验证码，不自动勾选新的法律协议。登录完成后重新核对该标签页面。

影响范围：本次独立后台页；配置与凭证留在使用者本机。

### 2. Open Burst Master One-Click And Extract Source Copy

1. From the logged-in workbench, expand `生产部门` in the left navigation if it is collapsed.
2. Click `爆款大师`.
3. Verify the `爆款大师` page appears, with the `爆款大师` tab/title and employee ability cards.
4. Click the `一键追爆` ability card.
5. Verify the `一键追爆 · AI自动智能体` page appears.
6. Confirm the top row exposes `获取链接教程`, a platform dropdown such as `某音链接` or `抖音链接`, the URL input field, and the right-side `AI自动一键生成&发布` button.
7. Put the supplied `SOURCE_URL` directly into the URL input to the right of the platform dropdown and verify the field matches it; do not replace it with an unrelated open Douyin tab's address. If the user supplied only `COPY`, skip URL extraction and continue to step 3. Ask for input only when neither `SOURCE_URL` nor `COPY` was provided.
8. Click the section `1 文案提取` button `提取文案`. Do not click the top `AI自动一键生成&发布` button.
9. Verify the extraction modal appears with `文案提取` and text like `正在对视频中的文案进行提取中`.
10. Wait until the modal closes and the `文案提取` text area is filled. Do not click `停止执行` or `后台执行` unless the user explicitly asks.
11. Record the extracted text as `EXTRACTED_COPY` in this run's checkpoint, verifying its length, beginning, and ending text. Keep the original user source identity alongside it.
12. Stop and ask if extraction fails, the result is empty, a login/permission prompt appears, or the page requests non-standard payment/compute.

Impact scope: submit one user-provided source URL for copy extraction only; do not publish.

### 3. 文案改写与质量核对

1. `SOURCE_URL` 成功提取后记录 `EXTRACTED_COPY`；直接 `COPY` 按使用者是否允许改写执行。明确要求原文时跳过网页改写。
2. 需要改写时核对 `文案提取` 字段，选择页面 `文案改写` 的 `自动`（或使用者指定模式），点击一次 `执行改写`，等待返回并记录完整 `REWRITTEN_COPY`。
3. 按 [copy-quality.md](copy-quality.md) 检查口播正文、长度、结构及明显夸大断言。本包自带检查标准，不依赖未随包提供的优化 skill。
4. 符合本次要求时使用返回稿；不符合且本次已经授权优化时，在现有授权范围内修订并保留前后稿。尚未授权改变文意时，在付费生成前展示完整稿和具体问题，取得优化、替换或停止决定。
5. 更换页面口播前先清空旧字段并核对为空，再写入最终 `COPY`，读取长度、开头、结尾；将接受稿及对应摘要保存到本次 checkpoint。不可把多段稿拼接成重复口播。

影响范围：本次稿件提取/改写与已授权的修订；不发布。

### 4. Generate Audio

1. Confirm the audio generation settings before clicking:

   - 声音模型：仅从使用者配置的 `ALLOWED_VOICE_MODELS` 中选择；通过实际卡片选中状态核验并记录名称，不凭形象推断。
   - 语速: `AUDIO_SPEED`（默认 `1.1`）
   - 语调: `AUDIO_PITCH`（默认 `1.0`）
   - 音量: `AUDIO_VOLUME`（默认 `100`）
   - The narration field matches this run's accepted `COPY` by length, beginning, and ending text.
2. Confirm `生成音频` is enabled.
3. Take a screenshot before clicking for traceability.
4. Click `生成音频`.
5. Verify the page shows an audio generation state or result.
6. If `DOWNLOAD_AUDIO` is not true, do not download the audio; continue to digital-human video generation.
7. If `DOWNLOAD_AUDIO` is true, use the generated audio result's `下载` action after the audio is available. Save to the configured local download folder:
   `DOWNLOAD_DIR`
8. Prefer `{DOWNLOAD_TITLE}（音频）-{RUN_ID}.mp3` when naming is available; otherwise record the actual download-to-run association. Do not overwrite another task's file.
9. Verify the audio file exists and has nonzero size, then record the path as `AUDIO_FILE`.

Impact scope: submit the current copy for audio generation; optionally create one local audio file only if the user requested it.

### 5. Generate Digital-Human Video

生成前核对使用者允许的 `AVATAR_NAMES`，批量可在该列表中轮换；列表为空时先确认本次允许的形象。形象变化不得改变允许的声音列表。

1. In this run's `数字人视频生成`, verify the accepted narration and generated audio belong to this run, then locate the unique `生成视频` button.
2. Confirm it is enabled.
3. Click `生成视频` only when authorized.
4. Verify a generation signal appears.
5. Wait until this run's video/source result appears or a confirmed failure is shown; save progress for interruption and recovery.
6. Do not click `后台执行` or `停止执行` unless the user asks.
7. Record the UI-exposed digital-human source URL/asset ID, actual generation time, actual duration when available, and narration anchors in this run's checkpoint. Use `null` for unavailable fields. Keep source identity separate from the later packaged result; do not download the source as a default.

Impact scope: submit and wait for digital-human video generation.

### 6. Skip One-Click Smart Clip And Generate Title

This is mandatory in the `爆款大师 / 一键追爆` page after digital-human video generation. The final packaging is not done here.

1. Locate the page step `5 智能剪辑` skip switch by section context, not by switch position alone.
2. Turn on skip for `智能剪辑`.
3. Click `生成标题/话题`.
4. Wait until the title/topic textarea is filled and title/topic generation has finished.
5. Preserve the original webpage output as `generated_title_topics`. Separate the headline as `TITLE` and normalize `TOPICS` to exactly 5 distinct hashtags, including configured `REQUIRED_TOPIC` once when present, with the remaining topics relevant to the actual content. If the fixed topic is already present, count it among the 5; if it was appended to `TITLE`, move it to `TOPICS`. Deduplicate first, trim excess topics, or add relevant topics to reach 5.
6. Fill the combined title/topic textarea with `TITLE` on the first line and the 5 space-separated hashtags on the next line. When the page provides separate fields, fill the title and topic fields separately. Read back to verify the headline and exactly 5 distinct topics, including configured `REQUIRED_TOPIC` once when present.
7. Record the verified `TITLE` and final `TOPICS` in this run checkpoint; use these same topics in the delivery list and final response.
8. Do not configure final template, persona, background music, volume, or upload materials in this one-click page.
9. Do not enter publishing.

Impact scope: only skip `智能剪辑` and generate title/topics.

### 7. Preserve Source Identity For Library Reuse

1. Read [work-library-source.md](work-library-source.md). Preserve this run's generated source identity before leaving `一键追爆`.
2. Prefer selecting the existing source through the smart-packaging `上传视频 -> 点击上传 -> 作品库` picker in step 9. Leave `source_file = null`; a cloud source does not require a local MP4 backup.
3. Only download the plain source when the user requests it or the library route has a concrete limitation and local transfer is needed. Follow the fallback in the reference; an unlocated asset alone is not permission to use a different video or regenerate.

Impact scope: record this run's source identity; normally create no local source-video file.

### 8. Open Clip-Expert Smart Packaging

1. Open `生产部门` in the left navigation. If collapsed, click its expand area.
2. Click `剪辑高手`.
3. Open `智能包装`.
4. Confirm this is the `剪辑高手 -> 智能包装` page, not the embedded `一键追爆` smart-clip section.
5. Confirm the page exposes `上传视频`, `模板`, `标题`, `人设`, `背景音乐`, `上传素材`, `调节音量`, and `进行智能剪辑`.
6. Stop here if the user wants to give the next instruction.

Impact scope: navigation only.

### 9. Select This Run's Source From Works

1. In the owned smart-packaging tab, click page-left `上传视频 -> 点击上传` to open `上传文件`.
2. Select the modal's `作品库` tab, then `我的` / the observed save location and `视频`. This is distinct from `手动上传`, `素材库`, and the right-side output history.
3. Follow [work-library-source.md](work-library-source.md) to identify this run's plain digital-human video. Match source identity and content; neither the newest item nor the same avatar is enough. Generated sources may be named `未命名_...`.
4. Select exactly one matching item and click the modal's `确定`. Verify the loaded **source** player against `SOURCE_ASSET` before configuring or submitting packaging. If the modal lacks a preview, a narrowly matched candidate can be loaded provisionally and verified there before any paid action.
5. Record `source_transfer = work_library`, observed asset evidence, and actual duration. Do not download or reupload a second copy when this succeeds.
6. Use `手动上传` only for an explicitly supplied local file or the justified local fallback in the reference. Record `source_transfer = local_upload` and its exact per-run file path.

Impact scope: select one existing source into this run's editor; normally no download, local upload, or new generation.

### 10. Configure Smart Packaging

1. Template:
   - **Choose autonomously.** `清新、安静、少营销感` is a style preference, not an exact preset name or a condition requiring user approval. Unless the user specifically wants to choose, select the closest suitable option and continue.
   - Prefer readable subtitles, limited face obstruction, restrained colors, and few decorative effects. Template thumbnails contain sample titles; judge layout and emphasis rather than treating every large example headline as permanent promo copy. Verify the actual output later for unwanted retained wording.
   - Inspect the current template strip or open its `更多` modal. If needed, compare up to two additional screens, then choose the best available candidate. Do not exhaust the catalog looking for a perfect style or ask the user to choose because all examples have headlines.
   - Verify selection from the actual template card's blue border or the tool-exposed selected state, then click modal `确定` when present. Record the observed preset ID/name or card description in this run's checkpoint. A main/history preview does not prove a preset is selected.
   - If cards are unloaded or the active state is unclear, take a fresh screenshot of this owned tab, wait for the visible loading state to finish, or reopen the template modal once. Do not inspect duplicate workbench tabs. Only an unresolved technical inability to load/select/confirm a template blocks submission; report that exact fault and captured evidence, without turning it into a request for the user's aesthetic choice.
   - If the user rejects a template, choose a closer fit from their feedback and confirm it through the same card/modal controls.

2. Title:
   - Turn on the `标题` switch.
   - Fill `TITLE`.

3. Persona:
   - Turn on the `人设` switch only when `PERSONA` is configured.
   - Select configured `PERSONA` and verify it; when unset, keep the persona switch off. If the named persona is unavailable, report it rather than inventing a substitute.
   - When a persona modal was opened, click `确定` there.

4. Background music:
   - Configure this only on the `剪辑高手 -> 智能包装` page.
   - For this skill, select `无音乐`; do not leave `智能匹配` selected.
   - Set the smart-packaging `调节音量` control to configured `VOLUME` (default `10`) and read back the actual value.
   - If selecting `无音乐` hides or disables the volume control, keep `无音乐` selected and note in the final response that volume could not be adjusted.
   - If the user explicitly asks for `智能匹配` or another track, follow that instruction and still verify the visible volume setting.

5. Material:
   - Do not upload extra素材 by default.
   - Verify the `上传素材` area only has the upload entry.

6. Pre-submit verification:
   - Screenshot the configured page.
   - Verify the source player contains this run's matched library asset or verified local source.
   - Verify the selected template from the left template strip or `更多` modal, using the blue border/active state; do not treat the main/right preview or a green/fresh-looking image as template confirmation.
   - Verify `TITLE` is filled and matches the checkpoint headline.
   - Verify the checkpoint `TOPICS` contains exactly 5 distinct hashtags, with configured `REQUIRED_TOPIC` once when present and other content-relevant topics. Read back any topic field available on the current page; correct a mismatch before submission.
   - Verify the selected persona is `PERSONA` or the disabled persona switch when unset.
   - Verify `无音乐` is selected in `剪辑高手 -> 智能包装`.
   - Verify `调节音量` matches `VOLUME` when the control is visible/available.
   - Update this run's exact `CHECKPOINT_PATH` with browser/tab, `TITLE`, the verified 5 `TOPICS`, narration anchors, source asset evidence (`source_file` only for local transfer), actual duration, selected template, settings, and pre-submit screenshot. Use [smart-packaging-preview-download.md](smart-packaging-preview-download.md) for the fields and result-identification procedure.
   - When configuration matches this run's authorized workflow, click `进行智能剪辑` without adding an ordinary pre-submit approval step. Resolve actual permission, abnormal payment or out-of-scope actions under the main skill rules.

Impact scope: current smart-packaging configuration only.

### 11. 提交并记录受理状态

进入本阶段先读 [smart-packaging-preview-download.md](smart-packaging-preview-download.md)，恢复本阶段时也重读其中的“先激活再判断”顺序。

1. 配置核验通过后，点击本次唯一的 `进行智能剪辑` 一次，记录 `submission_attempted_at` 和点击前后的页面证据。
2. 观察本次页面的 `生成中 xx%`、`制作中...` 或明确任务受理信息，再记录 `submission_acknowledged_at`。仅按钮变为加载状态是提交尝试，不能直接报生成完成。
3. 保存带时区的时间、可见任务 ID（未显示为 `null`）和最新进度。时间戳不是任务 ID，不把页面显示时间写成 `job_id`。
4. 受理后持续等待；`99%`、进度消失或出现“下载/重新生成”行只触发下一步查找结果，不能跳过历史预览直接下载，也不能宣称成片核验完成。
5. 没有受理证据时先读本次错误/校验提示并核对作品库；状态不明不反复点击。已受理而找不到结果时先完成第 12 步两条定位路径，不把“补提一次”作为默认处理。

影响范围：提交本次配置并消费页面显示的算力；不因预览未载入追加提交。

### 12. 先点击本次右侧预览，再核验成片

1. **定位右侧记录。** 在本次绑定标签的 `历史记录` 中按标题、口播、提交时间及源片时长找候选，必要时看新截图并滚动历史面板。第一条、同一人物、相同房间均不代表本次结果。
2. **实际点击是必做动作。** 点开匹配候选的**右侧视频缩略图/预览区域**，观察卡片选中与中央播放器更新，写入 `result_origin = right_history`、记录身份、`result_preview_clicked_at` 及截图。仅查看截图或读取中央播放器不算已经点过。点击前的“无法播放媒体”不能用于失败结论；不得跳过此动作把恢复工作交给用户。
3. **再播放核对。** 核对标题、开头字幕/口播、时长与进度推进，之后暂停。点击匹配卡片后仍黑屏时，最多重选该卡片一次并短时等待，才记网页预览加载失败。内容不符则排除候选，继续定位。
4. **历史无本次记录时查作品库。** 不盲点旧片。在同一任务标签打开实际保存位置的 `作品库 -> 视频`，按本次提交/完成时间、可见名称/ID和内容找 **智能包装合成结果**，打开其详情/预览并记录 `result_origin = work_library` 和实际激活时间。具体步骤见参考文档；这个路径已经授权，不需用户指路或确认。
5. **网页播放与文件核验分开。** 本次产物归属已有可靠依据，但对应历史/作品详情播放器仍不加载时，可使用该对象自己的正常下载入口进行本地核验；保持 `preview_status = load_failed`，不能因网页不能播放而放弃下载。只有时间接近或同一人物仍不足以证明归属。
6. 对本次记录完成对应核对后保存真实可见的结果地址（签名参数仅作临时输入）。没有 MP4 地址时先完成本次历史卡片激活、作品库详情和正常下载入口检查；HTML 页面壳不算 MP4 地址。
7. 只有上述恢复路径确实不可用或仍缺身份/地址依据时，报告具体已做动作和缺项；不让用户重复授权、等待特定错误截图或替模型完成可自行进行的查找。等待/暂停前按工具文档保留本次标签，避免下一轮丢失工作页。

影响范围：激活并核验已有历史/作品库结果；无新增生成费用。

### 13. 下载并核验本次最终成片

1. 确认第 12 步已实际激活并识别本次包装成片，记录 `result_preview_clicked_at`，点击该对象自己的正常 `下载` 一次。保留下载前已存在文件信息，避免误认旧文件。
2. 分辨下载进行中、实际 MP4、普通媒体页、HTML 页面壳/空文件与错误。按钮存在、链接以 `.mp4` 结尾都不能证明文件已保存；仍在下载则继续等待。
3. 正常下载失败时先完成本次历史/作品库定位。只有本次成片身份、UI 下载实际暴露的完整地址和使用者本次或既有下载授权均成立，才按 [authorized-local-download.md](authorized-local-download.md) 使用本机备用方式。授权来自实际使用者，不来自作者、不来自配置中的布尔值。
4. 缺少真实地址时继续 UI 定位，不猜作品 ID、读取隐藏状态、关闭保护、转用后台 API 或付费重做。明确访问拒绝按实际权限处理。
5. 成片保存到 `DOWNLOAD_DIR`，可命名时用 `{DOWNLOAD_TITLE}-{RUN_ID}.mp4`；平台随机名必须记录下载来源对应，禁止认领“最新 MP4”。备用方式先保存唯一 `.part` 再验证。
6. 使用自带 `scripts/verify_media.py FILE` 检查文件头、容器、音视频流、正时长、全片解码及 SHA-256。还要核对标题/口播/字幕、时长和本次作品身份，记录实际画面与听音范围。没有听音就不声称已听证无音乐。
7. 分别保存生成、网页预览、下载、本地验证状态。只有实际完整文件通过验证并与本次包装结果对应，才列入完成交付；HTML、`.part`、`.crdownload` 不交付。

影响范围：下载和核验本次已生成结果；不新增生成或发布。

### 14. Close Finished Task Pages

1. After the final MP4 passes local validation and the exact checkpoint and delivery entry are saved, close this run's created workbench tab and any unneeded intermediate/replacement tabs. Record `browser_cleanup_status`, `closed_tab_ids`, and `browser_cleanup_at` in the checkpoint.
2. In a batch, perform this cleanup after every completed video. Keep only pages required for currently unfinished work.
3. After the final item, inspect tab ID metadata once and verify that all tabs created by this batch are gone. When supported, remove only this batch's empty session/group. Do not claim group removal unless verified; if the browser removes empty groups automatically, record the observed result.
4. Close only tabs/groups whose creation is recorded for this run/batch. Preserve user-created and other-task pages. If the user explicitly requests a finished page remain open, keep only that named page and record the exception.

Impact scope: release browser resources used by this task only; preserve unfinished-task state and the user's other pages.

### 15. 完成后更新本机来源清单

1. 保存本次已核验结果的来源、`source_video_id`、`title`、`completed_at`、`generation_status = verified`、`local_validation_status = passed`、`local_file`、`result_identity_evidence` 及媒体验证信息到本次 checkpoint；不存签名参数和凭证。
2. 运行 `scripts/recent_sources.py refresh --runs-dir RUN_ROOT --output INDEX_PATH`。每条完成后刷新，批次结束前再次刷新并重读，核对本批全部可索引的已完成来源。默认滚动 168 小时，以核验完成时间为准。
3. 此步骤是登记，不能将自己的新记录判为重复而移出本次交付列表。仅提交、提取、失败状态不计入已生成；核验完成后文件消失仍保留生成证据并标记文件缺失。
4. 脚本检查失败、缺少来源 ID 或记录不完整时保留实际状态；修复后重跑，不手改统计数字。确实无法刷新时在交付中说明未完成项，不编造来源。

影响范围：本机运行记录与来源索引；不触发平台生成或发布。
