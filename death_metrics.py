import os
import gc
import pandas as pd
from tqdm import tqdm

# --- CONFIGURATION ---
DATA_DIR = r"C:\Users\YUSUF\Desktop\Dataset\datasets-OHLCV-1m\snapshots\55c907e5653cfa6ebe6be7644d9f75d2c2589532\data"
INDEX_FILE = "graveyard_index.csv"
OUTPUT_FILE = "death_metrics.csv"

# CRITERIA FOR "TRUE FAILURE"
MIN_DESTRUCTION = 0.80  # Must have lost 80% of value
TARGET_SAMPLE_SIZE = 1000  # How many to analyze


def run_extraction():
    print("--- PHASE 3: EXTRACTING THE TOP 1,000 LIQUID FAILURES ---")

    # 1. Load Index and Filter Candidates
    df_idx = pd.read_csv(INDEX_FILE)
    candidates = df_idx[
        (df_idx["status"] == "Dead/Delisted")
        & (df_idx.get("destruction_pct", 0) >= MIN_DESTRUCTION)
    ].copy()

    print(f"Total Dead: {len(df_idx)}")
    print(f"True Failures (>80% Drop): {len(candidates)}")
    if candidates.empty:
        print("No candidates meet the destruction threshold; exiting.")
        return

    # Add lifespan proxy for sorting
    candidates["death_dt"] = pd.to_datetime(candidates["death_month"])
    candidates["birth_dt"] = pd.to_datetime(candidates["birth_month"])
    candidates["lifespan_days"] = (candidates["death_dt"] - candidates["birth_dt"]).dt.days

    # Take top 5,000 longest-lived failures as the search pool
    search_pool = (
        candidates.sort_values("lifespan_days", ascending=False)
        .head(5000)["ticker"]
        .tolist()
    )
    print(f"Scanning top {len(search_pool)} candidates by lifespan to find volume leaders...")

    # Map tickers to death-month parquet file
    ticker_death_file = {}
    for t in search_pool:
        death_month = candidates.loc[candidates["ticker"] == t, "death_month"].values[0]
        ticker_death_file[t] = f"ohlcv_{death_month}.parquet"

    # Group tickers by file to minimize IO
    file_to_tickers = {}
    for t, fname in ticker_death_file.items():
        file_to_tickers.setdefault(fname, []).append(t)

    final_metrics = []

    # Iterate through relevant files
    for filename in tqdm(list(file_to_tickers.keys()), unit="file"):
        file_path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(file_path):
            continue

        target_tickers = file_to_tickers[filename]
        try:
            # Read only what we need to reduce memory/IO
            df = pd.read_parquet(file_path, columns=["ticker", "timestamp", "close", "volume"])

            for t in target_tickers:
                stock_data = df[df["ticker"] == t].sort_values("timestamp")
                if len(stock_data) < 60:
                    continue  # Skip illiquid traces

                # 1. Dollar Volume (final month)
                total_vol = stock_data["volume"].sum() * stock_data["close"].mean()

                # 2. Exodus Ratio (first vs last quarter of rows)
                quarter = max(len(stock_data) // 4, 1)
                early_vol = stock_data.iloc[:quarter]["volume"].mean()
                late_vol = stock_data.iloc[-quarter:]["volume"].mean()
                exodus_ratio = late_vol / (early_vol + 1)  # Avoid div/0

                # 3. Volatility (std of minute returns)
                returns = stock_data["close"].pct_change().dropna()
                volatility = returns.std()

                # 4. Final month drop
                peak = stock_data["close"].max()
                end = stock_data["close"].iloc[-1]
                final_drop = (peak - end) / peak if peak else 0

                final_metrics.append(
                    {
                        "ticker": t,
                        "dollar_volume": total_vol,
                        "exodus_ratio": exodus_ratio,
                        "volatility": volatility,
                        "final_drop_pct": final_drop,
                        "death_date": filename.replace("ohlcv_", "").replace(".parquet", ""),
                    }
                )

        except Exception as e:
            print(f"Error processing {filename}: {e}")

        del df
        gc.collect()

    if not final_metrics:
        print("No metrics produced; check inputs and thresholds.")
        return

    # 3. Select Top 1,000 Liquid Failures
    df_res = pd.DataFrame(final_metrics)
    df_final = df_res.sort_values("dollar_volume", ascending=False).head(TARGET_SAMPLE_SIZE)
    df_final.to_csv(OUTPUT_FILE, index=False)

    print("\n" + "=" * 40)
    print(f"EXTRACTION COMPLETE. Saved top {len(df_final)} tickers to {OUTPUT_FILE}")
    print("=" * 40)


if __name__ == "__main__":
    run_extraction()
