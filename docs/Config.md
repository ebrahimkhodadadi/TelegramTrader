- Get chatid from @RawDataBot
- Sample

```
{
  "Telegram": {
    "api_id": 12345,
    "api_hash": "7f4c8eb4f3104d3",
    "channels": {
      "whiteList": [],
      "blackList": ["forexprogamer"]
    }
  },
  "Notification": {
    "token": "732575:AQlqpWtCl82EQ1Oyk",
    "chatId": 67468216
  },
  "MetaTrader": {
      "SaveProfits": [20, 30 ,20, 30], // in percentage
      "server": "CapitalxtendLLC-MU",
      "username": 101694,
      "password": "rnj6A!F8A",
      "lot": "2%", // if remove % it will be fixed number
      "expirePendinOrderInMinutes": 30, // optional
      "HighRisk": false, // if you have two entry point change it true
      "AccountSize": 1000, // optional: otherwise it use current account size
      "CloserPrice": 0.5, // optional: to entry closer to the current price
      "path": "C:/Users/Trade/Desktop/TelegramMetaTrader/terminal64.exe"
    },
    "Timer": { // optional: controll trade time
    "start": "08:00",
    "end": "18:00"
  }
}
```