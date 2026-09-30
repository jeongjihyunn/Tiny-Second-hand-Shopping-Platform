(function () {
  const container = document.getElementById("chat-app");
  const room = container.dataset.room;

  const socket = io();
  const log = document.getElementById("chat-log");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");

  socket.on("connect", () => socket.emit("join", { room }));

  socket.on("new_message", (msg) => {
    if (msg.room !== room) return;
    const div = document.createElement("div");
    div.className = "chat-msg";
    // textContent, never innerHTML, so incoming messages cannot inject markup/script (XSS).
    const who = document.createElement("span");
    who.className = "who";
    who.textContent = msg.sender_username;
    const body = document.createElement("span");
    body.textContent = msg.body;
    div.appendChild(who);
    div.appendChild(body);
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
  });

  socket.on("error", (e) => alert(e.message));

  form.addEventListener("submit", (ev) => {
    ev.preventDefault();
    if (!input.value.trim()) return;
    socket.emit("send_message", { room, body: input.value });
    input.value = "";
  });

  log.scrollTop = log.scrollHeight;
})();
