package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"
)

// Message types
const (
	MessageConnect      = "connect"
	MessageDisconnect   = "disconnect"
	MessageHeartbeat    = "heartbeat"
	MessageCreateRoom   = "create_room"
	MessageJoinRoom     = "join_room"
	MessageLeaveRoom    = "leave_room"
	MessageRoomInfo     = "room_info"
	MessageGameStart    = "game_start"
	MessageGameState    = "game_state"
	MessagePlayerAction = "player_action"
	MessageGameOver     = "game_over"
	MessageChatMessage  = "chat_message"
	MessageError        = "error"
)

// Game actions
const (
	ActionMoveLeft   = "move_left"
	ActionMoveRight  = "move_right"
	ActionRotateCW   = "rotate_cw"
	ActionRotateCCW  = "rotate_ccw"
	ActionSoftDrop   = "soft_drop"
	ActionHardDrop   = "hard_drop"
	ActionHold       = "hold"
	ActionPlacePiece = "place_piece"
)

// Message structure
type Message struct {
	Type      string                 `json:"type"`
	Timestamp float64                `json:"timestamp"`
	Data      map[string]interface{} `json:"data"`
}

// Player structure
type Player struct {
	ID           string    `json:"id"`
	Name         string    `json:"name"`
	Conn         net.Conn  `json:"-"`
	RoomID       string    `json:"room_id"`
	Connected    bool      `json:"connected"`
	LastHeartbeat time.Time `json:"-"`
	mu           sync.RWMutex
}

// Room structure
type Room struct {
	ID          string             `json:"id"`
	Password    string             `json:"password,omitempty"`
	MaxPlayers  int                `json:"max_players"`
	Players     map[string]*Player `json:"players"`
	GameStarted bool               `json:"game_started"`
	CreatedAt   time.Time          `json:"created_at"`
	mu          sync.RWMutex
}

// Server structure
type TetrisServer struct {
	Host     string
	Port     int
	listener net.Listener
	
	players     map[string]*Player
	rooms       map[string]*Room
	playerMutex sync.RWMutex
	roomMutex   sync.RWMutex
	
	running bool
	quit    chan struct{}
}

// NewTetrisServer creates a new server instance
func NewTetrisServer(host string, port int) *TetrisServer {
	return &TetrisServer{
		Host:    host,
		Port:    port,
		players: make(map[string]*Player),
		rooms:   make(map[string]*Room),
		quit:    make(chan struct{}),
	}
}

// Start starts the server
func (s *TetrisServer) Start() error {
	addr := fmt.Sprintf("%s:%d", s.Host, s.Port)
	listener, err := net.Listen("tcp", addr)
	if err != nil {
		return fmt.Errorf("failed to listen on %s: %v", addr, err)
	}
	
	s.listener = listener
	s.running = true
	
	fmt.Printf("テトリスサーバーが %s で開始されました\n", addr)
	
	// Start background routines
	go s.heartbeatLoop()
	go s.cleanupLoop()
	
	// Accept connections
	go func() {
		for s.running {
			conn, err := listener.Accept()
			if err != nil {
				if s.running {
					log.Printf("接続受付エラー: %v", err)
				}
				continue
			}
			
			go s.handleClient(conn)
		}
	}()
	
	return nil
}

// Stop stops the server
func (s *TetrisServer) Stop() {
	fmt.Println("サーバーを停止中...")
	s.running = false
	close(s.quit)
	
	if s.listener != nil {
		s.listener.Close()
	}
	
	// Disconnect all players
	s.playerMutex.Lock()
	for _, player := range s.players {
		player.Conn.Close()
	}
	s.playerMutex.Unlock()
	
	fmt.Println("サーバーが停止されました")
}

// Handle client connections
func (s *TetrisServer) handleClient(conn net.Conn) {
	defer conn.Close()
	
	playerID := fmt.Sprintf("player_%d_%d", len(s.players), time.Now().Unix())
	player := &Player{
		ID:            playerID,
		Conn:          conn,
		Connected:     true,
		LastHeartbeat: time.Now(),
	}
	
	s.playerMutex.Lock()
	s.players[playerID] = player
	s.playerMutex.Unlock()
	
	fmt.Printf("クライアント接続: %s (ID: %s)\n", conn.RemoteAddr(), playerID)
	
	defer func() {
		s.disconnectPlayer(player)
	}()
	
	// Message handling loop
	for s.running && player.Connected {
		message, err := s.readMessage(conn)
		if err != nil {
			if s.running && err != io.EOF {
				log.Printf("メッセージ読み取りエラー (Player %s): %v", playerID, err)
			}
			break
		}
		
		log.Printf("受信メッセージ (Player %s): Type=%s", playerID, message.Type)
		
		if err := s.processMessage(player, message); err != nil {
			log.Printf("メッセージ処理エラー (Player %s): %v", playerID, err)
		}
		
		player.LastHeartbeat = time.Now()
	}
}

