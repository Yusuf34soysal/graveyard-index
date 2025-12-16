# Terminal Velocity Indicator

## Strategic Transformation: From Autopsy to Diagnosis

**Evolution**: The Graveyard Index has transformed from a descriptive "autopsy" tool into a predictive "Terminal Velocity Indicator" that generates alpha.

**Goal**: Predict Phase 2 (Death Spiral) entry within 30/60/90-day trading windows using minute-level microstructure features.

---

## Feature Engineering

### 1. Amihud Illiquidity Ratio (Intraday)
```python
def calc_amihud_illiquidity(df):
    # Modified Amihud for minute-level data
    # As death approaches, price impact spikes despite low volume
    df_clean = df[df['volume'] > 0].copy()
    df_clean['ret'] = df_clean['close'].pct_change().abs()
    df_clean['dollar_vol'] = df_clean['close'] * df_clean['volume']
    df_clean['illiq'] = df_clean['ret'] / df_clean['dollar_vol']
    return df_clean['illiq'].mean() * 1e6
```

### 2. Rogers-Satchell Volatility (Drift-Corrected)
```python
def calc_rogers_satchell_vol(df):
    # Drift-independent volatility for dying stocks
    # Superior to Parkinson for massive downward trends
    u = np.log(df['high'] / df['open'])
    d = np.log(df['low'] / df['open'])
    c = np.log(df['close'] / df['open'])
    rs_var = (u * (u - c)) + (d * (d - c))
    return np.sqrt(rs_var.mean())
```

### 3. Gap Shock Analysis
- Overnight gap magnitude normalized by ATR
- Dying companies gap down as liquidity evaporates

### 4. Order Flow Imbalance
- Sell pressure ratio using tick test proxy
- High sell pressure indicates institutional exit

---

## Phase 2 Detection

**Target Variable**: Binary indicator of Death Spiral entry

**Triggers**:
- 20-day MA crosses below 50-day MA
- Rogers-Satchell Volatility spikes >2 std dev above baseline

---

## Modeling Strategy

**Per consultation with Gemini AI**:

1. **Fixed Windows vs Time-to-Event**
   - Use probability of entry within fixed windows (30/60/90 days)
   - Trading utility: "85% probability of Death Spiral entry within 30 days"
   - More actionable than "42 days to death" predictions

2. **Hybrid Approach**
   - `lifelines` (Survival Analysis) for feature selection
   - `RandomForest`/`XGBoost` for signal generation on fixed windows
   - Class balancing for minority death events

3. **Training Target**
   - Predict Phase 2 entry, not delisting (happens too late)
   - 30/60/90-day probability thresholds

---

## Alpha Generation Mechanisms

### 1. Short-Side Alpha
- Identify shorting candidates before market prices in death
- Entry: High Terminal Velocity score
- Exit: Phase 2 confirmation or volatility spike

### 2. Risk Management
- Filter "value traps" (cheap but dying stocks)
- Avoid catching falling knives
- Portfolio risk screening

### 3. Informational Advantage
- Minute-data features → monthly predictions
- Classic informational edge for quants

---

## Why This Wins

| Feature | Why Quants Care |
|---------|----------------|
| **Descriptive** (Old) | Interesting history, but "so what?" |
| **Predictive** (New) | Actionable signals. Solves "Catching a Falling Knife" problem |
| **Granularity** | Minute-data features predicting weekly/monthly outcomes |

---

## Dataset

- **Size**: 84GB minute-level OHLCV
- **Coverage**: 49,315 delisted stocks (1992-2025)
- **Source**: Finnhub API
- **Validation**: 59% lost >50% value, median destruction 66.6%

---

## Implementation Status

✅ Feature engineering functions (Amihud, RS Vol, Gap, OFI)
✅ Phase 2 detection logic
✅ Strategic framework (Gemini consultation)
⏳ RandomForest baseline model
⏳ Survival analysis feature selection
⏳ Performance metrics & visualizations

---

## Academic Paper Strategy

**Hold off on full manuscript** until predictive modeling complete.

- **Tier 2 Paper**: "We categorized how stocks die"
- **Tier 1 Paper**: "We predict delisting with 75% accuracy 3 months ahead"
- **Tier 1+**: Fund whitepaper for alpha generation

---

## Code

See `terminal_velocity.py` for full implementation.

Colab notebook: [Link to Colab]

---

**Status**: TERMINAL VELOCITY INDICATOR OPERATIONAL
**Ready for**: Full dataset application and model training
