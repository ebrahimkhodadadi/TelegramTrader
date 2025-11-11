# Signal Analyzer

The Signal Analyzer is responsible for parsing trading signals from Telegram messages using advanced regex patterns and text processing. It extracts key trading information including direction, symbol, prices, and risk management levels.

## Overview

The analyzer processes raw text messages and converts them into structured trading data that can be executed by the MetaTrader integration. It supports multiple message formats and languages (English and Persian/Farsi).

## Supported Signal Formats

### Basic Format
```
BUY EURUSD @ 1.0850
SL: 1.0800
TP: 1.0900, 1.0950
```

### Alternative Formats
```
SELL XAUUSD @ 1950.50
Stop Loss: 1945.00
Take Profit: 1960.00, 1970.00

BUY GBPUSD
Entry: 1.2650
SL: 1.2600
TP1: 1.2700
TP2: 1.2750
```

### Persian/Farsi Support
```
خرید یورو @ ۱.۰۸۵۰
حد ضرر: ۱.۰۸۰۰
تی پی: ۱.۰۹۰۰، ۱.۰۹۵۰
```

## Parsing Logic

### 1. Text Cleaning
- Normalizes Unicode characters (bold, italic formatting)
- Removes emojis and special symbols
- Standardizes whitespace
- Converts Persian numbers to English

### 2. Action Type Detection
Detects buy/sell signals using keyword matching:

**Buy keywords:** buy, خرید, بخر, بای
**Sell keywords:** sell, فروش, بفروش, selling

### 3. Symbol Extraction
Recognizes trading symbols through pattern matching:

- **Direct symbols:** EURUSD, XAUUSD, GBPUSD
- **Special mappings:**
  - Gold: طلا, GOLD, XAUUSD, اونس, گلد
  - EURUSD: یورو, EURUSD
  - US30/DJI: US30, داوجونز
  - NASDAQ: NASDAQ
  - OIL: OIL

### 4. Price Extraction

#### Entry Price
- Primary pattern: `@ 1.0850`
- Fallback patterns: `entry:`, `open:`, `price:`
- Supports decimal numbers and Persian numerals

#### Second Entry (High Risk Mode)
- Patterns: `1.0850 - 1.0860`, `1.0850///1.0860`
- Used when `HighRisk: true` in configuration

#### Take Profit Levels
Multiple patterns supported:
- `TP: 1.0900, 1.0950`
- `TP1: 1.0900, TP2: 1.0950`
- `Take Profit: 1.0900`
- Persian: `تی پی: ۱.۰۹۰۰`

#### Stop Loss
Common patterns:
- `SL: 1.0800`
- `Stop Loss: 1.0800`
- `حد ضرر: ۱.۰۸۰۰` (Persian)
- `استاپ: ۱.۰۸۰۰` (Persian)

## Advanced Features

### Price Validation
For certain symbols (XAUUSD, DJIUSD), prices are validated and adjusted to match broker's tick size and formatting requirements.

### Duplicate Prevention
The analyzer checks for existing positions with identical parameters to prevent duplicate trades.

### Flexible Formatting
Supports various message layouts:
- Single line: `BUY EURUSD @ 1.0850 SL 1.0800 TP 1.0900`
- Multi-line with labels
- Mixed English/Persian text
- Different separator formats (comma, space, newline)

## Configuration Impact

### Symbol Mappings
Custom symbol mappings in `settings.json` affect how symbols are resolved:
```json
"SymbolMappings": {
  "XAUUSD": "XAUUSDm",
  "EURUSD": "EURUSD!"
}
```

### High Risk Mode
When enabled, supports dual entry points for position averaging.

## Error Handling

The analyzer gracefully handles:
- Malformed messages (returns null)
- Missing required fields
- Invalid price formats
- Unsupported symbols

All parsing errors are logged for debugging purposes.

## Testing

Unit tests for the analyzer are available in `tests/AnalayzerTest.py`. Run with:
```bash
python -m unittest tests/AnalayzerTest.py
```

## Extending the Analyzer

To add support for new signal formats:
1. Add regex patterns to the respective functions in `app/Analayzer/Analayzer.py`
2. Update keyword lists for action types and symbols
3. Add unit tests for new patterns
4. Test with real message examples