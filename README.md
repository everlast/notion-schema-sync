# Notion Database Schema Sync Tool

A Python tool to compare and synchronize database schemas between Notion environments (production/test).

## Features

- Compare database schemas between two Notion environments
- Show differences with color highlighting in terminal
- Detailed Formula property comparison
- Selective synchronization after difference confirmation
- Easy command-line interface
- Configurable display verbosity with simple/detailed modes

## Installation

1. Clone this repository:
```bash
git clone https://github.com/everlast/notion-schema-sync.git
cd notion-schema-sync
```

2. Install required dependencies:
```bash
pip install colorama requests python-dotenv
```

3. Create a `.env` file with your Notion API credentials:
```
NOTION_API_TOKEN_PROD=your_production_integration_token
NOTION_API_TOKEN_TEST=your_test_integration_token
PROD_DB_ID=your_production_database_id
TEST_DB_ID=your_test_database_id
```

## Usage

### Compare database schemas without syncing

```bash
python notion_sync.py --diff-only
```

### Compare and optionally sync schemas

```bash
python notion_sync.py --sync
```

### Display Options

By default, the tool shows detailed information about formulas and other property settings. You can control the verbosity with these options:

```bash
# Simple mode (hides formula expressions and detailed property settings)
python notion_sync.py --diff-only --simple

# Detailed mode (explicitly show all details - this is the default)
python notion_sync.py --diff-only --detail
```

You can combine these display options with any other command:

```bash
python notion_sync.py --sync --simple
```

## Color Coding

The tool uses color coding to make differences easier to spot:
- 🔴 Red: Properties present in production but missing in test
- 🔵 Blue: Properties present in test but missing in production
- 🟡 Yellow: Properties with different configurations between environments

## Requirements

- Python 3.6+
- Notion API Integration tokens with read/write access to your databases
- Database IDs for both environments
