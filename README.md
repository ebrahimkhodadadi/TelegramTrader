## Demo
![Screenshot](HowTo.gif)

# Project Setup Guide

Follow these steps to set up and run the project.

## 1. Configure Environment Variables
- Select and configure your environment in the `.env` file.

## 2. Set Application Settings
- Update the configuration files located in the `config` folder. Ensure that all required settings are defined in the appropriate `.json` files.

## 3. Run the Application
```bash
cd app && python runner.py
```

## Requirements Installation
Before running the application, install the required dependencies:

```bash
# Install necessary Python packages
pip install python-configuration
pip install setuptools
pip install -r requirements.txt
```

---

# Running Tests

To run the unit tests, use the following command:

```bash
python -m unittest .\tests\AnalyzerTest.py
```

---

## Documentation

For more detailed information about the project, please refer to the documentation located in the `/docs` folder.
