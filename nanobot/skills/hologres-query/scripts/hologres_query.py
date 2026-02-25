#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional, Tuple


@dataclass(frozen=True)
class HologresConn:
    host: str
    port: int
    dbname: str
    user: str
    password: str
    application_name: str = "hologres-query"


def _require_package(import_name: str, install_hint: str) -> Any:
    try:
        return __import__(import_name)
    except ModuleNotFoundError as e:
        raise SystemExit(f"Missing dependency: {import_name}\nInstall: {install_hint}") from e


def connect(conn: HologresConn):
    psycopg = _require_package("psycopg", 'pip install "psycopg[binary]"')
    return psycopg.connect(
        host=conn.host,
        port=conn.port,
        dbname=conn.dbname,
        user=conn.user,
        password=conn.password,
        keepalives=1,
        keepalives_idle=130,
        keepalives_interval=10,
        keepalives_count=15,
        application_name=conn.application_name,
    )


def _iter_rows(cur, arraysize: int = 2000) -> Iterable[tuple]:
    while True:
        batch = cur.fetchmany(arraysize)
        if not batch:
            break
        yield from batch


def _escape_md_cell(value: Any) -> str:
    if value is None:
        return ""
    s = str(value)
    s = s.replace("\n", "\\n").replace("|", "\\|")
    return s


def to_markdown(headers: list[str], rows: list[tuple]) -> str:
    cols = len(headers)
    norm_rows = [tuple("" if v is None else v for v in r) for r in rows]

    widths = [len(h) for h in headers]
    for r in norm_rows:
        for i in range(cols):
            widths[i] = max(widths[i], len(_escape_md_cell(r[i])))

    def fmt_row(values: Iterable[Any]) -> str:
        cells = [_escape_md_cell(v) for v in values]
        padded = [cells[i].ljust(widths[i]) for i in range(cols)]
        return "| " + " | ".join(padded) + " |"

    lines = [fmt_row(headers), "| " + " | ".join("-" * w for w in widths) + " |"]
    lines.extend(fmt_row(r) for r in norm_rows)
    return "\n".join(lines)


def export_excel(headers: list[str], rows_iter: Iterable[tuple], out_path: str) -> None:
    openpyxl = _require_package("openpyxl", "pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "query"

    ws.append(headers)
    for r in rows_iter:
        ws.append(list(r))
    wb.save(out_path)


def _normalize_explain_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, str):
        data = json.loads(payload)
    else:
        data = payload
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    raise TypeError(f"Unexpected EXPLAIN payload type: {type(payload)}")


def _extract_plan_metrics(explain: list[dict[str, Any]]) -> Tuple[Optional[float], Optional[int]]:
    if not explain:
        return None, None
    root = explain[0]
    plan = root.get("Plan") or {}
    total_cost = plan.get("Total Cost")
    plan_rows = plan.get("Plan Rows")
    try:
        total_cost_f = float(total_cost) if total_cost is not None else None
    except (TypeError, ValueError):
        total_cost_f = None
    try:
        plan_rows_i = int(plan_rows) if plan_rows is not None else None
    except (TypeError, ValueError):
        plan_rows_i = None
    return total_cost_f, plan_rows_i


