# Switch 2 Zelda stock check

Runs on GitHub Actions (scheduled every 5 minutes; each run checks 3 times, 3 minutes apart) and alerts Dre when the Nintendo Switch 2 The Legend of Zelda 40th Anniversary Edition looks purchasable on the Nintendo Store, or when the check keeps failing.

Alerts: a failed run (GitHub emails andrerfc1996@gmail.com) and Telegram once the `TELEGRAM_BOT_TOKEN` secret is added (Settings > Secrets and variables > Actions).

Manual test: Actions > Switch 2 Zelda stock check > Run workflow.
