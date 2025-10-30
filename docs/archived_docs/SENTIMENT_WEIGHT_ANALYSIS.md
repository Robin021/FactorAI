# Sentiment Weight Analysis & Recommendations

## Current Issue

Stock 688256 (寒武纪) shows a **divergence problem**:
- News Sentiment: **1.0** (extremely positive)
- Price Momentum: **-0.226** (down 2.26%)
- Volume: **-0.033** (weak)
- Final Score: **61.27** (Optimistic) ❌

This is a classic "sell the news" pattern being misclassified as optimistic.

## Root Cause

### 1. Default Weights (from sentiment_calculator.py)
```python
WEIGHTS = {
    'news': 0.25,           # 25%
    'money_flow': 0.25,     # 25%
    'volatility': 0.20,     # 20%
    'technical': 0.20,      # 20%
    'social': 0.10          # 10%
}
```

### 2. A-Share Components Actually Used
```python
components = {
    'news': 1.0,            # Weight: 0.25
    'technical': -0.226,    # Weight: 0.20
    'volume': -0.033,       # Weight: 0.00 ❌ NOT IN DEFAULT WEIGHTS
    'money_flow': 0.0,      # Weight: 0.25
    'volatility': -0.010,   # Weight: 0.20
    'margin': 0.0           # Weight: 0.00 ❌ NOT IN DEFAULT WEIGHTS
}
```

### 3. The Problem
- `volume` and `margin` have **NO weight** in the default config
- Only news (0.25), technical (0.20), money_flow (0.25), volatility (0.20) are counted
- Total weight used: 0.90 (not 1.0)
- News dominates because other components are zero or negative

## Calculation Breakdown

```
Weighted Sum = (1.0 × 0.25) + (-0.226 × 0.20) + (-0.033 × 0.0) + (0.0 × 0.25) + (-0.010 × 0.20) + (0.0 × 0.0)
             = 0.250 + (-0.045) + 0 + 0 + (-0.002) + 0
             = 0.203

Total Weight = 0.25 + 0.20 + 0.25 + 0.20 = 0.90

Raw Score = 0.203 / 0.90 = 0.2256
Normalized = (0.2256 + 1) × 50 = 61.28 ✓
```

## Recommended Solutions

### Solution 1: Add Volume & Margin to Default Weights (Recommended)
```python
WEIGHTS = {
    'news': 0.20,           # 20% (reduced from 25%)
    'money_flow': 0.20,     # 20% (reduced from 25%)
    'volatility': 0.15,     # 15% (reduced from 20%)
    'technical': 0.20,      # 20% (same)
    'volume': 0.15,         # 15% (NEW)
    'social': 0.05,         # 5% (reduced from 10%)
    'margin': 0.05          # 5% (NEW)
}
```

**Rationale:**
- Volume is critical for confirming price moves
- Margin trading shows institutional sentiment
- Reduces news weight to prevent over-influence
- Total = 100%

### Solution 2: Add Divergence Penalty
When news and price/volume disagree significantly, apply a penalty:

```python
def calculate_divergence_penalty(components: Dict[str, float]) -> float:
    """
    Detect news-price divergence and apply penalty
    
    Returns: penalty factor (0.0 to 1.0)
    """
    news = components.get('news', 0.0)
    technical = components.get('technical', 0.0)
    volume = components.get('volume', 0.0)
    
    # Check if news is positive but price/volume are negative
    if news > 0.5 and technical < -0.1 and volume < 0:
        # Strong divergence - this is a warning sign
        divergence_strength = abs(news - technical)
        penalty = min(0.3, divergence_strength * 0.3)  # Max 30% penalty
        return penalty
    
    # Check if news is negative but price/volume are positive
    if news < -0.5 and technical > 0.1 and volume > 0:
        divergence_strength = abs(news - technical)
        penalty = min(0.3, divergence_strength * 0.3)
        return penalty
    
    return 0.0  # No penalty
```

### Solution 3: Adjust Sentiment Level Thresholds
Current thresholds may be too lenient:

```python
# Current (too optimistic)
SENTIMENT_LEVELS = {
    'extreme_fear': (0, 20),
    'fear': (20, 40),
    'neutral': (40, 60),
    'greed': (60, 80),        # 61.27 falls here ❌
    'extreme_greed': (80, 100)
}

# Recommended (more conservative)
SENTIMENT_LEVELS = {
    'extreme_fear': (0, 15),
    'fear': (15, 35),
    'neutral': (35, 65),      # 61.27 would fall here ✓
    'greed': (65, 85),
    'extreme_greed': (85, 100)
}
```

## Implementation Priority

1. **High Priority**: Solution 1 (Add volume & margin weights)
   - Fixes the root cause
   - Simple configuration change
   - Immediate impact

2. **Medium Priority**: Solution 2 (Divergence detection)
   - Adds intelligence to the system
   - Catches "sell the news" patterns
   - More complex to implement

3. **Low Priority**: Solution 3 (Threshold adjustment)
   - Fine-tuning after other fixes
   - Requires backtesting
   - Subjective

## Expected Result After Fix

With Solution 1 applied:
```
Weighted Sum = (1.0 × 0.20) + (-0.226 × 0.20) + (-0.033 × 0.15) + (0.0 × 0.20) + (-0.010 × 0.15) + (0.0 × 0.05)
             = 0.200 + (-0.045) + (-0.005) + 0 + (-0.0015) + 0
             = 0.1485

Total Weight = 1.00

Raw Score = 0.1485 / 1.00 = 0.1485
Normalized = (0.1485 + 1) × 50 = 57.43
Level = NEUTRAL ✓
```

This is more accurate - the stock should be neutral/cautious, not optimistic.
