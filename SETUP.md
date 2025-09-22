# Quick Setup Guide

## Option 1: Automated Installation (Recommended)

### Linux/macOS:
```bash
chmod +x install.sh
./install.sh
```

### Windows:
```cmd
install.bat
```

## Option 2: Manual Installation

1. **Create virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate.bat  # Windows
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the application**:
```bash
python app.py
# OR use the enhanced runner
python run.py --debug
```

## Running Options

### Development Mode (default):
```bash
python app.py
# OR
python run.py --debug
```

### Production Mode:
```bash
python run.py --production --host 0.0.0.0 --port 8080 --workers 4
```

### Custom Configuration:
```bash
python run.py --host 192.168.1.100 --port 5000 --debug
```

## Accessing the Application

Open your web browser and navigate to:
- Local development: http://127.0.0.1:8050
- Custom host/port: http://YOUR_HOST:YOUR_PORT

## Troubleshooting

1. **Python not found**: Install Python 3.8+
2. **Permission denied**: Run `chmod +x install.sh` first
3. **Port in use**: Use a different port with `--port XXXX`
4. **Dependencies fail**: Update pip with `pip install --upgrade pip`

## Next Steps

1. Read the full README.md for detailed usage instructions
2. Explore the three analysis modes: Strip, Circular, and Trapezoidal
3. Try the example calculations with default parameters
4. Export your results as CSV files
