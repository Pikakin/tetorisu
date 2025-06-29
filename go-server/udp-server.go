package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"
)

// Message types (same as TCP version)
const (
	MessageConnect      = "connect"
	MessageDisconnect   = "disconnect"
	MessageHeartbeat    = "heartbeat"
	MessageCreateRoom   = "create_room"
	MessageJoinRoom     = "join_room"
	MessageLeaveRoom    = "leave_room"
	MessageListRooms    = "list_rooms"
	MessageRoomInfo     = "room_info"
	MessageGameStart    = "game_start"
	MessageGameState    = "game_state"
	MessagePlayerAction = "player_action"
	MessageGameOver     = "game_over"
	MessageChatMessage  = "chat_message"
	MessageError        = "error"
)

// Message structure
type Message struct {
	Type      string                 `json:"type"`
	Timestamp float64                `json:"timestamp"`
	Data      map[string]interface{} `json:"data"`
	PlayerID  string                 `json:"player_id,omitempty"`
	Sequence  uint32                 `json:"sequence,omitempty"`
}

// Player structure for UDP
type UDPPlayer struct {
	ID           string           `json:"id"`
	Name         string           `json:"name"`
	Addr         *net.UDPAddr     `json:"-"`
	RoomID       string           `json:"room_id"`
	Connected    bool             `json:"connected"`
	LastSeen     time.Time        `json:"-"`
	LastSequence uint32           `json:"-"`
	mu           sync.RWMutex     `json:"-"`
}

// Room structure (same as TCP)
type UDPRoom struct {
	ID          string                `json:"id"`
	Password    string                `json:"password,omitempty"`
	MaxPlayers  int                   `json:"max_players"`
	Players     map[string]*UDPPlayer `json:"players"`
	GameStarted bool                  `json:"game_started"`
	CreatedAt   time.Time             `json:"created_at"`
	mu          sync.RWMutex          `json:"-"`
}

// UDP Server structure
type UDPTetrisServer struct {
	Host string
	Port int
	conn *net.UDPConn
	
	players     map[string]*UDPPlayer      // PlayerID -> Player
	playersByAddr map[string]*UDPPlayer    // "IP:Port" -> Player
	rooms       map[string]*UDPRoom
	playerMutex sync.RWMutex
	roomMutex   sync.RWMutex
	
	running    bool
	quit       chan struct{}
	packetChan chan *UDPPacket
}

// UDP Packet structure
type UDPPacket struct {
	Data []byte
	Addr *net.UDPAddr
}

// NewUDPTetrisServer creates a new UDP server
func NewUDPTetrisServer(host string, port int) *UDPTetrisServer {
	return &UDPTetrisServer{
		Host:          host,
		Port:          port,
		players:       make(map[string]*UDPPlayer),
		playersByAddr: make(map[string]*UDPPlayer),
		rooms:         make(map[string]*UDPRoom),
		quit:          make(chan struct{}),
		packetChan:    make(chan *UDPPacket, 1000), // Buffer for high throughput
	}
}

// Start the UDP server
func (s *UDPTetrisServer) Start() error {
	addr, err := net.ResolveUDPAddr("udp", fmt.Sprintf("%s:%d", s.Host, s.Port))
	if err != nil {
		return fmt.Errorf("アドレス解決エラー: %v", err)
	}
	
	conn, err := net.ListenUDP("udp", addr)
	if err != nil {
		return fmt.Errorf("UDP リスナー開始エラー: %v", err)
	}
	
	s.conn = conn
	s.running = true
	
	fmt.Printf("テトリス UDPサーバーが %s で開始されました\n", addr)
	
	// Start background routines
	go s.packetReceiver()
	go s.packetProcessor()
	go s.heartbeatLoop()
	go s.cleanupLoop()
	
	return nil
}

// Stop the server
func (s *UDPTetrisServer) Stop() {
	fmt.Println("UDPサーバーを停止中...")
	s.running = false
	close(s.quit)
	
	if s.conn != nil {
		s.conn.Close()
	}
	
	fmt.Println("UDPサーバーが停止されました")
}

