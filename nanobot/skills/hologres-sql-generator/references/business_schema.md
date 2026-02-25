# 业务数据表元数据定义

本文件定义了业务查询中常用的表结构、字段及其数据类型。在生成 SQL 时，应严格参考此处的定义。

## 业务缩写映射 (Business Abbreviations)

为了准确识别用户意图，请遵循以下缩写映射规则：

| 缩写/关键词 | 完整业务含义 | 对应字段前缀 |
| :--- | :--- | :--- |
| **tt** | **TikTok** | `tt_...` |
| **lzd** | **Lazada FastCash** | `lzd_...` |
| **cashloan** / **CL** | **现金贷** | `cashloan_...` |
| **newct** | 新客 | `newct_...` |
| **oldct** | 老客 | `oldct_...` |

## 数据表：`rpt_holo.coll_owner_repay_daily`

### 字段列表

| 字段名 | 数据类型 | 业务含义说明 |
| :--- | :--- | :--- |
| `datas_refresh_time` | `text` | 数据刷新时间 |
| `datas_refresh_hour` | `text` | 数据刷新小时 |
| `owner_id` | `bigint` | 负责人 ID |
| `owner_name` | `text` | 负责人姓名 |
| `bucket` | `text` | 逾期阶段 (Bucket) |
| `group_split` | `text` | 分组拆分 |
| `group_name` | `text` | 组名 |
| `group_name_abbr` | `text` | 组名简称 |
| `workplace` | `text` | 工作地点 |
| `moudle` | `text` | 模块 |
| `owing_cnt` | `numeric(38,15)` | 欠款件数 |
| `owing_amount` | `numeric(38,15)` | 欠款金额 |
| `newct_moudle_owing_amount` | `numeric(38,15)` | 新 CT 模块欠款金额 |
| `oldct_moudle_owing_amount` | `numeric(38,15)` | 老 CT 模块欠款金额 |
| `owing_principal` | `numeric(38,15)` | 欠款本金 |
| `newct_moudle_owing_principal` | `numeric(38,15)` | 新 CT 模块欠款本金 |
| `oldct_moudle_owing_principal` | `numeric(38,15)` | 老 CT 模块欠款本金 |
| `repay_cnt` | `numeric(38,15)` | 还款件数 |
| `repay_amount` | `numeric(38,15)` | 还款金额 |
| `repay_principal` | `numeric(38,15)` | 还款本金 |
| `new_moudle_owing_cnt` | `numeric(38,15)` | 新模块欠款件数 |
| `new_moudle_owing_amount` | `numeric(38,15)` | 新模块欠款金额 |
| `new_moudle_owing_principal` | `numeric(38,15)` | 新模块欠款本金 |
| `new_moudle_repay_cnt` | `numeric(38,15)` | 新模块还款件数 |
| `new_moudle_repay_amount` | `numeric(38,15)` | 新模块还款金额 |
| `new_moudle_repay_principal` | `numeric(38,15)` | 新模块还款本金 |
| `old_moudle_owing_cnt` | `numeric(38,15)` | 老模块欠款件数 |
| `old_moudle_owing_amount` | `numeric(38,15)` | 老模块欠款金额 |
| `old_moudle_owing_principal` | `numeric(38,15)` | 老模块欠款本金 |
| `old_moudle_repay_cnt` | `numeric(38,15)` | 老模块还款件数 |
| `old_moudle_repay_amount` | `numeric(38,15)` | 老模块还款金额 |
| `old_moudle_repay_principal` | `numeric(38,15)` | 老模块还款本金 |
| `target_repay_amount` | `numeric(38,15)` | 目标还款金额 |
| `user_type` | `text` | 用户类型 |
| `is_outs_owner` | `bigint` | 是否委外负责人 |
| `tt_owing_amount` | `numeric(38,15)` | **TikTok** 欠款金额 |
| `tt_newct_moudle_owing_amount` | `numeric(38,15)` | **TikTok** 新 CT 模块欠款金额 |
| `tt_oldct_moudle_owing_amount` | `numeric(38,15)` | **TikTok** 老 CT 模块欠款金额 |
| `tt_owing_principal` | `numeric(38,15)` | **TikTok** 欠款本金 |
| `tt_newct_moudle_owing_principal` | `numeric(38,15)` | **TikTok** 新 CT 模块欠款本金 |
| `tt_oldct_moudle_owing_principal` | `numeric(38,15)` | **TikTok** 老 CT 模块欠款本金 |
| `tt_repay_amount` | `numeric(38,15)` | **TikTok** 还款金额 |
| `tt_repay_principal` | `numeric(38,15)` | **TikTok** 还款本金 |
| `tt_new_moudle_owing_amount` | `numeric(38,15)` | **TikTok** 新模块欠款金额 |
| `tt_new_moudle_owing_principal` | `numeric(38,15)` | **TikTok** 新模块欠款本金 |
| `tt_new_moudle_repay_amount` | `numeric(38,15)` | **TikTok** 新模块还款金额 |
| `tt_new_moudle_repay_principal` | `numeric(38,15)` | **TikTok** 新模块还款本金 |
| `tt_old_moudle_owing_amount` | `numeric(38,15)` | **TikTok** 老模块欠款金额 |
| `tt_old_moudle_owing_principal` | `numeric(38,15)` | **TikTok** 老模块欠款本金 |
| `tt_old_moudle_repay_amount` | `numeric(38,15)` | **TikTok** 老模块还款金额 |
| `tt_old_moudle_repay_principal` | `numeric(38,15)` | **TikTok** 老模块还款本金 |
| `cashloan_owing_amount` | `numeric(38,15)` | **现金贷 (CL)** 欠款金额 |
| `cashloan_newct_moudle_owing_amount` | `numeric(38,15)` | **现金贷 (CL)** 新 CT 模块欠款金额 |
| `cashloan_oldct_moudle_owing_amount` | `numeric(38,15)` | **现金贷 (CL)** 老 CT 模块欠款金额 |
| `cashloan_owing_principal` | `numeric(38,15)` | **现金贷 (CL)** 欠款本金 |
| `cashloan_newct_moudle_owing_principal` | `numeric(38,15)` | **现金贷 (CL)** 新 CT 模块欠款本金 |
| `cashloan_oldct_moudle_owing_principal` | `numeric(38,15)` | **现金贷 (CL)** 老 CT 模块欠款本金 |
| `cashloan_repay_amount` | `numeric(38,15)` | **现金贷 (CL)** 还款金额 |
| `cashloan_repay_principal` | `numeric(38,15)` | **现金贷 (CL)** 还款本金 |
| `cashloan_new_moudle_owing_amount` | `numeric(38,15)` | **现金贷 (CL)** 新模块欠款金额 |
| `cashloan_new_moudle_owing_principal` | `numeric(38,15)` | **现金贷 (CL)** 新模块欠款本金 |
| `cashloan_new_moudle_repay_amount` | `numeric(38,15)` | **现金贷 (CL)** 新模块还款金额 |
| `cashloan_new_moudle_repay_principal` | `numeric(38,15)` | **现金贷 (CL)** 新模块还款本金 |
| `cashloan_old_moudle_owing_amount` | `numeric(38,15)` | **现金贷 (CL)** 老模块欠款金额 |
| `cashloan_old_moudle_owing_principal` | `numeric(38,15)` | **现金贷 (CL)** 老模块欠款本金 |
| `cashloan_old_moudle_repay_amount` | `numeric(38,15)` | **现金贷 (CL)** 老模块还款金额 |
| `cashloan_old_moudle_repay_principal` | `numeric(38,15)` | **现金贷 (CL)** 老模块还款本金 |

> **注意**：所有 `numeric(38,15)` 类型的字段在进行除法运算时，务必显式转换为 `::float` 以确保计算精度。
