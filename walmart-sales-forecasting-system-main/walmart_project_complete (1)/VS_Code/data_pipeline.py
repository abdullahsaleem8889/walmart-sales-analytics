

import os, sys, time, logging
import pandas as pd
import numpy as np
import pyodbc
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline_log.txt", encoding="utf-8"),
    ],
)
log = logging.getLogger("ETL")

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

SQL_SERVER   = "(localdb)\\mssqllocaldb"                      
SQL_DATABASE = "WalmartSalesForecast"

BATCH_SIZE = 2000

def progress(current, total, label=""):
    pct  = int(current / total * 40)
    bar  = "#" * pct + "-" * (40 - pct)
    done = int(current / total * 100)
    print(f"\r  [{bar}] {done:3d}%  {current:,}/{total:,}  {label}   ", end="", flush=True)

def get_conn():
    """SQL Server se connect karo (Windows Auth)."""
    drivers = [
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 18 for SQL Server",
        "SQL Server",
    ]
    last_err = None
    for drv in drivers:
        try:
            conn = pyodbc.connect(
                f"Driver={{{drv}}};"
                f"Server={SQL_SERVER};"
                f"Database={SQL_DATABASE};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;",
                timeout=15,
            )
            log.info(f"[OK] Connected → {SQL_SERVER}/{SQL_DATABASE}  (driver: {drv})")
            return conn
        except Exception as e:
            last_err = e
    log.error(f"[FAIL] SQL connection error: {last_err}")
    log.error("  TIP: SSMS mein pehle walmart_final_no_errors.sql chalao!")
    raise last_err

def extract() -> dict:
    log.info("=" * 60)
    log.info("  STEP 1 — EXTRACT  (CSV files padhna)")
    log.info("=" * 60)

    base = Path(DATA_PATH)
    files = {
        "stores":   "stores.csv",
        "features": "features.csv",
        "train":    "train.csv",
        "test":     "test.csv",
    }

    data = {}
    for name, fname in files.items():
        path = base / fname
        if not path.exists():
            log.warning(f"  [SKIP] {fname} nahi mila")
            continue
        df = pd.read_csv(path, low_memory=False)
        data[name] = df
        log.info(f"  [OK]   {fname:20s} → {len(df):>7,} rows × {df.shape[1]} cols")

    if not data:
        log.error("  [FAIL] Koi CSV nahi mila! DATA_PATH check karo.")
        sys.exit(1)

    return data

