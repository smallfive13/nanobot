---
name: hologres-sql-generator
description: 将用户自然语言需求转化为阿里云 Hologres SQL。适用于：根据表结构、字段和指标定义生成 SELECT 语句，支持 Hologres 特有语法优化。
metadata: {"nanobot":{"always":true}}
---

# Hologres SQL Generator

此技能专门用于将用户的业务需求转化为高性能的阿里云 Hologres SQL (SELECT 语句)。它能够理解复杂的业务逻辑，并将其映射到提供的数据模型上。

## 核心能力

1. **意图识别**：解析用户自然语言中的维度、指标、过滤条件和时间范围。特别支持业务缩写识别（如 tt -> TikTok, CL -> 现金贷）。
2. **SQL 生成**：生成符合 Hologres 语法的标准 SQL，默认仅生成 `SELECT` 语句。
3. **性能优化**：根据查询需求，合理使用 Hologres 的特性。具体参考 `references/hologres_best_practices.md`。

## 使用流程

1. **加载元数据与缩写映射**：
    - **优先读取**：首先读取 `references/business_schema.md` 获取预定义的表结构、字段、类型及**业务缩写映射规则**。
    - **补充上下文**：检查当前环境中是否存在由上游技能提供的额外元数据文件。
2. **解析需求**：结合元数据和缩写规则，从用户的自然语言需求中提取关键信息：
    - **业务实体识别**：识别用户提到的“TikTok”、“CL”、“现金贷”等关键词，并映射到对应的字段前缀（如 `tt_` 或 `cashloan_`）。
    - **维度 (Dimensions)**：通常对应 `GROUP BY` 子句。
    - **指标 (Metrics)**：需要进行聚合计算的字段。
3. **构建 SQL**：基于解析出的信息，按照 `references/hologres_best_practices.md` 中定义的最佳实践，逐步构建 `SELECT` 语句。
4. **自检与修正**：检查生成的 SQL，确保所有引用的字段和表都在元数据中存在，聚合函数使用正确，且整体语法符合 Hologres 标准。
5. **当用户要“执行/查询/跑一下”时（必须）**：
   1. 先把最终 SQL 输出给用户（用于审阅）
   2. 必须调用 `exec` 工具执行 `hologres-query` 脚本，先 EXPLAIN 再查询，不要只输出命令
   3. 执行命令时必须加 `--yes`，避免脚本交互确认导致 CLI 卡住
   4. 执行命令时应加 `--save --name "<建议名称>" --save-dir workspace/memory/hologres-sql`，并在回复中标注 `Saved: <record>.json`
   5. 将脚本 stdout/stderr（包含 EXPLAIN 与结果）整理到最终回复中
   6. 询问用户是否“确认保存口径正确”；若用户回复确认，你必须调用 `hologres_sql_approve`，把该 record 写入 `workspace/memory/HOLOGRES_SQL.md`

## 执行命令模板（给 exec 工具）

假设用户已把连接信息保存到 `~/.nanobot/hologres-query.json`（推荐方式），则执行命令为：

```bash
python nanobot/skills/hologres-query/scripts/hologres_query.py \
  --config ~/.nanobot/hologres-query.json --profile default \
  --sql "<PUT_SQL_HERE>" --yes \
  --save --name "<NAME>" --save-dir workspace/memory/hologres-sql
```

## 示例参考

### 需求：统计各组 TikTok 的还款金额和 CL 的欠款金额

**意图解析**：
- “TikTok” 映射到 `tt_` 前缀字段。
- “CL” 映射到 `cashloan_` 前缀字段。

**生成的 SQL**：
```sql
SELECT
  -- 【维度列】
  track."group_name"                   AS group_name,
  -- 【TikTok 统计】
  SUM(track."tt_repay_amount")         AS tt_total_repay_amount, -- TikTok 还款金额汇总
  -- 【现金贷 (CL) 统计】
  SUM(track."cashloan_owing_amount")   AS cl_total_owing_amount  -- 现金贷欠款金额汇总
FROM "rpt_holo"."coll_owner_repay_daily" AS track
WHERE 
  track."datas_refresh_time" = TO_CHAR(CURRENT_DATE, 'YYYY-MM-DD')
GROUP BY 
  1
;
```