// Packet receiver goroutine
func (s *UDPTetrisServer) packetReceiver() {
	buffer := make([]byte, 4096) // 4KB buffer
	
	for s.running {
		n, addr, err := s.conn.ReadFromUDP(buffer)
		if err != nil {
			if s.running {
				log.Printf("UDP読み取りエラー: %v", err)
			}
			continue
		}
		
		// Copy data to avoid buffer reuse issues
		data := make([]byte, n)
		copy(data, buffer[:n])
		
		packet := &UDPPacket{
			Data: data,
			Addr: addr,
		}
		
		// Non-blocking send to packet channel
		select {
		case s.packetChan <- packet:
		default:
			log.Printf("パケットチャネルが満杯です (from %s)", addr)
		}
	}
}

// Packet processor goroutine
func (s *UDPTetrisServer) packetProcessor() {
	for {
		select {
		case packet := <-s.packetChan:
			s.handlePacket(packet)
		case <-s.quit:
			return
		}
	}
}

// Handle incoming packet
func (s *UDPTetrisServer) handlePacket(packet *UDPPacket) {
	log.Printf("パケット受信 from %s: %s", packet.Addr, string(packet.Data))
	
	var message Message
	if err := json.Unmarshal(packet.Data, &message); err != nil {
		log.Printf("JSON パースエラー from %s: %v", packet.Addr, err)
		log.Printf("受信データ: %s", string(packet.Data))
		return
	}
	
	log.Printf("メッセージ解析成功: Type=%s, PlayerID=%s", message.Type, message.PlayerID)
	
	// Get or create player
	player := s.getOrCreatePlayer(packet.Addr)
	player.LastSeen = time.Now()
	
	// Handle sequence numbers for ordering (optional)
	if message.Sequence != 0 && message.Sequence <= player.LastSequence {
		log.Printf("古いパケットを無視: Seq=%d, LastSeq=%d", message.Sequence, player.LastSequence)
		return
	}
	player.LastSequence = message.Sequence
	
	log.Printf("メッセージ処理開始: Type=%s from Player=%s", message.Type, player.ID)
	
	// Process message
	if err := s.processMessage(player, &message); err != nil {
		log.Printf("メッセージ処理エラー from %s: %v", packet.Addr, err)
	} else {
		log.Printf("メッセージ処理完了: Type=%s", message.Type)
	}
}

// Get or create player by address
func (s *UDPTetrisServer) getOrCreatePlayer(addr *net.UDPAddr) *UDPPlayer {
	addrStr := addr.String()
	
	s.playerMutex.Lock()
	defer s.playerMutex.Unlock()
	
	if player, exists := s.playersByAddr[addrStr]; exists {
		return player
	}
	
	// Create new player
	playerID := fmt.Sprintf("udp_player_%d_%d", len(s.players), time.Now().Unix())
	player := &UDPPlayer{
		ID:        playerID,
		Addr:      addr,
		Connected: true,
		LastSeen:  time.Now(),
	}
	
	s.players[playerID] = player
	s.playersByAddr[addrStr] = player
	
	fmt.Printf("新しいプレイヤー: %s (ID: %s)\n", addr, playerID)
	
	return player
}

// Send message to player
func (s *UDPTetrisServer) sendMessage(player *UDPPlayer, message *Message) error {
	if !player.Connected {
		log.Printf("送信失敗: プレイヤーが接続されていません (Player=%s)", player.ID)
		return fmt.Errorf("プレイヤーが接続されていません")
	}
	
	data, err := json.Marshal(message)
	if err != nil {
		log.Printf("メッセージ変換エラー: %v", err)
		return err
	}
	
	log.Printf("メッセージ送信: Type=%s to %s (%d bytes)", message.Type, player.Addr, len(data))
	
	if len(data) > 1400 { // Avoid UDP fragmentation
		log.Printf("警告: 大きなメッセージ (%d bytes) to %s", len(data), player.Addr)
	}
	
	_, err = s.conn.WriteToUDP(data, player.Addr)
	if err != nil {
		log.Printf("UDP送信エラー to %s: %v", player.Addr, err)
		player.Connected = false
		return err
	}
	
	log.Printf("メッセージ送信完了: Type=%s to %s", message.Type, player.Addr)
	return nil
}