// Read message from connection
func (s *TetrisServer) readMessage(conn net.Conn) (*Message, error) {
	// Read message length (4 bytes) - ensure full read
	lengthBytes := make([]byte, 4)
	if _, err := io.ReadFull(conn, lengthBytes); err != nil {
		return nil, err
	}
	
	// Parse message length (big endian)
	messageLength := int(lengthBytes[0])<<24 | int(lengthBytes[1])<<16 | int(lengthBytes[2])<<8 | int(lengthBytes[3])
	if messageLength <= 0 || messageLength > 1024*1024 { // 1MB limit
		return nil, fmt.Errorf("invalid message length: %d", messageLength)
	}
	
	// Read message body - ensure full read
	messageBytes := make([]byte, messageLength)
	if _, err := io.ReadFull(conn, messageBytes); err != nil {
		return nil, err
	}
	
	var message Message
	if err := json.Unmarshal(messageBytes, &message); err != nil {
		return nil, err
	}
	
	return &message, nil
}

// Send message to player
func (s *TetrisServer) sendMessage(player *Player, message *Message) error {
	if !player.Connected {
		return fmt.Errorf("player not connected")
	}
	
	messageBytes, err := json.Marshal(message)
	if err != nil {
		return err
	}
	
	messageLength := len(messageBytes)
	lengthBytes := []byte{
		byte(messageLength >> 24),
		byte(messageLength >> 16),
		byte(messageLength >> 8),
		byte(messageLength),
	}
	
	// Send length and message in one write to avoid fragmentation
	fullMessage := append(lengthBytes, messageBytes...)
	if _, err := player.Conn.Write(fullMessage); err != nil {
		player.Connected = false
		return err
	}
	
	return nil
}

// Process incoming message
func (s *TetrisServer) processMessage(player *Player, message *Message) error {
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
	case MessagePlayerAction:
		return s.handlePlayerAction(player, message.Data)
	case MessageGameState:
		return s.handleGameState(player, message.Data)
	case MessageChatMessage:
		return s.handleChatMessage(player, message.Data)
	case MessageHeartbeat:
		// Heartbeat is automatically handled by updating LastHeartbeat
		return nil
	default:
		return s.sendError(player, "UNKNOWN_MESSAGE", fmt.Sprintf("不明なメッセージタイプ: %s", message.Type))
	}
}

// Handle connect message
func (s *TetrisServer) handleConnect(player *Player, data map[string]interface{}) error {
	if name, ok := data["player_name"].(string); ok {
		player.Name = name
	}
	
	log.Printf("プレイヤー接続完了: %s (ID: %s)", player.Name, player.ID)
	
	response := &Message{
		Type:      MessageConnect,
		Timestamp: float64(time.Now().UnixNano()) / 1e9,
		Data: map[string]interface{}{
			"success":   true,
			"player_id": player.ID,
			"server_info": map[string]interface{}{
				"name":    "Tetorisu Go Server",
				"version": "1.0.0",
			},
		},
	}
	
	return s.sendMessage(player, response)
}

// Handle disconnect message
func (s *TetrisServer) handleDisconnect(player *Player) error {
	player.Connected = false
	return nil
}

// Handle create room message
func (s *TetrisServer) handleCreateRoom(player *Player, data map[string]interface{}) error {
	roomID, ok := data["room_id"].(string)
	if !ok {
		return s.sendError(player, "INVALID_ROOM_ID", "無効なルームID")
	}
	
	password, _ := data["password"].(string)
	
	s.roomMutex.Lock()
	if _, exists := s.rooms[roomID]; exists {
		s.roomMutex.Unlock()
		return s.sendError(player, "ROOM_EXISTS", "ルームが既に存在します")
	}
	
	room := &Room{
		ID:         roomID,
		Password:   password,
		MaxPlayers: 2,
		Players:    make(map[string]*Player),
		CreatedAt:  time.Now(),
	}
	
	room.Players[player.ID] = player
	player.RoomID = roomID
	s.rooms[roomID] = room
	s.roomMutex.Unlock()
	
	response := &Message{
		Type:      MessageCreateRoom,
		Timestamp: float64(time.Now().UnixNano()) / 1e9,
		Data: map[string]interface{}{
			"success": true,
			"room_id": roomID,
		},
	}
	
	return s.sendMessage(player, response)
}

// Handle join room message
func (s *TetrisServer) handleJoinRoom(player *Player, data map[string]interface{}) error {
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
	
	// Get player names
	playerNames := make([]string, 0, len(room.Players))
	for _, p := range room.Players {
		playerNames = append(playerNames, p.Name)
	}
	s.roomMutex.Unlock()
	
	// Send success response
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
	
	// Notify other players
	notification := &Message{
		Type:      MessageRoomInfo,
		Timestamp: float64(time.Now().UnixNano()) / 1e9,
		Data: map[string]interface{}{
			"event":       "player_joined",
			"player_name": player.Name,
			"players":     playerNames,
		},
	}
	
	return s.broadcastToRoom(roomID, notification, player.ID)
}

