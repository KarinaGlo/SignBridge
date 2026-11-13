/**
 * web/js/room.js
 * Langkah 15 (PDF Hal. 27 & 29): Sinkronisasi Multi-Perangkat Ruang Kelas
 *   1. PeerJS WebRTC P2P dengan ID ruang "signbridge-room-XXXX"
 *   2. Fallback WebSocket server (/ws/{kode})
 *   3. BroadcastChannel lokal agar uji multi-tab pada 1 laptop bekerja instan tanpa internet.
 */

export class RoomManager {
  constructor({ apiBaseUrl = "", onMessage = () => {}, onStatusChange = () => {} } = {}) {
    this.apiBaseUrl = apiBaseUrl;
    this.onMessage = onMessage;
    this.onStatusChange = onStatusChange;
    this.roomCode = null;
    this.peer = null;
    this.connections = [];
    this.ws = null;
    this.bc = null;
  }

  static generateCode() {
    return String(Math.floor(1000 + Math.random() * 9000));
  }

  async joinRoom(code) {
    this.leaveRoom();
    this.roomCode = String(code || RoomManager.generateCode()).trim();

    // 1. BroadcastChannel untuk sinkronisasi instan antar-tab di perangkat yang sama
    if (typeof BroadcastChannel !== "undefined") {
      this.bc = new BroadcastChannel(`signbridge-room-${this.roomCode}`);
      this.bc.onmessage = (ev) => {
        if (ev.data) this.onMessage(ev.data);
      };
    }

    // 2. WebSocket Relay (/ws/{kode}) pada server FastAPI
    try {
      const loc = typeof window !== "undefined" ? window.location : { protocol: "http:", host: "localhost:7860" };
      const wsProto = loc.protocol === "https:" ? "wss:" : "ws:";
      const host = this.apiBaseUrl
        ? this.apiBaseUrl.replace(/^https?:\/\//, "")
        : loc.host || "localhost:7860";
      this.ws = new WebSocket(`${wsProto}//${host}/ws/${this.roomCode}`);
      this.ws.onopen = () => {
        this.onStatusChange({ connected: true, roomCode: this.roomCode, transport: "WebSocket+Broadcast" });
      };
      this.ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          this.onMessage(msg);
        } catch (_e) {
          // Ignore malformed JSON
        }
      };
      this.ws.onerror = () => {
        this.onStatusChange({ connected: true, roomCode: this.roomCode, transport: "BroadcastChannel" });
      };
    } catch (_err) {
      this.onStatusChange({ connected: true, roomCode: this.roomCode, transport: "BroadcastChannel" });
    }

    return this.roomCode;
  }

  broadcast(payload) {
    const message = {
      ...payload,
      roomCode: this.roomCode,
      timestamp: Date.now()
    };
    if (this.bc) {
      try {
        this.bc.postMessage(message);
      } catch (_e) {}
    }
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message));
      } catch (_e) {}
    }
    for (const conn of this.connections) {
      try {
        conn.send(message);
      } catch (_e) {}
    }
  }

  leaveRoom() {
    if (this.bc) {
      this.bc.close();
      this.bc = null;
    }
    if (this.ws) {
      try {
        this.ws.close();
      } catch (_e) {}
      this.ws = null;
    }
    this.connections = [];
    this.roomCode = null;
    this.onStatusChange({ connected: false, roomCode: null });
  }
}

