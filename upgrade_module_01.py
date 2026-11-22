import os
from PIL import Image, ImageDraw, ImageFont

base_dir = r"C:\Users\Aniket\OneDrive\Desktop\github\system-design-illustrated"
mod_dir = os.path.join(base_dir, "01-client-server-networking")
assets_dir = os.path.join(mod_dir, "assets")
os.makedirs(assets_dir, exist_ok=True)

# -------------------------------------------------------------
# 1. Generate Ultra-Crisp High-Res Animation (960 x 440)
# -------------------------------------------------------------
def generate_hd_tcp_handshake():
    out_path = os.path.join(assets_dir, "tcp_handshake.gif")
    w, h = 960, 440
    frames = []
    total_frames = 50

    try:
        font_title = ImageFont.truetype("segoeuib.ttf", 20)
        font_header = ImageFont.truetype("segoeuib.ttf", 16)
        font_node = ImageFont.truetype("segoeuib.ttf", 15)
        font_code = ImageFont.truetype("consola.ttf", 14)
        font_sub = ImageFont.truetype("segoeui.ttf", 13)
        font_badge = ImageFont.truetype("segoeuib.ttf", 12)
    except Exception:
        font_title = ImageFont.load_default()
        font_header = font_title
        font_node = font_title
        font_code = font_title
        font_sub = font_title
        font_badge = font_title

    client_box = (60, 110, 240, 310)
    server_box = (720, 110, 900, 310)

    for f in range(total_frames):
        img = Image.new("RGB", (w, h), color="#0d1117")
        draw = ImageDraw.Draw(img)

        # Title Header
        draw.text((35, 20), "TCP THREE-WAY HANDSHAKE & CONNECTION ESTABLISHMENT", font=font_title, fill="#f0f6fc")
        draw.text((35, 48), "How reliable connections are negotiated before any HTTP data can travel", font=font_sub, fill="#8b949e")

        # Top Step Timeline Indicators
        steps = [
            ("1. SYN (seq=x)", f < 14, "#58a6ff"),
            ("2. SYN-ACK (seq=y, ack=x+1)", 14 <= f < 28, "#3fb950"),
            ("3. ACK (ack=y+1)", 28 <= f < 38, "#d29922"),
            ("4. HTTP/2 Data Stream", f >= 38, "#bc8cff")
        ]
        step_x = 35
        for text, is_active, col in steps:
            bg_col = "#21262d" if not is_active else "#161b22"
            border_col = col if is_active else "#30363d"
            text_col = "#ffffff" if is_active else "#8b949e"
            draw.rounded_rectangle((step_x, 75, step_x + 210, 102), radius=5, fill=bg_col, outline=border_col, width=2 if is_active else 1)
            draw.text((step_x + 12, 80), text, font=font_badge, fill=text_col)
            step_x += 225

        # Client Node Card
        c_state = "CLOSED"
        c_state_col = "#8b949e"
        if f < 14:
            c_state = "SYN-SENT"
            c_state_col = "#58a6ff"
        elif 14 <= f < 28:
            c_state = "SYN-SENT"
            c_state_col = "#58a6ff"
        else:
            c_state = "ESTABLISHED"
            c_state_col = "#3fb950"

        draw.rounded_rectangle(client_box, radius=8, fill="#161b22", outline="#58a6ff", width=2)
        draw.text((client_box[0] + 25, client_box[1] + 20), "📱 CLIENT", font=font_header, fill="#58a6ff")
        draw.text((client_box[0] + 25, client_box[1] + 45), "Browser / Mobile App", font=font_sub, fill="#8b949e")
        draw.text((client_box[0] + 25, client_box[1] + 75), "Port: 52140", font=font_code, fill="#c9d1d9")
        draw.line([(client_box[0] + 20, client_box[1] + 110), (client_box[2] - 20, client_box[1] + 110)], fill="#30363d", width=1)
        draw.text((client_box[0] + 25, client_box[1] + 125), "TCP Socket State:", font=font_sub, fill="#8b949e")
        draw.rounded_rectangle((client_box[0] + 25, client_box[1] + 148, client_box[2] - 25, client_box[1] + 178), radius=4, fill="#0d1117", outline=c_state_col, width=1)
        draw.text((client_box[0] + 40, client_box[1] + 154), c_state, font=font_node, fill=c_state_col)

        # Server Node Card
        s_state = "LISTEN"
        s_state_col = "#8b949e"
        if f < 14:
            s_state = "LISTEN"
            s_state_col = "#8b949e"
        elif 14 <= f < 28:
            s_state = "SYN-RECEIVED"
            s_state_col = "#d29922"
        else:
            s_state = "ESTABLISHED"
            s_state_col = "#3fb950"

        draw.rounded_rectangle(server_box, radius=8, fill="#161b22", outline="#3fb950", width=2)
        draw.text((server_box[0] + 25, server_box[1] + 20), "🖥️ SERVER", font=font_header, fill="#3fb950")
        draw.text((server_box[0] + 25, server_box[1] + 45), "Nginx / API Gateway", font=font_sub, fill="#8b949e")
        draw.text((server_box[0] + 25, server_box[1] + 75), "Port: 443 (HTTPS)", font=font_code, fill="#c9d1d9")
        draw.line([(server_box[0] + 20, server_box[1] + 110), (server_box[2] - 20, server_box[1] + 110)], fill="#30363d", width=1)
        draw.text((server_box[0] + 25, server_box[1] + 125), "TCP Socket State:", font=font_sub, fill="#8b949e")
        draw.rounded_rectangle((server_box[0] + 25, server_box[1] + 148, server_box[2] - 25, server_box[1] + 178), radius=4, fill="#0d1117", outline=s_state_col, width=1)
        draw.text((server_box[0] + 35, server_box[1] + 154), s_state, font=font_node, fill=s_state_col)

        # Wire Lines connecting them
        draw.line([(240, 160), (720, 160)], fill="#21262d", width=2)
        draw.line([(240, 210), (720, 210)], fill="#21262d", width=2)
        draw.line([(240, 260), (720, 260)], fill="#21262d", width=2)

        # Moving Packet Simulation
        if f < 14:
            # Step 1: SYN (Client -> Server)
            t = f / 13.0
            px = 240 + t * (720 - 240)
            py = 160
            packet_col = "#58a6ff"
            draw.ellipse([px-10, py-10, px+10, py+10], fill=packet_col, outline="#ffffff", width=2)
            draw.rounded_rectangle((px - 55, py - 38, px + 55, py - 14), radius=4, fill="#161b22", outline=packet_col)
            draw.text((px - 45, py - 34), "SYN (seq=100)", font=font_code, fill=packet_col)
            explanation = "CLIENT sends SYN packet with Initial Sequence Number (ISN = 100). Asks to open a connection."
            expl_col = "#58a6ff"

        elif 14 <= f < 28:
            # Step 2: SYN-ACK (Server -> Client)
            t = (f - 14) / 13.0
            px = 720 - t * (720 - 240)
            py = 210
            packet_col = "#3fb950"
            draw.ellipse([px-10, py-10, px+10, py+10], fill=packet_col, outline="#ffffff", width=2)
            draw.rounded_rectangle((px - 95, py - 38, px + 95, py - 14), radius=4, fill="#161b22", outline=packet_col)
            draw.text((px - 85, py - 34), "SYN-ACK (seq=300, ack=101)", font=font_code, fill=packet_col)
            explanation = "SERVER acknowledges client seq (ack=101) and sends its own ISN (seq=300) + allocates buffer memory."
            expl_col = "#3fb950"

        elif 28 <= f < 38:
            # Step 3: ACK (Client -> Server)
            t = (f - 28) / 9.0
            px = 240 + t * (720 - 240)
            py = 260
            packet_col = "#d29922"
            draw.ellipse([px-10, py-10, px+10, py+10], fill=packet_col, outline="#ffffff", width=2)
            draw.rounded_rectangle((px - 55, py - 38, px + 55, py - 14), radius=4, fill="#161b22", outline=packet_col)
            draw.text((px - 45, py - 34), "ACK (ack=301)", font=font_code, fill=packet_col)
            explanation = "CLIENT confirms server seq (ack=301). Connection is now fully ESTABLISHED on both sides!"
            expl_col = "#d29922"

        else:
            # Step 4: HTTP/2 Data Payload Exchange
            t = (f - 38) / 11.0
            px = 240 + t * (720 - 240)
            py = 210
            draw.ellipse([px-12, py-12, px+12, py+12], fill="#bc8cff", outline="#ffffff", width=2)
            draw.rounded_rectangle((px - 110, py - 40, px + 110, py - 14), radius=4, fill="#161b22", outline="#bc8cff")
            draw.text((px - 100, py - 36), "GET /api/feed (HTTP/2 Stream 1)", font=font_code, fill="#bc8cff")
            explanation = "FULL DUPLEX READY: Client streams encrypted HTTP/2 requests with multiplexing over this open socket."
            expl_col = "#bc8cff"

        # Bottom Narrative Banner
        draw.rounded_rectangle((35, 335, 925, 410), radius=6, fill="#161b22", outline="#30363d", width=1)
        draw.text((55, 348), "PROTOCOL MECHANICS & PACKET TRACE", font=font_badge, fill="#8b949e")
        draw.text((55, 372), f">> {explanation}", font=font_sub, fill=expl_col)

        frames.append(img)

    frames[0].save(out_path, save_all=True, append_images=frames[1:], optimize=True, duration=85, loop=0)
    print("Created ultra-crisp animation:", out_path)

generate_hd_tcp_handshake()
