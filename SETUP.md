# Quick Setup Guide

## 1. Activate Virtual Environment

### Windows (PowerShell - Recommended):
```powershell
.\venv\Scripts\Activate.ps1
```

### Windows (Command Prompt):
```cmd
.\venv\Scripts\activate.bat
```

### If you get an execution policy error in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 2. Install Dependencies

After activating the virtual environment:
```bash
pip install -r requirements.txt
```

## 3. Configure OpenAI API Key

Edit the `.env` file and replace `your_openai_api_key_here` with your actual API key:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

## 4. Create Sample Database (Already done! ✅)

The database has been created with sample data.

## 5. Run the Chatbot

```bash
python main.py
```

## Verify Installation

You should see your command prompt change to show `(venv)` at the beginning, like this:
```
(venv) PS D:\Old laptop data\Python Haier\Python FIles\Project\ChatBot>
```

This means the virtual environment is active!