def _load_json_file(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError("Config must be a JSON object")
    return data


def _get_default_config_path() -> Path:
    return Path(os.path.expanduser("~/.nanobot/hologres-query.json"))


def _select_profile(config: dict[str, Any], profile: str) -> dict[str, Any]:
    profiles = config.get("profiles")
    if isinstance(profiles, dict):
        p = profiles.get(profile)
        if p is None:
            raise KeyError(f'Profile "{profile}" not found in config')
        if not isinstance(p, dict):
            raise TypeError(f'Profile "{profile}" must be a JSON object')
        return p
    return config


def _merge_conn_args(cfg: dict[str, Any], args: argparse.Namespace) -> HologresConn:
    host = args.host if args.host is not None else cfg.get("host", "")
    port = args.port if args.port is not None else cfg.get("port", 80)
    dbname = args.dbname if args.dbname is not None else cfg.get("dbname", "")
    user = args.user if args.user is not None else cfg.get("user", "")
    password = args.password if args.password is not None else cfg.get("password", "")
    application_name = (
        args.application_name
        if args.application_name is not None
        else cfg.get("application_name", "hologres-query")
    )

    try:
        port_i = int(port)
    except (TypeError, ValueError):
        raise SystemExit("Invalid port in args/config; must be an integer")

    return HologresConn(
        host=str(host),
        port=port_i,
        dbname=str(dbname),
        user=str(user),
        password=str(password),
        application_name=str(application_name),
    )


def _risk_block(
    total_cost: Optional[float],
    plan_rows: Optional[int],
    max_total_cost: float,
    max_plan_rows: int,
) -> Tuple[bool, str]:
    reasons: list[str] = []
    if total_cost is not None and total_cost > max_total_cost:
        reasons.append(f"Total Cost {total_cost:.2f} > {max_total_cost:.2f}")
    if plan_rows is not None and plan_rows > max_plan_rows:
        reasons.append(f"Plan Rows {plan_rows} > {max_plan_rows}")
    if reasons:
        return True, "; ".join(reasons)
    return False, ""

def _slugify(value: str) -> str:
    s = value.strip().lower()
    out = []
    for ch in s:
        if ch.isalnum():
            out.append(ch)
        elif ch in {"-", "_"}:
            out.append(ch)
        else:
            out.append("-")
    slug = "".join(out).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "query"


def _default_save_dir() -> Path:
    return Path(os.path.expanduser("~/.nanobot/hologres-query/queries"))


def _save_record(
    save_dir: Path,
    name: str,
    sql: str,
    params: list[str],
    explain_json: list[dict[str, Any]],
    total_cost: Optional[float],
    plan_rows: Optional[int],
    blocked_reason: str,
    result_type: str,
    result_path: str,
    preview_markdown: str,
) -> Path:
    save_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"{ts}_{_slugify(name)}"

    sql_path = save_dir / f"{base}.sql"
    sql_path.write_text(sql.strip() + "\n", encoding="utf-8")

    meta = {
        "timestamp": ts,
        "name": name,
        "sql_file": sql_path.name,
        "params": params,
        "explain": explain_json,
        "explain_summary": {"total_cost": total_cost, "plan_rows": plan_rows},
        "blocked_reason": blocked_reason,
        "result": {"type": result_type, "path": result_path},
        "preview_markdown": preview_markdown,
    }
    meta_path = save_dir / f"{base}.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return meta_path


def explain_then_query(
    conn: HologresConn,
    sql: str,
    params: list[str],
    auto_yes: bool,
    force: bool,
    max_total_cost: float,
    max_plan_rows: int,
    save: bool = False,
    save_dir: Optional[Path] = None,
    save_name: str = "",
    excel_threshold: int = 20,
    preview_rows: int = 10,
) -> None:
    with connect(conn) as cxn:
        cxn.autocommit = True
        with cxn.cursor() as cur:
            cur.execute(f"EXPLAIN (FORMAT JSON) {sql}", params or None)
            explain_payload = cur.fetchone()
            explain_json = _normalize_explain_json(explain_payload[0] if explain_payload else [])
            total_cost, plan_rows = _extract_plan_metrics(explain_json)

            print("=== EXPLAIN (FORMAT JSON) ===")
            print(json.dumps(explain_json, ensure_ascii=False, indent=2))
            print("\n=== EXPLAIN SUMMARY ===")
            print(f"Total Cost: {total_cost if total_cost is not None else 'N/A'}")
            print(f"Plan Rows: {plan_rows if plan_rows is not None else 'N/A'}")

            blocked, reason = _risk_block(
                total_cost=total_cost,
                plan_rows=plan_rows,
                max_total_cost=max_total_cost,
                max_plan_rows=max_plan_rows,
            )
            if blocked and not force:
                if save:
                    meta_path = _save_record(
                        save_dir=save_dir or _default_save_dir(),
                        name=save_name or "blocked",
                        sql=sql,
                        params=params,
                        explain_json=explain_json,
                        total_cost=total_cost,
                        plan_rows=plan_rows,
                        blocked_reason=reason,
                        result_type="blocked",
                        result_path="",
                        preview_markdown="",
                    )
                    print(f"\nSaved: {meta_path}")
                raise SystemExit(
                    "Blocked by safety guard based on EXPLAIN.\n"
                    f"Reason: {reason}\n"
                    "Tune thresholds (--max-total-cost/--max-plan-rows) or use --force to override."
                )

            if not auto_yes:
                if not sys.stdin.isatty():
                    print("\n=== CONFIRMATION REQUIRED ===")
                    print("Non-interactive execution detected; query NOT executed.")
                    print('Re-run with --yes to proceed after EXPLAIN (or reply "YES" in chat).')
                    if save:
                        meta_path = _save_record(
                            save_dir=save_dir or _default_save_dir(),
                            name=save_name or "explain_only",
                            sql=sql,
                            params=params,
                            explain_json=explain_json,
                            total_cost=total_cost,
                            plan_rows=plan_rows,
                            blocked_reason="",
                            result_type="explain_only",
                            result_path="",
                            preview_markdown="",
                        )
                        print(f"\nSaved: {meta_path}")
                    return
                ans = input("\nProceed to run the query? [y/N]: ").strip().lower()
                if ans not in {"y", "yes"}:
                    print("Abort: query not executed.")
                    return

            cur.execute(sql, params or None)
            headers = [d.name for d in (cur.description or [])]

            preview: list[tuple] = []
            total = 0

            arraysize = 2000
            row_iter = _iter_rows(cur, arraysize=arraysize)
            buffered: list[tuple] = []

            for r in row_iter:
                total += 1
                if len(preview) < preview_rows:
                    preview.append(r)
                buffered.append(r)
                if total > excel_threshold:
                    break

            if total <= excel_threshold:
                buffered.extend(list(row_iter))
                total = len(buffered)
                md = to_markdown(headers, buffered)
                print("\n=== RESULT (Markdown) ===")
                print(md)
                print(f"\nRows: {total}")
                if save:
                    meta_path = _save_record(
                        save_dir=save_dir or _default_save_dir(),
                        name=save_name or "query",
                        sql=sql,
                        params=params,
                        explain_json=explain_json,
                        total_cost=total_cost,
                        plan_rows=plan_rows,
                        blocked_reason="",
                        result_type="markdown",
                        result_path="",
                        preview_markdown=md,
                    )
                    print(f"\nSaved: {meta_path}")
                return

            ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = f"hologres_query_{ts}.xlsx"

            def all_rows_iter():
                yield from buffered
                yield from row_iter

            export_excel(headers, all_rows_iter(), out_path)

            print("\n=== RESULT (Excel) ===")
            print(f"Saved: {out_path}")
            print("\n=== PREVIEW (Top 10, Markdown) ===")
            preview_md = to_markdown(headers, preview)
            print(preview_md)
            print(f"\nRows: > {excel_threshold}")
            if save:
                meta_path = _save_record(
                    save_dir=save_dir or _default_save_dir(),
                    name=save_name or "query",
                    sql=sql,
                    params=params,
                    explain_json=explain_json,
                    total_cost=total_cost,
                    plan_rows=plan_rows,
                    blocked_reason="",
                    result_type="excel",
                    result_path=str(Path(out_path).resolve()),
                    preview_markdown=preview_md,
                )
                print(f"\nSaved: {meta_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Hologres query helper (EXPLAIN first).")
    parser.add_argument(
        "--config",
        default="",
        help='Optional config JSON path (default: "~/.nanobot/hologres-query.json" if exists)',
    )
    parser.add_argument("--profile", default="default", help="Config profile name (default)")

    parser.add_argument("--host", default=None, help="Hologres endpoint host")
    parser.add_argument("--port", type=int, default=None, help="Hologres endpoint port")
    parser.add_argument("--dbname", default=None, help="Database name")
    parser.add_argument("--user", default=None, help="Access ID / username")
    parser.add_argument("--password", default=None, help="Access Key / password")
    parser.add_argument("--application-name", default=None)
    parser.add_argument("--sql", required=True, help="SQL text (use %s placeholders for params).")
    parser.add_argument(
        "--params",
        nargs="*",
        default=[],
        help="Positional parameters for %s placeholders (strings are passed as-is).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Run query after EXPLAIN without interactive confirmation.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Override safety guard that blocks large/slow plans.",
    )
    parser.add_argument("--max-total-cost", type=float, default=10_000_000)
    parser.add_argument("--max-plan-rows", type=int, default=5_000_000)
    parser.add_argument("--save", action="store_true", help="Save SQL + EXPLAIN + preview to files")
    parser.add_argument(
        "--save-dir",
        default="",
        help='Save directory (default: "~/.nanobot/hologres-query/queries")',
    )
    parser.add_argument("--name", default="", help="Optional name for saved record files")

    args = parser.parse_args()

    config: dict[str, Any] = {}
    config_path = Path(args.config).expanduser() if args.config else _get_default_config_path()
    if args.config:
        if not config_path.exists():
            raise SystemExit(f"Config file not found: {config_path}")
        config = _load_json_file(config_path)
    else:
        if config_path.exists():
            config = _load_json_file(config_path)

    profile_cfg = _select_profile(config, args.profile) if config else {}
    conn = _merge_conn_args(profile_cfg, args)

    if not all([conn.host, conn.dbname, conn.user, conn.password]):
        raise SystemExit(
            "Missing connection info.\n"
            "Provide via args or config: host/port/dbname/user/password\n"
            "Example:\n"
            '  python hologres_query.py --host "<Endpoint>" --port 80 --dbname "<db>" '
            '--user "<AccessId>" --password "<AccessKey>" --sql "SELECT 1"\n'
            'Config example: ~/.nanobot/hologres-query.json (supports profiles)'
        )

    explain_then_query(
        conn=conn,
        sql=args.sql,
        params=list(args.params),
        auto_yes=args.yes,
        force=args.force,
        max_total_cost=args.max_total_cost,
        max_plan_rows=args.max_plan_rows,
        save=bool(args.save),
        save_dir=Path(args.save_dir).expanduser() if args.save_dir else None,
        save_name=str(args.name or ""),
    )


if __name__ == "__main__":
    main()
