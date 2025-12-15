import os
import gc
import pandas as pd
from tqdm import tqdm

# Paths
DATA_DIR = r"C:\Users\YUSUF\Desktop\Dataset\datasets-OHLCV-1m\snapshots\55c907e5653cfa6ebe6be7644d9f75d2c2589532\data"
OUTPUT_FILE = "graveyard_index.csv"

# Save partial results every N files
CHECKPOINT_EVERY = 25

# Consider a stock "dead" if last seen before this month
CUTOFF_DATE = "2024-06"


def save_checkpoint(lifecycle, path):
    """Persist current lifecycle snapshot to CSV."""
    rows = []
    for ticker, stats in lifecycle.items():
        status = "Alive" if stats[1] >= CUTOFF_DATE else "Dead/Delisted"
        rows.append(
            {
                "ticker": ticker,
                "birth_month": stats[0],
                "death_month": stats[1],
                "status": status,
                "all_time_high": stats[2],
                "all_time_low": stats[3],
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)


def build_graveyard_index():
    print("--- INITIATING GRAVEYARD SCAN ---")
    files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".parquet"))
    print(f"Scanning {len(files)} monthly files...")

    lifecycle = {}

    for i, filename in enumerate(tqdm(files, unit="file")):
        current_month = filename.replace("ohlcv_", "").replace(".parquet", "")
        file_path = os.path.join(DATA_DIR, filename)

        try:
            df = pd.read_parquet(file_path, columns=["ticker", "close"])
            monthly_stats = df.groupby("ticker")["close"].agg(["min", "max"])

            for ticker, stats in monthly_stats.iterrows():
                if ticker not in lifecycle:
                    lifecycle[ticker] = [current_month, current_month, stats["max"], stats["min"]]
                else:
                    lifecycle[ticker][1] = current_month
                    if stats["max"] > lifecycle[ticker][2]:
                        lifecycle[ticker][2] = stats["max"]
                    if stats["min"] < lifecycle[ticker][3]:
                        lifecycle[ticker][3] = stats["min"]

            del df, monthly_stats
            gc.collect()

        except Exception as e:
            print(f"Error reading {filename}: {e}")

        if (i + 1) % CHECKPOINT_EVERY == 0:
            save_checkpoint(lifecycle, OUTPUT_FILE + ".checkpoint")

    print("Compiling the Book of the Dead...")
    save_checkpoint(lifecycle, OUTPUT_FILE)

    df_index = pd.read_csv(OUTPUT_FILE)
    mask_dead = df_index["status"] == "Dead/Delisted"
    df_index.loc[mask_dead, "destruction_pct"] = (
        (df_index["all_time_high"] - df_index["all_time_low"]) / df_index["all_time_high"]
    )
    df_index.to_csv(OUTPUT_FILE, index=False)

    print("\n" + "=" * 40)
    print("GRAVEYARD CENSUS COMPLETE")
    print("=" * 40)
    print(f"Total Tickers Found:      {len(df_index):,}")
    print(f"Confirmed Living (2024+): {len(df_index[df_index['status']=='Alive']):,}")
    print(f"Confirmed Dead (Delisted):{len(df_index[mask_dead]):,}")
    print("-" * 40)
    print(f"Index saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_graveyard_index()
