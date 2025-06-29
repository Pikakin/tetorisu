@echo off
echo テトリス UDP Goサーバーを起動します...
go mod tidy
go run udp-server.go
pause