// Process message (similar to TCP version)
func (s *UDPTetrisServer) processMessage(player *UDPPlayer, message *Message) error {
	switch message.Type {
	case MessageConnect:
		return s.handleConnect(player, message.Data)
	case MessageDisconnect:
		return s.handleDisconnect(player)
	case MessageCreateRoom:
		return s.handleCreateRoom(player, message.Data)
	case MessageJoinRoom:
		return s.handleJoinRoom(player, message.Data)
	case MessageLeaveRoom:
		return s.handleLeaveRoom(player)
	case MessageListRooms:
		return s.handleListRooms(player)
	case MessagePlayerAction:
		return s.handlePlayerAction(player, message.Data)
	case MessageGameState:
		return s.handleGameState(player, message.Data)
	case MessageChatMessage:
		return s.handleChatMessage(player, message.Data)
	case MessageHeartbeat:
		return nil // Already handled by updating LastSeen
	default:
		return s.sendError(player, "UNKNOWN_MESSAGE", fmt.Sprintf("不明なメッセージタイプ: %s", message.Type))
	}
}

// Handle connect (similar to TCP but simpler)
func (s *UDPTetrisServer) handleConnect(player *UDPPlayer, data map[string]interface{}) error {
	if name, ok := data["player_name"].(string); ok {
		player.Name = name
	}
	
	log.Printf("プレイヤー接続: %s (ID: %s, Addr: %s)", player.Name, player.ID, player.Addr)
	
	response := &Message{
		Type:      MessageConnect,
		Timestamp: float64(time.Now().UnixNano()) / 1e9,
		Data: map[string]interface{}{
			"success":   true,
			"player_id": player.ID,
			"server_info": map[string]interface{}{
				"name":     "Tetorisu UDP Server",
				"version":  "1.0.0",
				"protocol": "UDP",
			},
		},
	}
	
	return s.sendMessage(player, response)
}

// Handle disconnect
func (s *UDPTetrisServer) handleDisconnect(player *UDPPlayer) error {
	s.disconnectPlayer(player)
	return nil
}

// Handle create room
func (s *UDPTetrisServer) handleCreateRoom(player *UDPPlayer, data map[string]interface{}) error {
	log.Printf("ルーム作成リクエスト from Player=%s, Data=%+v", player.ID, data)
	
	roomID, ok := data["room_id"].(string)
	if !ok {
		log.Printf("無効なルームID: %+v", data)
		return s.sendError(player, "INVALID_ROOM_ID", "無効なルームID")
	}
	
	password, _ := data["password"].(string)
	
	s.roomMutex.Lock()
	if _, exists := s.rooms[roomID]; exists {
		s.roomMutex.Unlock()
		return s.sendError(player, "ROOM_EXISTS", "ルームが既に存在します")
	}
	
	room := &UDPRoom{
		ID:         roomID,
		Password:   password,
		MaxPlayers: 2,
		Players:    make(map[string]*UDPPlayer),
		CreatedAt:  time.Now(),
	}
	
	room.Players[player.ID] = player
	player.RoomID = roomID
	s.rooms[roomID] = room
	s.roomMutex.Unlock()
	
	log.Printf("ルーム作成成功: RoomID=%s, PlayerID=%s", roomID, player.ID)
	
	response := &Message{
		Type:      MessageCreateRoom,
		Timestamp: float64(time.Now().UnixNano()) / 1e9,
		Data: map[string]interface{}{
			"success": true,
			"room_id": roomID,
		},
	}
	
	log.Printf("ルーム作成レスポンス送信: %+v", response)
	return s.sendMessage(player, response)
}