def transform(raw: dict) -> dict:
    log.info("")
    log.info("=" * 60)
    log.info("  STEP 2 — TRANSFORM  (Data clean karna)")
    log.info("=" * 60)

    cleaned = {}

    if "stores" in raw:
        df = raw["stores"].copy()
        df.columns = df.columns.str.strip()
        df["Store"] = pd.to_numeric(df["Store"], errors="coerce").astype("Int64")
        df["Size"]  = pd.to_numeric(df["Size"],  errors="coerce").astype("Int64")
        df["Type"]  = df["Type"].astype(str).str.strip().str.upper()
        df = df.dropna(subset=["Store"]).drop_duplicates(subset=["Store"])
        cleaned["stores"] = df
        log.info(f"  [OK]   stores     → {len(df)} rows (clean)")

    if "features" in raw:
        df = raw["features"].copy()
        df.columns = df.columns.str.strip()

        df["IsHoliday"] = df["IsHoliday"].map(
            {True:1, False:0, "TRUE":1, "FALSE":0,
             "True":1, "False":0, 1:1, 0:0}
        ).fillna(0).astype(int)

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Store", "Date"])

        for col in ["MarkDown1","MarkDown2","MarkDown3","MarkDown4","MarkDown5"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        for col in ["Temperature","Fuel_Price","CPI","Unemployment"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                df[col] = df[col].fillna(df[col].median())

        df["Store"] = df["Store"].astype(int)
        df = df.drop_duplicates(subset=["Store","Date"])
        cleaned["features"] = df
        log.info(f"  [OK]   features   → {len(df):,} rows (clean)")

    if "train" in raw:
        df = raw["train"].copy()
        df.columns = df.columns.str.strip()

        df["IsHoliday"] = df["IsHoliday"].map(
            {True:1, False:0, "TRUE":1, "FALSE":0,
             "True":1, "False":0, 1:1, 0:0}
        ).fillna(0).astype(int)

        df["Date"]         = pd.to_datetime(df["Date"], errors="coerce")
        df["Weekly_Sales"] = pd.to_numeric(df["Weekly_Sales"], errors="coerce")
        df["Store"]        = pd.to_numeric(df["Store"], errors="coerce")
        df["Dept"]         = pd.to_numeric(df["Dept"],  errors="coerce")

        neg = (df["Weekly_Sales"] < 0).sum()
        if neg:
            df["Weekly_Sales"] = df["Weekly_Sales"].clip(lower=0)
            log.info(f"  [FIX]  {neg:,} negative sales → clipped to 0")

        df = df.dropna(subset=["Store","Dept","Date","Weekly_Sales"])
        df["Store"] = df["Store"].astype(int)
        df["Dept"]  = df["Dept"].astype(int)
        cleaned["train"] = df
        log.info(f"  [OK]   train      → {len(df):,} rows (clean)")

    if "test" in raw:
        df = raw["test"].copy()
        df.columns = df.columns.str.strip()

        df["IsHoliday"] = df["IsHoliday"].map(
            {True:1, False:0, "TRUE":1, "FALSE":0,
             "True":1, "False":0, 1:1, 0:0}
        ).fillna(0).astype(int)

        df["Date"]  = pd.to_datetime(df["Date"], errors="coerce")
        df["Store"] = pd.to_numeric(df["Store"], errors="coerce")
        df["Dept"]  = pd.to_numeric(df["Dept"],  errors="coerce")
        df = df.dropna(subset=["Store","Dept","Date"])
        df["Store"] = df["Store"].astype(int)
        df["Dept"]  = df["Dept"].astype(int)
        cleaned["test"] = df
        log.info(f"  [OK]   test       → {len(df):,} rows (clean)")

    return cleaned

TABLE_CONFIG = {
    "stores": {
        "sql_table": "Stores",
        "cols":      ["Store","Type","Size"],
        "pk_check":  "SELECT COUNT(*) FROM Stores",
    },
    "features": {
        "sql_table": "Features",
        "cols":      ["Store","Date","Temperature","Fuel_Price",
                      "MarkDown1","MarkDown2","MarkDown3","MarkDown4","MarkDown5",
                      "CPI","Unemployment","IsHoliday"],
        "pk_check":  "SELECT COUNT(*) FROM Features",
    },
    "train": {
        "sql_table": "SalesTraining",
        "cols":      ["Store","Dept","Date","Weekly_Sales","IsHoliday"],
        "pk_check":  "SELECT COUNT(*) FROM SalesTraining",
    },
    "test": {
        "sql_table": "SalesTest",
        "cols":      ["Store","Dept","Date","IsHoliday"],
        "pk_check":  "SELECT COUNT(*) FROM SalesTest",
    },
}

def load(cleaned: dict, conn: pyodbc.Connection) -> dict:
    log.info("")
    log.info("=" * 60)
    log.info("  STEP 3 — LOAD  (SQL Server mein insert karna)")
    log.info("=" * 60)

    cursor = conn.cursor()
    cursor.fast_executemany = True                  
    stats  = {}

    load_order = ["stores", "features", "train", "test"]

    delete_order = ["SalesTest", "SalesTraining", "ModelPredictions", "Features", "Stores"]
    for del_table in delete_order:
        try:
            cursor.execute(f"DELETE FROM [{del_table}]")
            conn.commit()
            log.info(f"  [OK]   Old data deleted from {del_table}")
        except Exception as e:
            log.info(f"  [SKIP] Could not delete {del_table}: {e}")

    for key in load_order:
        if key not in cleaned:
            continue

        cfg        = TABLE_CONFIG[key]
        table      = cfg["sql_table"]
        cols       = [c for c in cfg["cols"] if c in cleaned[key].columns]
        df         = cleaned[key][cols].copy()
        total_rows = len(df)

        log.info(f"\n  -- {table} ({total_rows:,} rows) --")

        log_time = datetime.now()
        try:
            cursor.execute(
                "INSERT INTO PipelineLog (TableName, StartTime, Status) VALUES (?,?,?)",
                (table, log_time, "RUNNING")
            )
            conn.commit()
            log_id = cursor.execute(
                "SELECT MAX(LogID) FROM PipelineLog WHERE TableName=?", table
            ).fetchone()[0]
        except Exception:
            log_id = None

        col_sql  = ", ".join(f"[{c}]" for c in cols)
        ph       = ", ".join("?" for _ in cols)
        ins_sql  = f"INSERT INTO [{table}] ({col_sql}) VALUES ({ph})"

        rows_ok   = 0
        rows_fail = 0
        t_start   = time.time()

        batches = [df.iloc[i:i+BATCH_SIZE] for i in range(0, total_rows, BATCH_SIZE)]
        total_batches = len(batches)

        for b_idx, batch in enumerate(batches):

            rows = []
            for row in batch.itertuples(index=False, name=None):
                clean_row = tuple(
                    None if (v is None or (isinstance(v, float) and np.isnan(v)))
                    else (bool(v) if isinstance(v, (np.bool_,)) else
                          int(v)  if isinstance(v, (np.integer,)) else
                          float(v) if isinstance(v, (np.floating,)) else v)
                    for v in row
                )
                rows.append(clean_row)

            try:
                cursor.executemany(ins_sql, rows)
                conn.commit()
                rows_ok += len(rows)
            except Exception as e:

                conn.rollback()
                for r in rows:
                    try:
                        cursor.execute(ins_sql, r)
                        conn.commit()
                        rows_ok += 1
                    except Exception:
                        rows_fail += 1

            progress(b_idx + 1, total_batches, table)

        elapsed = time.time() - t_start
        print()                               

        if log_id:
            try:
                cursor.execute(
                    "UPDATE PipelineLog SET RowsInserted=?, RowsFailed=?, "
                    "EndTime=?, Status=? WHERE LogID=?",
                    (rows_ok, rows_fail, datetime.now(),
                     "SUCCESS" if rows_fail == 0 else "PARTIAL", log_id)
                )
                conn.commit()
            except Exception:
                pass

        actual = cursor.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]

        stats[table] = {
            "inserted": rows_ok,
            "failed":   rows_fail,
            "sql_count": actual,
            "seconds":  round(elapsed, 1),
        }

        status = "OK" if rows_fail == 0 else "WARN"
        log.info(
            f"  [{status}]   Inserted: {rows_ok:,}  |  Failed: {rows_fail}  |  "
            f"SQL count: {actual:,}  |  Time: {elapsed:.1f}s"
        )

    cursor.close()
    return stats

def main():
    print()
    print("=" * 60)
    print("  WALMART ETL PIPELINE — STARTING")
    print(f"  Data  : {DATA_PATH}")
    print(f"  Server: {SQL_SERVER}  DB: {SQL_DATABASE}")
    print("=" * 60)
    print()

    t0   = time.time()
    conn = None

    try:

        raw = extract()

        clean = transform(raw)

        log.info("")
        log.info("=" * 60)
        log.info("  STEP 2.5 — SQL SERVER CONNECTION")
        log.info("=" * 60)
        conn = get_conn()

        stats = load(clean, conn)

        total_sec = time.time() - t0
        print()
        print("=" * 60)
        print("  PIPELINE COMPLETE!")
        print("=" * 60)
        print(f"  {'Table':<20} {'Inserted':>10} {'SQL Count':>10} {'Time':>8}")
        print(f"  {'-'*20} {'-'*10} {'-'*10} {'-'*8}")
        for tbl, s in stats.items():
            match = "OK" if s["inserted"] == s["sql_count"] else "!!"
            print(
                f"  {tbl:<20} {s['inserted']:>10,} {s['sql_count']:>10,} "
                f"{s['seconds']:>7.1f}s  {match}"
            )
        print(f"  {'-'*52}")
        print(f"  Total time: {total_sec:.1f} seconds")
        print()
        print("  Ab SSMS mein check karo:")
        print("  SELECT COUNT(*) FROM SalesTraining  -- should be 421,570")
        print("  SELECT * FROM PipelineLog")
        print()
        print("  Flask app chalao:")
        print("  cd flask_app  ->  python app.py")
        print("=" * 60)
        print()

    except KeyboardInterrupt:
        print("\n\n  [STOPPED] User ne Ctrl+C se rokha.")
    except Exception as e:
        log.error(f"\n  [FAIL] Pipeline crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if conn:
            conn.close()
            log.info("  [OK]   SQL connection closed.")

if __name__ == "__main__":
    main()