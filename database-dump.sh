#!/bin/sh

sqlite3 ./telegram_bot.db .dump > ./database.sqlite.sql.txt