// Handle join room
func (s *UDPTetrisServer) handleJoinRoom(player *UDPPlayer, data map[string]interface{}) error {
	roomID, ok := data["room_id"].(string)
	if !ok {
		return s.sendError(player, "INVALID_ROOM_ID", "無効なルームID")
	}
	
	password, _ := data["password"].(string)
	
	s.roomMutex.Lock()
	room, exists := s.rooms[roomID]
	if !exists {
		s.roomMutex.Unlock()
		return s.sendError(player, "ROOM_NOT_FOUND", "ルームが見つかりません")
	}
	
	if room.Password != "" && room.Password != password {
		s.roomMutex.Unlock()
		return s.sendError(player, "INVALID_PASSWORD", "パスワードが間違っています")
	}
	
	if len(room.Players) >= room.MaxPlayers {
		s.roomMutex.Unlock()
		return s.sendError(player, "ROOM_FULL", "ルームが満員です")
	}
	
	room.Players[player.ID] = player
	player.RoomID = roomID
	
	playerNames := make([]string, 0, len(room.Players))
	for _, p := range room.Players {
		playerNames = append(playerNames, p.Name)
	}
	s.roomMutex.Unlock()
	
	response := &Message{
		Type:      MessageJoinRoom,
		Timestamp: float64(time.Now().UnixNano()) / 1e9,
		Data: map[string]interface{}{
			"success": true,
			"room_id": roomID,
			"players": playerNames,
		},
	}
	
	if err := s.sendMessage(player, response); err != nil {
		return err
	}
	
	// Notify other players (fire and forget)
	go s.broadcastToRoom(roomID, &Message{
		Type:      MessageRoomInfo,
		Timestamp: float64(time.Now().UnixNano()) / 1e9,
		Data: map[string]interface{}{
			"event":       "player_joined",
			"player_name": player.Name,
			"players":     playerNames,
		},
	}, player.ID)
	
	return nil
}

// Handle leave room
func (s *UDPTetrisServer) handleLeaveRoom(player *UDPPlayer) error {
	if player.RoomID == "" {
		return nil
	}
	
	s.roomMutex.Lock()
	room, exists := s.rooms[player.RoomID]
	if exists {
		delete(room.Players, player.ID)
		
		playerNames := make([]string, 0, len(room.Players))
		for _, p := range room.Players {
			playerNames = append(playerNames, p.Name)
		}
		
		if len(room.Players) == 0 {
			delete(s.rooms, player.RoomID)
		} else {
			// Notify other players (fire and forget)
			go s.broadcastToRoom(player.RoomID, &Message{
				Type:      MessageRoomInfo,
				Timestamp: float64(time.Now().UnixNano()) / 1e9,
				Data: map[string]interface{}{
					"event":       "player_left",
					"player_name": player.Name,
					"players":     playerNames,
				},
			}, player.ID)
		}
	}
	s.roomMutex.Unlock()
	
	player.RoomID = ""
	
	response := &Message{
		Type:      MessageLeaveRoom,
		Timestamp: float64(time.Now().UnixNano()) / 1e9,
		Data: map[string]interface{}{
			"success": true,
		},
	}
	
	return s.sendMessage(player, response)
}

// Handle list rooms
func (s *UDPTetrisServer) handleListRooms(player *UDPPlayer) error {
	s.roomMutex.RLock()
	rooms := make([]map[string]interface{}, 0, len(s.rooms))
	
	for _, room := range s.rooms {
		playerNames := make([]string, 0, len(room.Players))
		for _, p := range room.Players {
			playerNames = append(playerNames, p.Name)
		}
		
		roomData := map[string]interface{}{
			"room_id":      room.ID,
			"name":         room.ID, // Use room ID as name for now
			"players":      playerNames,
			"max_players":  2,
			"has_password": room.Password != "",
		}
		rooms = append(rooms, roomData)
	}
	s.roomMutex.RUnlock()
	
	response := &Message{
		Type:      MessageListRooms,
		Timestamp: float64(time.Now().UnixNano()) / 1e9,
		Data: map[string]interface{}{
			"rooms": rooms,
		},
	}
	
	return s.sendMessage(player, response)
}

// Handle player action (high frequency, low latency)
func (s *UDPTetrisServer) handlePlayerAction(player *UDPPlayer, data map[string]interface{}) error {
	if player.RoomID == "" {
		return nil
	}
	
	// Fire and forget for low latency
	go s.broadcastToRoom(player.RoomID, &Message{
		Type:      MessagePlayerAction,
		Timestamp: float64(time.Now().UnixNano()) / 1e9,
		Data: map[string]interface{}{
			"player_id":   player.ID,
			"player_name": player.Name,
			"action":      data["action"],
		},
	}, player.ID)
	
	return nil
}

// Handle game state (high frequency)
func (s *UDPTetrisServer) handleGameState(player *UDPPlayer, data map[string]interface{}) error {
	if player.RoomID == "" {
		return nil
	}
	
	// Fire and forget for low latency
	go s.broadcastToRoom(player.RoomID, &Message{
		Type:      MessageGameState,
		Timestamp: float64(time.Now().UnixNano()) / 1e9,
		Data: map[string]interface{}{
			"player_id":   player.ID,
			"player_name": player.Name,
			"event":       data["event"],
			"grid":        data["grid"],
			"score":       data["score"],
			"level":       data["level"],
		},
	}, player.ID)
	
	return nil
}

