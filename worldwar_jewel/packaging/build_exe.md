# Build executable (Windows)

Use PyInstaller to ship a single-folder build:

```bash
pyinstaller --onefile --name worldwar_jewel worldwar_jewel/app/main.py
```

If you need assets, add `--collect-all worldwar_jewel` and keep the `app/assets` folder beside the exe.
