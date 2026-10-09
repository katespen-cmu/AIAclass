# TaskFlow

A small task-management demo app used for the AIA class lab.

## Structure
- `models.py` - User, Task, Project data classes
- `database.py` - toy in-memory database layer
- `utils.py` - sorting/filtering helpers
- `config/settings.py` - loads DB settings from environment 
- `main.py` - runnable demo
- `tests/` - unit tests

## Usage
    python3 main.py
    python3 tests/test_models.py
