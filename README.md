# TelegramTrader

TelegramTrader is an automated trading bot that monitors Telegram channels for trading signals, parses them using advanced regex patterns, and executes trades on MetaTrader 5 terminals. It supports risk management, position monitoring, and customizable trading strategies.

## Demo

![Demo](HowTo.gif)

## Features

### Core Functionality
- **Automated Signal Processing**: Listens to Telegram channels and automatically parses trading signals
- **Multi-Symbol Support**: Handles various trading instruments including forex, commodities, and indices
- **Risk Management**: Implements stop-loss, take-profit, and position sizing based on account balance
- **Dual Entry Points**: Optional high-risk mode with two entry levels for better averaging

### Trading Operations
- **Order Types**: Supports market, limit, and stop orders
- **Position Management**: Partial closures, profit saving strategies, and trailing stops
- **Symbol Validation**: Automatic symbol mapping for different broker conventions (e.g., XAUUSD vs xauusd!)
- **Time-Based Trading**: Optional trading hour restrictions

### Integration & Monitoring
- **MetaTrader 5 Integration**: Full API integration for order execution and position monitoring
- **Telegram Notifications**: Real-time notifications via Telegram bot
- **Comprehensive Logging**: Structured logging with timestamps and error tracking
- **Database Storage**: SQLite-based storage for signals and position tracking

### Advanced Features
- **Trailing Stop Loss**: Automatic adjustment of stop losses as profits increase
- **Profit Saving**: Configurable partial profit taking at multiple levels
- **Message Editing Support**: Handles signal updates and modifications
- **Channel Filtering**: Whitelist/blacklist system for channel management

## Installation

### Prerequisites
- Python 3.8+
- MetaTrader 5 terminal installed
- Telegram API credentials

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/ebrahimkhodadadi/TelegramTrader.git
   cd TelegramTrader
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure settings**
   - Create `settings.json` based on [Configuration Guide](docs/Config.md)
   - Set up your MetaTrader credentials and Telegram API keys

4. **Run the application**
   ```bash
   cd app
   python runner.py
   ```

### Alternative: Pre-built Release
1. Download the latest release from [GitHub Releases](https://github.com/ebrahimkhodadadi/TelegramTrader/releases)
2. Place `settings.json` alongside the executable
3. Run the executable

## Configuration

Create a `settings.json` file with your trading parameters. See [Configuration Guide](docs/Config.md) for detailed instructions.

Key settings include:
- MetaTrader server credentials and account details
- Telegram API keys and channel filters
- Risk management parameters (lot sizes, profit targets)
- Symbol mappings for your broker

## Usage

### Signal Format
The bot recognizes trading signals in various formats. Common patterns include:

```
BUY EURUSD @ 1.0850
SL: 1.0800
TP: 1.0900, 1.0950

SELL XAUUSD @ 1950.50
Stop Loss: 1945.00
Take Profit: 1960.00, 1970.00
```

### Supported Commands
- **Edit/Update**: Modify stop loss or take profit levels
- **Delete/Close**: Close positions
- **Half**: Close half of a position
- **Risk Free**: Move stop loss to entry price

### Monitoring
- Logs are saved daily in the `log/` directory
- Telegram notifications for important events
- Real-time position monitoring and trailing stops

## Testing

The project includes comprehensive unit and integration tests organized by component.

### Test Structure
- **Unit Tests**: Individual component testing with mocks
- **Integration Tests**: Component interaction testing
- **Fixtures**: Shared test data and utilities

### Running Tests

#### Run All Tests
```bash
# Using pytest (recommended)
pip install pytest
pytest tests/

# Using unittest
python -m unittest discover tests/
```

#### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific component
pytest tests/unit/analyzer/
```

#### Run with Coverage
```bash
pip install pytest-cov
pytest --cov=app --cov-report=html tests/
```

### Test Organization
```
tests/
├── fixtures/              # Test utilities and mock data
├── unit/                 # Unit tests by component
│   ├── analyzer/         # Signal parsing tests
│   ├── metatrader/       # Trading logic tests
│   ├── database/         # Data persistence tests
│   └── ...
├── integration/          # End-to-end component tests
└── utils/                # Test data generators
```

See [tests/README.md](tests/README.md) for detailed testing documentation.

## Documentation

Detailed documentation is available in the `docs/` folder:

- [Configuration Guide](docs/Config.md) - Complete settings reference
- [Analyzer Documentation](docs/Analayzer.md) - Signal parsing details
- [MetaTrader Integration](docs/MetaTrader.md) - MT5 API usage
- [Telegram Integration](docs/Telegram.md) - Telegram API setup
- [Release Guide](docs/Release.md) - Building executables

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

See [LICENSE](LICENSE) file for details.

## Disclaimer

This software is for educational and research purposes. Trading involves risk of loss. Use at your own risk and always test thoroughly before live trading.