// Handle chat message
func (s *UDPTetrisServer) handleChatMessage(player *UDPPlayer, data map[string]interface{}) error {
	if player.RoomID == "" {
		return nil
	}
	
	message := &Message{
		Type:      MessageChatMessage,
		Timestamp: float64(time.Now().UnixNano()) / 1e9,
		Data: map[string]interface{}{
			"player_id":   player.ID,
			"player_name": player.Name,
			"message":     data["message"],
		},
	}
	
	return s.broadcastToRoom(player.RoomID, message, "")
}

// Send error message
func (s *UDPTetrisServer) sendError(player *UDPPlayer, errorCode, errorMessage string) error {
	message := &Message{
		Type:      MessageError,
		Timestamp: float64(time.Now().UnixNano()) / 1e9,
		Data: map[string]interface{}{
			"error_code":    errorCode,
			"error_message": errorMessage,
		},
	}
	
	return s.sendMessage(player, message)
}

// Broadcast to room (UDP fire and forget)
func (s *UDPTetrisServer) broadcastToRoom(roomID string, message *Message, excludePlayerID string) error {
	s.roomMutex.RLock()
	room, exists := s.rooms[roomID]
	if !exists {
		s.roomMutex.RUnlock()
		return nil
	}
	
	players := make([]*UDPPlayer, 0, len(room.Players))
	for _, player := range room.Players {
		if player.ID != excludePlayerID && player.Connected {
			players = append(players, player)
		}
	}
	s.roomMutex.RUnlock()
	
	// Send to all players concurrently for minimum latency
	for _, player := range players {
		go func(p *UDPPlayer) {
			if err := s.sendMessage(p, message); err != nil {
				log.Printf("ブロードキャスト送信エラー (Player %s): %v", p.ID, err)
			}
		}(player)
	}
	
	return nil
}

// Disconnect player
func (s *UDPTetrisServer) disconnectPlayer(player *UDPPlayer) {
	fmt.Printf("プレイヤー切断: %s (ID: %s)\n", player.Addr, player.ID)
	
	if player.RoomID != "" {
		s.handleLeaveRoom(player)
	}
	
	s.playerMutex.Lock()
	delete(s.players, player.ID)
	delete(s.playersByAddr, player.Addr.String())
	s.playerMutex.Unlock()
	
	player.Connected = false
}

// Heartbeat loop (for UDP connection tracking)
func (s *UDPTetrisServer) heartbeatLoop() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			now := time.Now()
			var disconnectedPlayers []*UDPPlayer
			
			s.playerMutex.RLock()
			for _, player := range s.players {
				if now.Sub(player.LastSeen) > 90*time.Second { // 90 second timeout for UDP
					disconnectedPlayers = append(disconnectedPlayers, player)
				}
			}
			s.playerMutex.RUnlock()
			
			for _, player := range disconnectedPlayers {
				s.disconnectPlayer(player)
			}
			
		case <-s.quit:
			return
		}
	}
}

// Cleanup loop
func (s *UDPTetrisServer) cleanupLoop() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			s.roomMutex.Lock()
			for roomID, room := range s.rooms {
				if len(room.Players) == 0 {
					delete(s.rooms, roomID)
					fmt.Printf("空のルームを削除: %s\n", roomID)
				}
			}
			s.roomMutex.Unlock()
			
		case <-s.quit:
			return
		}
	}
}

// Main function
func main() {
	host := "localhost"
	port := 12346 // Different port from TCP version
	
	if len(os.Args) > 1 {
		if _, err := fmt.Sscanf(os.Args[1], "%d", &port); err != nil {
			log.Fatalf("無効なポート番号: %s", os.Args[1])
		}
	}
	
	if len(os.Args) > 2 {
		host = os.Args[2]
	}
	
	server := NewUDPTetrisServer(host, port)
	
	// Handle graceful shutdown
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	
	go func() {
		<-c
		server.Stop()
		os.Exit(0)
	}()
	
	if err := server.Start(); err != nil {
		log.Fatalf("UDP サーバー開始エラー: %v", err)
	}
	
	// Keep the server running
	select {}
}
