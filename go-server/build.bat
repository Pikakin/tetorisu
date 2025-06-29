@echo off
echo テトリス Goサーバーをビルドします...
go mod tidy
go build -o tetorisu-server.exe main.go
echo ビルド完了: tetorisu-server.exe
pause