// Handle leave room message
func (s *TetrisServer) handleLeaveRoom(player *Player) error {
	if player.RoomID == "" {
		return nil
	}
	
	s.roomMutex.Lock()
	room, exists := s.rooms[player.RoomID]
	if exists {
		delete(room.Players, player.ID)
		
		// Get remaining player names
		playerNames := make([]string, 0, len(room.Players))
		for _, p := range room.Players {
			playerNames = append(playerNames, p.Name)
		}
		
		// Delete empty room
		if len(room.Players) == 0 {
			delete(s.rooms, player.RoomID)
		} else {
			// Notify other players
			notification := &Message{
				Type:      MessageRoomInfo,
				Timestamp: float64(time.Now().UnixNano()) / 1e9,
				Data: map[string]interface{}{
					"event":       "player_left",
					"player_name": player.Name,
					"players":     playerNames,
				},
			}
			
			go s.broadcastToRoom(player.RoomID, notification, player.ID)
		}
	}
	s.roomMutex.Unlock()
	
	player.RoomID = ""
	
	// Send success response only if player is still connected
	if player.Connected {
		response := &Message{
			Type:      MessageLeaveRoom,
			Timestamp: float64(time.Now().UnixNano()) / 1e9,
			Data: map[string]interface{}{
				"success": true,
			},
		}
		return s.sendMessage(player, response)
	}
	
	return nil
}

// Handle player action message
func (s *TetrisServer) handlePlayerAction(player *Player, data map[string]interface{}) error {
	if player.RoomID == "" {
		return nil
	}
	
	message := &Message{
		Type:      MessagePlayerAction,
		Timestamp: float64(time.Now().UnixNano()) / 1e9,
		Data: map[string]interface{}{
			"player_id":   player.ID,
			"player_name": player.Name,
		},
	}
	
	// Copy action data
	for k, v := range data {
		message.Data[k] = v
	}
	
	return s.broadcastToRoom(player.RoomID, message, player.ID)
}

// Handle game state message
func (s *TetrisServer) handleGameState(player *Player, data map[string]interface{}) error {
	if player.RoomID == "" {
		return nil
	}
	
	message := &Message{
		Type:      MessageGameState,
		Timestamp: float64(time.Now().UnixNano()) / 1e9,
		Data: map[string]interface{}{
			"player_id":   player.ID,
			"player_name": player.Name,
		},
	}
	
	// Copy game state data
	for k, v := range data {
		message.Data[k] = v
	}
	
	return s.broadcastToRoom(player.RoomID, message, player.ID)
}

// Handle chat message
func (s *TetrisServer) handleChatMessage(player *Player, data map[string]interface{}) error {
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
			"timestamp":   float64(time.Now().UnixNano()) / 1e9,
		},
	}
	
	return s.broadcastToRoom(player.RoomID, message, "")
}

// Send error message
func (s *TetrisServer) sendError(player *Player, errorCode, errorMessage string) error {
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

// Broadcast message to room
func (s *TetrisServer) broadcastToRoom(roomID string, message *Message, excludePlayerID string) error {
	s.roomMutex.RLock()
	room, exists := s.rooms[roomID]
	if !exists {
		s.roomMutex.RUnlock()
		return nil
	}
	
	players := make([]*Player, 0, len(room.Players))
	for _, player := range room.Players {
		if player.ID != excludePlayerID && player.Connected {
			players = append(players, player)
		}
	}
	s.roomMutex.RUnlock()
	
	for _, player := range players {
		if err := s.sendMessage(player, message); err != nil {
			log.Printf("ブロードキャスト送信エラー (Player %s): %v", player.ID, err)
		}
	}
	
	return nil
}

// Disconnect player
func (s *TetrisServer) disconnectPlayer(player *Player) {
	fmt.Printf("プレイヤー切断: %s (ID: %s)\n", player.Conn.RemoteAddr(), player.ID)
	
	// Leave room if in one
	if player.RoomID != "" {
		s.handleLeaveRoom(player)
	}
	
	// Remove from player list
	s.playerMutex.Lock()
	delete(s.players, player.ID)
	s.playerMutex.Unlock()
	
	player.Connected = false
	player.Conn.Close()
}

// Heartbeat loop
func (s *TetrisServer) heartbeatLoop() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			now := time.Now()
			var disconnectedPlayers []*Player
			
			s.playerMutex.RLock()
			for _, player := range s.players {
				if now.Sub(player.LastHeartbeat) > 60*time.Second {
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
func (s *TetrisServer) cleanupLoop() {
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
	port := 12345
	
	// Parse command line arguments
	if len(os.Args) > 1 {
		if _, err := fmt.Sscanf(os.Args[1], "%d", &port); err != nil {
			log.Fatalf("無効なポート番号: %s", os.Args[1])
		}
	}
	
	if len(os.Args) > 2 {
		host = os.Args[2]
	}
	
	server := NewTetrisServer(host, port)
	
	// Handle graceful shutdown
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	
	go func() {
		<-c
		server.Stop()
		os.Exit(0)
	}()
	
	if err := server.Start(); err != nil {
		log.Fatalf("サーバー開始エラー: %v", err)
	}
	
	// Keep the server running
	select {}
}
