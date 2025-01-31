$ pyinstaller .\TelegramTrader.spec

if .spec doesnt exist:
    $ pip install pyinstaller
    $ pyinstaller --onefile --console app/runner.py

dist/runner.exe

optional: 
    $ pyinstaller --onefile --console --name TelegramTrader --icon=icon.ico app/runner.py
