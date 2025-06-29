@echo off
echo テトリス Goサーバーを起動します...
go mod tidy
go run main.go
pause
