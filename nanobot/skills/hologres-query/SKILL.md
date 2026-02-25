---
name: hologres-query
description: 安全查询 Hologres：必须先 EXPLAIN 并做风控阻断；再执行查询；结果自动转 Markdown 或导出 Excel。用户要跑 Hologres 查询时调用。
metadata: {"nanobot":{"always":true,"requires":{"bins":["python3"]}}}
---

# hologres-query Skill

## 目标

当用户要查询 Hologres 时，必须走安全流程：

1. 先给出 SQL（参数化）
2. 执行 EXPLAIN，展示计划与关键指标
3. 如果 EXPLAIN 估算代价/数据量过大，默认直接阻断（防止集群异常）
4. 只有在 EXPLAIN 通过风控且用户确认后，才执行真实查询
5. 输出规则：
   - `<= 20` 行：Markdown 表格
   - `> 20` 行：导出 Excel，并给出前 10 行预览

## 脚本位置与执行

- 脚本路径：`{baseDir}/scripts/hologres_query.py`
- 连接信息传递方式：
  - 推荐：写到本机 `~/.nanobot/hologres-query.json`（脚本会自动读取，如果文件存在）
  - 或：在命令行用参数传入（会覆盖配置文件）
- 示例配置模板：`{baseDir}/scripts/hologres-query.config.example.json`

直接执行（建议用 Python 3.11+）：

```bash
python {baseDir}/scripts/hologres_query.py \
  --host "<Endpoint>" --port 80 --dbname "<db>" --user "<AccessId>" --password "<AccessKey>" \
  --sql "SELECT 1"

python {baseDir}/scripts/hologres_query.py \
  --host "<Endpoint>" --port 80 --dbname "<db>" --user "<AccessId>" --password "<AccessKey>" \
  --sql "SELECT * FROM t WHERE ds=%s" --params 2026-02-07

# 使用配置文件（默认会尝试读取 ~/.nanobot/hologres-query.json）
python {baseDir}/scripts/hologres_query.py --sql "SELECT 1"

# 指定配置文件与 profile
python {baseDir}/scripts/hologres_query.py \
  --config ~/.nanobot/hologres-query.json --profile default \
  --sql "SELECT 1"
```

安装依赖：

```bash
pip install "psycopg[binary]" openpyxl
```

## 在 nanobot 里必须“实际执行”的要求

skills 只是说明书，不会自动执行。用户明确说“执行/查询/跑一下”时：

1. 先用 `read_file` 读本 skill 的 `SKILL.md`（如果尚未加载）
2. 必须调用 `exec` 工具执行脚本（不要只输出命令，不要只讲步骤）
3. 把脚本 stdout/stderr 里的 EXPLAIN 与查询结果整理进最终回复（不要依赖 `message` 工具把结果发到 CLI）
4. 默认执行查询时应加 `--save --name "<建议名称>" --save-dir workspace/memory/hologres-sql`，确保生成可追溯的记录 JSON（控制台会打印 `Saved: <record>.json`）。
5. 用户确认口径正确的反馈机制：当用户回复“确认保存”，你必须调用 `hologres_sql_approve` 工具，将该 `Saved: ...json` 记录写入 `workspace/memory/HOLOGRES_SQL.md`（需要用户给一个标题/用途/口径说明）。
6. 非交互环境（例如 gateway / 机器人通道）禁止等待 `input()`：必须用“两步确认”流程
   - 第一步：执行脚本但不加 `--yes`，只拿到 EXPLAIN（脚本会明确提示“query NOT executed”）
   - 第二步：用户回复“YES/确认执行”后，再 `exec` 重新运行同一条 SQL，并加 `--yes`（必要时再加 `--force`）

## 风控（必须）

脚本会使用 `EXPLAIN (FORMAT JSON)` 解析计划，提取：

- 估算行数（Plan Rows）
- 总代价（Total Cost）

当任一阈值超过时，默认阻断并退出，不执行真实查询。可用以下参数调整：

- `--max-plan-rows 5000000`
- `--max-total-cost 10000000`

如果用户明确愿意承担风险，才允许用 `--force` 绕过阻断继续执行（仍需交互确认或 `--yes`）。
