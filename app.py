# import streamlit as st
# import cv2
# import numpy as np
# import mediapipe as mp
# import time

# from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
# from mediapipe.tasks import python
# from mediapipe.tasks.python import vision


# async_processing=True

# # Load model
# base_options = python.BaseOptions(model_asset_path="pose_landmarker_lite.task")

# options = vision.PoseLandmarkerOptions(
#     base_options=base_options,
#     running_mode=vision.RunningMode.VIDEO
# )

# detector = vision.PoseLandmarker.create_from_options(options)


# class PostureDetector(VideoTransformerBase):
#     def transform(self, frame):
#         img = frame.to_ndarray(format="bgr24")

#         rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#         mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

#         timestamp = int(time.time() * 1000)
#         result = detector.detect_for_video(mp_image, timestamp)

#         if result.pose_landmarks:
#             landmarks = result.pose_landmarks[0]

#             h, w, _ = img.shape

#             left = landmarks[11]
#             right = landmarks[12]

#             if abs(left.y - right.y) > 0.1:
#                 posture = "Bad Posture"
#                 color = (0, 0, 255)
#             elif abs(left.y - right.y) > 0.075:
#                 posture = "Slightly Bend"
#                 color = (0, 255, 255)
#             else:
#                 posture = "Good Posture"
#                 color = (0, 255, 0)

#             for lm in landmarks:
#                 cx, cy = int(lm.x * w), int(lm.y * h)
#                 cv2.circle(img, (cx, cy), 5, color, -1)

#             cv2.putText(img, posture, (20, 40),
#                         cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

#         return img


# st.title("PostureSense")
# st.write("Real-time posture monitoring system")

# webrtc_streamer(
#     key="posture",
#     video_transformer_factory=PostureDetector
# )




# import streamlit as st
# import cv2
# import numpy as np
# import mediapipe as mp
# import time
# import json
# from collections import deque
# from datetime import datetime

# from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, RTCConfiguration
# from mediapipe.tasks import python
# from mediapipe.tasks.python import vision

# # ── Page config ───────────────────────────────────────────────────────────────
# st.set_page_config(
#     page_title="PostureSense",
#     page_icon="🧘",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# # ── Custom CSS ─────────────────────────────────────────────────────────────────
# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

# :root {
#     --good: #00e676;
#     --warn: #ffea00;
#     --bad:  #ff1744;
#     --bg:   #0d0f14;
#     --card: #161922;
#     --text: #e8eaf0;
#     --muted: #6b7280;
# }

# html, body, [data-testid="stAppViewContainer"] {
#     background-color: var(--bg) !important;
#     color: var(--text) !important;
#     font-family: 'DM Sans', sans-serif;
# }

# [data-testid="stSidebar"] {
#     background-color: #0a0c10 !important;
#     border-right: 1px solid #1e2230;
# }

# h1, h2, h3 { font-family: 'Space Mono', monospace; }

# .metric-card {
#     background: var(--card);
#     border: 1px solid #1e2230;
#     border-radius: 12px;
#     padding: 1.2rem 1.4rem;
#     text-align: center;
#     margin-bottom: 0.5rem;
# }
# .metric-card .label {
#     font-size: 0.72rem;
#     letter-spacing: 0.12em;
#     text-transform: uppercase;
#     color: var(--muted);
#     margin-bottom: 0.4rem;
# }
# .metric-card .value {
#     font-family: 'Space Mono', monospace;
#     font-size: 1.9rem;
#     font-weight: 700;
#     line-height: 1;
# }
# .metric-card .value.good  { color: var(--good); }
# .metric-card .value.warn  { color: var(--warn); }
# .metric-card .value.bad   { color: var(--bad);  }
# .metric-card .value.white { color: var(--text);  }

# .status-pill {
#     display: inline-block;
#     padding: 0.35rem 1rem;
#     border-radius: 999px;
#     font-family: 'Space Mono', monospace;
#     font-size: 0.82rem;
#     font-weight: 700;
#     letter-spacing: 0.05em;
#     margin-bottom: 0.8rem;
# }
# .pill-good { background: rgba(0,230,118,0.15); color: var(--good); border: 1px solid rgba(0,230,118,0.3); }
# .pill-warn { background: rgba(255,234,0,0.12);  color: var(--warn); border: 1px solid rgba(255,234,0,0.3); }
# .pill-bad  { background: rgba(255,23,68,0.15);  color: var(--bad);  border: 1px solid rgba(255,23,68,0.3); }

# .section-header {
#     font-family: 'Space Mono', monospace;
#     font-size: 0.7rem;
#     letter-spacing: 0.15em;
#     text-transform: uppercase;
#     color: var(--muted);
#     border-bottom: 1px solid #1e2230;
#     padding-bottom: 0.4rem;
#     margin: 1.2rem 0 0.8rem;
# }

# .tip-box {
#     background: linear-gradient(135deg, #161922 60%, #1a1f2e);
#     border-left: 3px solid var(--good);
#     border-radius: 0 8px 8px 0;
#     padding: 0.8rem 1rem;
#     font-size: 0.88rem;
#     color: #b0bcc8;
#     margin-bottom: 0.5rem;
# }

# .red-overlay {
#     position: fixed;
#     inset: 0;
#     background: rgba(255,23,68,0.18);
#     pointer-events: none;
#     z-index: 9999;
#     animation: pulse-red 1s ease-in-out infinite alternate;
# }
# @keyframes pulse-red {
#     from { background: rgba(255,23,68,0.10); }
#     to   { background: rgba(255,23,68,0.28); }
# }

# /* Hide Streamlit chrome */
# #MainMenu, footer, header { visibility: hidden; }
# [data-testid="stToolbar"] { display: none; }
# </style>
# """, unsafe_allow_html=True)

# # ── Session state init ─────────────────────────────────────────────────────────
# def _init():
#     defaults = {
#         "session_start": None,
#         "posture_log": [],           # list of (timestamp, label)
#         "last_alert_time": 0,
#         "current_posture": "Waiting…",
#         "total_good": 0,
#         "total_warn": 0,
#         "total_bad": 0,
#         "alert_count": 0,
#         "session_active": False,
#         "history": deque(maxlen=120), # last 120 readings (~2 min at 1 fps)
#     }
#     for k, v in defaults.items():
#         if k not in st.session_state:
#             st.session_state[k] = v

# _init()

# # ── Sidebar settings ───────────────────────────────────────────────────────────
# with st.sidebar:
#     st.markdown("## 🧘 PostureSense")
#     st.markdown("<div class='section-header'>Detection Settings</div>", unsafe_allow_html=True)
#     sensitivity = st.select_slider(
#         "Shoulder tilt sensitivity",
#         options=["Low", "Medium", "High"],
#         value="Medium",
#         help="Low = more tolerant, High = stricter"
#     )
#     THRESHOLDS = {"Low": (0.13, 0.10), "Medium": (0.10, 0.075), "High": (0.07, 0.05)}
#     BAD_THRESH, WARN_THRESH = THRESHOLDS[sensitivity]

#     st.markdown("<div class='section-header'>Alert Settings</div>", unsafe_allow_html=True)
#     voice_alerts = st.toggle("🔊 Voice alerts", value=True)
#     red_overlay  = st.toggle("🔴 Red screen flash", value=True)
#     alert_cooldown = st.slider("Alert cooldown (seconds)", 5, 60, 15)

#     st.markdown("<div class='section-header'>Posture Tips</div>", unsafe_allow_html=True)
#     tips = [
#         "Keep shoulders level and relaxed.",
#         "Ears should align over shoulders.",
#         "Sit with hips pushed back in chair.",
#         "Screen at eye level, arm's length away.",
#         "Take a break every 30 minutes.",
#     ]
#     for tip in tips:
#         st.markdown(f"<div class='tip-box'>💡 {tip}</div>", unsafe_allow_html=True)

# # ── Voice alert JS injection ───────────────────────────────────────────────────
# VOICE_JS = """
# <script>
# function speakAlert(msg) {
#     if (!window._psVoiceReady) {
#         window._psVoiceReady = true;
#         window.speechSynthesis.cancel();
#     }
#     var u = new SpeechSynthesisUtterance(msg);
#     u.rate = 0.95; u.pitch = 1; u.volume = 1;
#     window.speechSynthesis.speak(u);
# }
# window._lastAlertKey = "";
# function checkAndAlert(key, msg) {
#     if (key !== window._lastAlertKey) {
#         window._lastAlertKey = key;
#         speakAlert(msg);
#     }
# }
# </script>
# """
# st.markdown(VOICE_JS, unsafe_allow_html=True)

# # ── MediaPipe model ────────────────────────────────────────────────────────────
# @st.cache_resource
# def load_detector():
#     base_options = python.BaseOptions(model_asset_path="pose_landmarker_lite.task")
#     options = vision.PoseLandmarkerOptions(
#         base_options=base_options,
#         running_mode=vision.RunningMode.VIDEO,
#     )
#     return vision.PoseLandmarker.create_from_options(options)

# detector = load_detector()

# # ── Video transformer ──────────────────────────────────────────────────────────
# class PostureDetector(VideoTransformerBase):
#     def __init__(self):
#         self._frame_ts = 0

#     def transform(self, frame):
#         img = frame.to_ndarray(format="bgr24")
#         rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#         mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

#         self._frame_ts += 33  # ~30 fps synthetic timestamp
#         result = detector.detect_for_video(mp_image, self._frame_ts)

#         posture = "No Pose"
#         color   = (150, 150, 150)

#         if result.pose_landmarks:
#             landmarks = result.pose_landmarks[0]
#             h, w, _ = img.shape
#             left  = landmarks[11]
#             right = landmarks[12]
#             diff  = abs(left.y - right.y)

#             if diff > BAD_THRESH:
#                 posture, color = "Bad Posture",      (0, 0, 255)
#             elif diff > WARN_THRESH:
#                 posture, color = "Slightly Bent",    (0, 220, 255)
#             else:
#                 posture, color = "Good Posture",     (0, 220, 100)

#             # Draw landmarks
#             for lm in landmarks:
#                 cx, cy = int(lm.x * w), int(lm.y * h)
#                 cv2.circle(img, (cx, cy), 4, color, -1)

#             # Shoulder line
#             lx, ly = int(left.x * w),  int(left.y * h)
#             rx, ry = int(right.x * w), int(right.y * h)
#             cv2.line(img, (lx, ly), (rx, ry), color, 2)

#         # Posture label with background
#         label_bg_color = (0, 0, 180) if posture == "Bad Posture" else \
#                          (0, 160, 160) if posture == "Slightly Bent" else (0, 140, 60)
#         cv2.rectangle(img, (10, 10), (280, 55), label_bg_color, -1)
#         cv2.putText(img, posture, (18, 44),
#                     cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2, cv2.LINE_AA)

#         # Update shared session state (thread-safe via simple assignment)
#         now = time.time()
#         if st.session_state.session_active:
#             st.session_state.current_posture = posture
#             if posture == "Good Posture":
#                 st.session_state.total_good += 1
#             elif posture == "Slightly Bent":
#                 st.session_state.total_warn += 1
#             elif posture == "Bad Posture":
#                 st.session_state.total_bad  += 1

#             st.session_state.history.append(posture)

#             # Trigger alert if bad and cooldown passed
#             if posture == "Bad Posture":
#                 if now - st.session_state.last_alert_time > alert_cooldown:
#                     st.session_state.last_alert_time = now
#                     st.session_state.alert_count     += 1
#                     st.session_state.posture_log.append((now, posture))

#         return img

# # ── Layout ─────────────────────────────────────────────────────────────────────
# st.markdown("# 🧘 PostureSense")
# st.markdown("##### Real-time posture monitoring · sit tall, work better")

# col_cam, col_stats = st.columns([3, 2], gap="large")

# with col_cam:
#     # Session control
#     ctrl_col1, ctrl_col2 = st.columns(2)
#     with ctrl_col1:
#         if st.button("▶ Start Session", use_container_width=True, type="primary"):
#             st.session_state.session_active = True
#             st.session_state.session_start  = time.time()
#             st.session_state.total_good = 0
#             st.session_state.total_warn = 0
#             st.session_state.total_bad  = 0
#             st.session_state.alert_count = 0
#             st.session_state.posture_log = []
#             st.session_state.history     = deque(maxlen=120)
#             st.rerun()
#     with ctrl_col2:
#         if st.button("⏹ Stop Session", use_container_width=True):
#             st.session_state.session_active = False
#             st.rerun()

#     # Camera feed
#     webrtc_streamer(
#         key="posture",
#         video_transformer_factory=PostureDetector,
#         rtc_configuration=RTCConfiguration(
#             {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
#         ),
#         media_stream_constraints={"video": True, "audio": False},
#         async_processing=True,
#     )

#     # Red overlay injection
#     posture_now = st.session_state.current_posture
#     if red_overlay and posture_now == "Bad Posture" and st.session_state.session_active:
#         st.markdown("<div class='red-overlay'></div>", unsafe_allow_html=True)

#     # Voice alert injection
#     if voice_alerts and st.session_state.session_active:
#         alert_key = str(st.session_state.alert_count)
#         st.markdown(
#             f"<script>checkAndAlert('{alert_key}', 'Bad posture detected! Please sit up straight.');</script>",
#             unsafe_allow_html=True,
#         )

# with col_stats:
#     st.markdown("<div class='section-header'>Live Status</div>", unsafe_allow_html=True)

#     # Current posture pill
#     pill_class = {"Good Posture": "pill-good", "Slightly Bent": "pill-warn",
#                   "Bad Posture": "pill-bad"}.get(posture_now, "pill-warn")
#     st.markdown(f"<span class='status-pill {pill_class}'>{posture_now}</span>", unsafe_allow_html=True)

#     # Session timer
#     elapsed = ""
#     if st.session_state.session_start and st.session_state.session_active:
#         secs = int(time.time() - st.session_state.session_start)
#         elapsed = f"{secs // 60:02d}:{secs % 60:02d}"
#     elif st.session_state.session_start:
#         secs = int(time.time() - st.session_state.session_start)
#         elapsed = f"{secs // 60:02d}:{secs % 60:02d} (ended)"

#     m1, m2 = st.columns(2)
#     with m1:
#         st.markdown(f"""<div class='metric-card'>
#             <div class='label'>Session Time</div>
#             <div class='value white'>{elapsed or '--:--'}</div>
#         </div>""", unsafe_allow_html=True)
#     with m2:
#         st.markdown(f"""<div class='metric-card'>
#             <div class='label'>Alerts Sent</div>
#             <div class='value bad'>{st.session_state.alert_count}</div>
#         </div>""", unsafe_allow_html=True)

#     # Posture breakdown
#     total = st.session_state.total_good + st.session_state.total_warn + st.session_state.total_bad
#     good_pct = round(st.session_state.total_good / total * 100) if total else 0
#     warn_pct = round(st.session_state.total_warn / total * 100) if total else 0
#     bad_pct  = round(st.session_state.total_bad  / total * 100) if total else 0

#     st.markdown("<div class='section-header'>Posture Breakdown</div>", unsafe_allow_html=True)
#     g1, g2, g3 = st.columns(3)
#     with g1:
#         st.markdown(f"""<div class='metric-card'>
#             <div class='label'>Good</div>
#             <div class='value good'>{good_pct}%</div>
#         </div>""", unsafe_allow_html=True)
#     with g2:
#         st.markdown(f"""<div class='metric-card'>
#             <div class='label'>Slightly Bent</div>
#             <div class='value warn'>{warn_pct}%</div>
#         </div>""", unsafe_allow_html=True)
#     with g3:
#         st.markdown(f"""<div class='metric-card'>
#             <div class='label'>Bad</div>
#             <div class='value bad'>{bad_pct}%</div>
#         </div>""", unsafe_allow_html=True)

#     # Live history bar chart
#     st.markdown("<div class='section-header'>Posture Timeline (last 2 min)</div>", unsafe_allow_html=True)
#     if st.session_state.history:
#         history_list = list(st.session_state.history)
#         bar_vals = [
#             1 if p == "Good Posture" else 0.5 if p == "Slightly Bent" else 0
#             for p in history_list
#         ]
#         bar_colors = [
#             "#00e676" if p == "Good Posture" else "#ffea00" if p == "Slightly Bent" else "#ff1744"
#             for p in history_list
#         ]

#         # Build SVG bar chart
#         n   = len(bar_vals)
#         svw = 380
#         svh = 80
#         bw  = max(2, svw // max(n, 1) - 1)

#         bars = ""
#         for i, (v, c) in enumerate(zip(bar_vals, bar_colors)):
#             bh = int(v * svh)
#             x  = i * (svw // n)
#             y  = svh - bh
#             bars += f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" fill="{c}" rx="1"/>'

#         svg = f"""
#         <svg viewBox="0 0 {svw} {svh}" xmlns="http://www.w3.org/2000/svg"
#              style="width:100%;border-radius:8px;background:#161922;display:block;">
#           {bars}
#         </svg>"""
#         st.markdown(svg, unsafe_allow_html=True)
#         st.caption("🟢 Good  🟡 Slightly Bent  🔴 Bad")
#     else:
#         st.info("Start a session to see your posture history.")

#     # Session summary
#     if not st.session_state.session_active and st.session_state.session_start and total > 0:
#         st.markdown("<div class='section-header'>📋 Session Summary</div>", unsafe_allow_html=True)

#         duration_s = int(time.time() - st.session_state.session_start)
#         good_s = round(st.session_state.total_good / total * duration_s)
#         bad_s  = round(st.session_state.total_bad  / total * duration_s)

#         score = good_pct
#         grade = "🏆 Excellent" if score >= 80 else "👍 Good" if score >= 60 else "⚠️ Needs Work" if score >= 40 else "❌ Poor"

#         summary_lines = [
#             f"**Duration:** {duration_s // 60}m {duration_s % 60}s",
#             f"**Posture Score:** {score}/100 — {grade}",
#             f"**Good posture time:** ~{good_s // 60}m {good_s % 60}s ({good_pct}%)",
#             f"**Bad posture time:** ~{bad_s // 60}m {bad_s % 60}s ({bad_pct}%)",
#             f"**Alerts triggered:** {st.session_state.alert_count}",
#         ]
#         for line in summary_lines:
#             st.markdown(line)

#         # Advice
#         if score >= 80:
#             st.success("Great session! Keep up the excellent posture habits.")
#         elif score >= 60:
#             st.warning("Decent session. Try to be more mindful during longer work blocks.")
#         else:
#             st.error("Your posture needs attention. Consider ergonomic adjustments or more frequent breaks.")

# # ── Auto-refresh while session active ─────────────────────────────────────────
# if st.session_state.session_active:
#     time.sleep(1)
#     st.rerun()


# import streamlit as st
# import cv2
# import numpy as np
# import mediapipe as mp
# import time
# import threading
# from collections import deque

# from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, RTCConfiguration
# from mediapipe.tasks import python
# from mediapipe.tasks.python import vision

# # ── Page config ────────────────────────────────────────────────────────────────
# st.set_page_config(
#     page_title="PostureSense",
#     page_icon="🧘",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# # ── CSS ────────────────────────────────────────────────────────────────────────
# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

# :root {
#     --good: #00e676; --warn: #ffea00; --bad: #ff1744;
#     --bg: #0d0f14;   --card: #161922; --text: #e8eaf0; --muted: #6b7280;
# }
# html, body, [data-testid="stAppViewContainer"] {
#     background-color: var(--bg) !important;
#     color: var(--text) !important;
#     font-family: 'DM Sans', sans-serif;
# }
# [data-testid="stSidebar"] {
#     background-color: #0a0c10 !important;
#     border-right: 1px solid #1e2230;
# }
# h1, h2, h3 { font-family: 'Space Mono', monospace; }

# .metric-card {
#     background: var(--card); border: 1px solid #1e2230;
#     border-radius: 12px; padding: 1.2rem 1.4rem;
#     text-align: center; margin-bottom: 0.5rem;
# }
# .metric-card .label {
#     font-size: 0.72rem; letter-spacing: 0.12em;
#     text-transform: uppercase; color: var(--muted); margin-bottom: 0.4rem;
# }
# .metric-card .value {
#     font-family: 'Space Mono', monospace;
#     font-size: 1.9rem; font-weight: 700; line-height: 1;
# }
# .metric-card .value.good  { color: var(--good); }
# .metric-card .value.warn  { color: var(--warn); }
# .metric-card .value.bad   { color: var(--bad);  }
# .metric-card .value.white { color: var(--text); }

# .status-pill {
#     display: inline-block; padding: 0.35rem 1rem;
#     border-radius: 999px; font-family: 'Space Mono', monospace;
#     font-size: 0.82rem; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 0.8rem;
# }
# .pill-good { background: rgba(0,230,118,0.15); color: var(--good); border: 1px solid rgba(0,230,118,0.3); }
# .pill-warn { background: rgba(255,234,0,0.12);  color: var(--warn); border: 1px solid rgba(255,234,0,0.3); }
# .pill-bad  { background: rgba(255,23,68,0.15);  color: var(--bad);  border: 1px solid rgba(255,23,68,0.3); }
# .pill-idle { background: rgba(107,114,128,0.15); color: var(--muted); border: 1px solid rgba(107,114,128,0.3); }

# .section-header {
#     font-family: 'Space Mono', monospace; font-size: 0.7rem;
#     letter-spacing: 0.15em; text-transform: uppercase; color: var(--muted);
#     border-bottom: 1px solid #1e2230; padding-bottom: 0.4rem; margin: 1.2rem 0 0.8rem;
# }
# .tip-box {
#     background: linear-gradient(135deg, #161922 60%, #1a1f2e);
#     border-left: 3px solid var(--good); border-radius: 0 8px 8px 0;
#     padding: 0.8rem 1rem; font-size: 0.88rem; color: #b0bcc8; margin-bottom: 0.5rem;
# }
# .red-overlay {
#     position: fixed; inset: 0; background: rgba(255,23,68,0.18);
#     pointer-events: none; z-index: 9999;
#     animation: pulse-red 1s ease-in-out infinite alternate;
# }
# @keyframes pulse-red {
#     from { background: rgba(255,23,68,0.10); }
#     to   { background: rgba(255,23,68,0.28); }
# }
# #MainMenu, footer, header { visibility: hidden; }
# [data-testid="stToolbar"] { display: none; }
# </style>
# """, unsafe_allow_html=True)

# # ── Thread-safe shared state ───────────────────────────────────────────────────
# # The video transformer runs in a background thread.
# # Writing to st.session_state from there causes crashes/freezes.
# # Instead we use a plain dict protected by a threading.Lock().
# _shared = {
#     "posture": "Waiting…",
#     "lock": threading.Lock(),
# }

# # ── Session state init ─────────────────────────────────────────────────────────
# def _init():
#     defaults = {
#         "session_start": None,
#         "session_active": False,
#         "total_good": 0,
#         "total_warn": 0,
#         "total_bad": 0,
#         "alert_count": 0,
#         "last_alert_time": 0,
#         "posture_log": [],
#         "history": deque(maxlen=120),
#     }
#     for k, v in defaults.items():
#         if k not in st.session_state:
#             st.session_state[k] = v

# _init()

# # ── Sidebar ────────────────────────────────────────────────────────────────────
# with st.sidebar:
#     st.markdown("## 🧘 PostureSense")
#     st.markdown("<div class='section-header'>Detection Settings</div>", unsafe_allow_html=True)
#     sensitivity = st.select_slider(
#         "Shoulder tilt sensitivity",
#         options=["Low", "Medium", "High"], value="Medium",
#     )
#     THRESHOLDS = {"Low": (0.13, 0.10), "Medium": (0.10, 0.075), "High": (0.07, 0.05)}
#     BAD_THRESH, WARN_THRESH = THRESHOLDS[sensitivity]

#     st.markdown("<div class='section-header'>Alert Settings</div>", unsafe_allow_html=True)
#     voice_alerts   = st.toggle("🔊 Voice alerts", value=True)
#     red_overlay    = st.toggle("🔴 Red screen flash", value=True)
#     alert_cooldown = st.slider("Alert cooldown (seconds)", 5, 60, 15)

#     st.markdown("<div class='section-header'>Posture Tips</div>", unsafe_allow_html=True)
#     for tip in [
#         "Keep shoulders level and relaxed.",
#         "Ears should align over shoulders.",
#         "Sit with hips pushed back in chair.",
#         "Screen at eye level, arm's length away.",
#         "Take a break every 30 minutes.",
#     ]:
#         st.markdown(f"<div class='tip-box'>💡 {tip}</div>", unsafe_allow_html=True)

# # ── Voice alert JS ─────────────────────────────────────────────────────────────
# st.markdown("""
# <script>
# window._psLastAlertKey = "";
# function psCheckAlert(key, msg) {
#     if (key && key !== window._psLastAlertKey) {
#         window._psLastAlertKey = key;
#         window.speechSynthesis.cancel();
#         var u = new SpeechSynthesisUtterance(msg);
#         u.rate = 0.95; u.pitch = 1; u.volume = 1;
#         window.speechSynthesis.speak(u);
#     }
# }
# </script>
# """, unsafe_allow_html=True)

# # ── MediaPipe detector — IMAGE mode (no timestamp issues) ──────────────────────
# @st.cache_resource
# def load_detector():
#     base_options = python.BaseOptions(model_asset_path="pose_landmarker_lite.task")
#     options = vision.PoseLandmarkerOptions(
#         base_options=base_options,
#         running_mode=vision.RunningMode.IMAGE,  # ✅ KEY FIX: IMAGE mode, no timestamps
#     )
#     return vision.PoseLandmarker.create_from_options(options)

# detector = load_detector()

# # ── Video transformer ──────────────────────────────────────────────────────────
# class PostureDetector(VideoTransformerBase):
#     """
#     Runs in a background thread.
#     Only writes to _shared dict — never touches st.session_state.
#     """

#     def transform(self, frame):
#         img = frame.to_ndarray(format="bgr24")
#         rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#         mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

#         try:
#             result = detector.detect(mp_image)  # ✅ No timestamp argument needed
#         except Exception:
#             return img

#         posture = "No Pose"
#         color   = (120, 120, 120)

#         if result.pose_landmarks:
#             landmarks = result.pose_landmarks[0]
#             h, w, _   = img.shape
#             left       = landmarks[11]  # left shoulder
#             right      = landmarks[12]  # right shoulder
#             diff       = abs(left.y - right.y)

#             if diff > BAD_THRESH:
#                 posture, color = "Bad Posture",   (0, 0, 255)
#             elif diff > WARN_THRESH:
#                 posture, color = "Slightly Bent", (0, 200, 255)
#             else:
#                 posture, color = "Good Posture",  (0, 220, 100)

#             # Draw landmarks
#             for lm in landmarks:
#                 cx, cy = int(lm.x * w), int(lm.y * h)
#                 cv2.circle(img, (cx, cy), 4, color, -1)

#             # Shoulder connector line
#             lx, ly = int(left.x * w),  int(left.y * h)
#             rx, ry = int(right.x * w), int(right.y * h)
#             cv2.line(img, (lx, ly), (rx, ry), color, 2)

#         # Label overlay on video frame
#         bg = {"Bad Posture": (0,0,180), "Slightly Bent": (0,140,140),
#               "Good Posture": (0,120,50)}.get(posture, (60,60,60))
#         cv2.rectangle(img, (10, 10), (290, 58), bg, -1)
#         cv2.putText(img, posture, (18, 46),
#                     cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2, cv2.LINE_AA)

#         # ✅ Thread-safe write
#         with _shared["lock"]:
#             _shared["posture"] = posture

#         return img

# # ── Read posture (main thread) ─────────────────────────────────────────────────
# with _shared["lock"]:
#     posture_now = _shared["posture"]

# # ── Update session counters — only the main Streamlit thread touches session_state
# if st.session_state.session_active and posture_now not in ("Waiting…", "No Pose"):
#     if posture_now == "Good Posture":
#         st.session_state.total_good += 1
#     elif posture_now == "Slightly Bent":
#         st.session_state.total_warn += 1
#     elif posture_now == "Bad Posture":
#         st.session_state.total_bad += 1

#     st.session_state.history.append(posture_now)

#     now = time.time()
#     if posture_now == "Bad Posture":
#         if now - st.session_state.last_alert_time > alert_cooldown:
#             st.session_state.last_alert_time = now
#             st.session_state.alert_count += 1

# # ── Layout ─────────────────────────────────────────────────────────────────────
# st.markdown("# 🧘 PostureSense")
# st.markdown("##### Real-time posture monitoring · sit tall, work better")

# col_cam, col_stats = st.columns([3, 2], gap="large")

# with col_cam:
#     c1, c2 = st.columns(2)
#     with c1:
#         if st.button("▶ Start Session", use_container_width=True, type="primary"):
#             st.session_state.session_active  = True
#             st.session_state.session_start   = time.time()
#             st.session_state.total_good      = 0
#             st.session_state.total_warn      = 0
#             st.session_state.total_bad       = 0
#             st.session_state.alert_count     = 0
#             st.session_state.last_alert_time = 0
#             st.session_state.posture_log     = []
#             st.session_state.history         = deque(maxlen=120)
#             st.rerun()
#     with c2:
#         if st.button("⏹ Stop Session", use_container_width=True):
#             st.session_state.session_active = False
#             st.rerun()

#     webrtc_streamer(
#         key="posture",
#         video_transformer_factory=PostureDetector,
#         rtc_configuration=RTCConfiguration(
#             {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
#         ),
#         media_stream_constraints={"video": True, "audio": False},
#         async_processing=True,
#     )

#     # Red overlay
#     if red_overlay and posture_now == "Bad Posture" and st.session_state.session_active:
#         st.markdown("<div class='red-overlay'></div>", unsafe_allow_html=True)

#     # Voice alert trigger
#     if voice_alerts and st.session_state.session_active:
#         alert_key = str(st.session_state.alert_count) if st.session_state.alert_count > 0 else ""
#         st.markdown(
#             f"<script>psCheckAlert('{alert_key}', 'Bad posture detected! Please sit up straight.');</script>",
#             unsafe_allow_html=True,
#         )

# with col_stats:
#     st.markdown("<div class='section-header'>Live Status</div>", unsafe_allow_html=True)

#     pill_class = {
#         "Good Posture": "pill-good",
#         "Slightly Bent": "pill-warn",
#         "Bad Posture": "pill-bad",
#     }.get(posture_now, "pill-idle")
#     st.markdown(f"<span class='status-pill {pill_class}'>{posture_now}</span>", unsafe_allow_html=True)

#     elapsed = "--:--"
#     if st.session_state.session_start:
#         secs   = int(time.time() - st.session_state.session_start)
#         suffix = "" if st.session_state.session_active else " (ended)"
#         elapsed = f"{secs // 60:02d}:{secs % 60:02d}{suffix}"

#     m1, m2 = st.columns(2)
#     with m1:
#         st.markdown(f"""<div class='metric-card'>
#             <div class='label'>Session Time</div>
#             <div class='value white'>{elapsed}</div>
#         </div>""", unsafe_allow_html=True)
#     with m2:
#         st.markdown(f"""<div class='metric-card'>
#             <div class='label'>Alerts Sent</div>
#             <div class='value bad'>{st.session_state.alert_count}</div>
#         </div>""", unsafe_allow_html=True)

#     total    = st.session_state.total_good + st.session_state.total_warn + st.session_state.total_bad
#     good_pct = round(st.session_state.total_good / total * 100) if total else 0
#     warn_pct = round(st.session_state.total_warn / total * 100) if total else 0
#     bad_pct  = round(st.session_state.total_bad  / total * 100) if total else 0

#     st.markdown("<div class='section-header'>Posture Breakdown</div>", unsafe_allow_html=True)
#     g1, g2, g3 = st.columns(3)
#     for col, label, pct, cls in [
#         (g1, "Good",          good_pct, "good"),
#         (g2, "Slightly Bent", warn_pct, "warn"),
#         (g3, "Bad",           bad_pct,  "bad"),
#     ]:
#         with col:
#             st.markdown(f"""<div class='metric-card'>
#                 <div class='label'>{label}</div>
#                 <div class='value {cls}'>{pct}%</div>
#             </div>""", unsafe_allow_html=True)

#     # Posture timeline SVG chart
#     st.markdown("<div class='section-header'>Posture Timeline (last 2 min)</div>", unsafe_allow_html=True)
#     history_list = list(st.session_state.history)
#     if history_list:
#         n        = len(history_list)
#         svw, svh = 380, 80
#         bw       = max(2, svw // n - 1)
#         bars     = ""
#         for i, p in enumerate(history_list):
#             v = 1.0 if p == "Good Posture" else 0.5 if p == "Slightly Bent" else 0.15
#             c = "#00e676" if p == "Good Posture" else "#ffea00" if p == "Slightly Bent" else "#ff1744"
#             bh = int(v * svh)
#             x  = i * (svw // n)
#             bars += f'<rect x="{x}" y="{svh - bh}" width="{bw}" height="{bh}" fill="{c}" rx="1"/>'
#         st.markdown(f"""
#         <svg viewBox="0 0 {svw} {svh}" xmlns="http://www.w3.org/2000/svg"
#              style="width:100%;border-radius:8px;background:#161922;display:block;">{bars}</svg>
#         """, unsafe_allow_html=True)
#         st.caption("🟢 Good  🟡 Slightly Bent  🔴 Bad")
#     else:
#         st.info("Start a session to see your posture history.")

#     # Session summary (shown after session ends)
#     if not st.session_state.session_active and st.session_state.session_start and total > 0:
#         st.markdown("<div class='section-header'>📋 Session Summary</div>", unsafe_allow_html=True)
#         duration_s = int(time.time() - st.session_state.session_start)
#         good_s     = round(st.session_state.total_good / total * duration_s)
#         bad_s      = round(st.session_state.total_bad  / total * duration_s)
#         score      = good_pct
#         grade      = ("🏆 Excellent" if score >= 80 else "👍 Good" if score >= 60
#                       else "⚠️ Needs Work" if score >= 40 else "❌ Poor")

#         for line in [
#             f"**Duration:** {duration_s // 60}m {duration_s % 60}s",
#             f"**Posture Score:** {score}/100 — {grade}",
#             f"**Good posture time:** ~{good_s // 60}m {good_s % 60}s ({good_pct}%)",
#             f"**Bad posture time:** ~{bad_s // 60}m {bad_s % 60}s ({bad_pct}%)",
#             f"**Alerts triggered:** {st.session_state.alert_count}",
#         ]:
#             st.markdown(line)

#         if score >= 80:
#             st.success("Great session! Keep up the excellent posture habits.")
#         elif score >= 60:
#             st.warning("Decent session. Try to be more mindful during longer work blocks.")
#         else:
#             st.error("Your posture needs attention. Consider ergonomic adjustments or more frequent breaks.")

# # ── Auto-refresh while session active ─────────────────────────────────────────
# if st.session_state.session_active:
#     time.sleep(1)
#     st.rerun()

"""
PostureSense — Real-time posture monitoring
Fully compatible with Streamlit Community Cloud deployment.
"""

import streamlit as st
import cv2
import mediapipe as mp
import time
import threading
from collections import deque

from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG  (must be first Streamlit call)
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="PostureSense",
    page_icon="🧘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
:root{--good:#00e676;--warn:#ffea00;--bad:#ff1744;--bg:#0d0f14;--card:#161922;--text:#e8eaf0;--muted:#6b7280}
html,body,[data-testid="stAppViewContainer"]{background:var(--bg)!important;color:var(--text)!important;font-family:'DM Sans',sans-serif}
[data-testid="stSidebar"]{background:#0a0c10!important;border-right:1px solid #1e2230}
h1,h2,h3{font-family:'Space Mono',monospace}
.mc{background:var(--card);border:1px solid #1e2230;border-radius:12px;padding:1.1rem 1.2rem;text-align:center;margin-bottom:.5rem}
.mc .lbl{font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:.35rem}
.mc .val{font-family:'Space Mono',monospace;font-size:1.8rem;font-weight:700;line-height:1}
.val.good{color:var(--good)}.val.warn{color:var(--warn)}.val.bad{color:var(--bad)}.val.wht{color:var(--text)}
.pill{display:inline-block;padding:.35rem 1rem;border-radius:999px;font-family:'Space Mono',monospace;font-size:.82rem;font-weight:700;letter-spacing:.05em;margin-bottom:.8rem}
.pg{background:rgba(0,230,118,.15);color:var(--good);border:1px solid rgba(0,230,118,.3)}
.pw{background:rgba(255,234,0,.12);color:var(--warn);border:1px solid rgba(255,234,0,.3)}
.pb{background:rgba(255,23,68,.15);color:var(--bad);border:1px solid rgba(255,23,68,.3)}
.pi{background:rgba(107,114,128,.15);color:var(--muted);border:1px solid rgba(107,114,128,.3)}
.sh{font-family:'Space Mono',monospace;font-size:.68rem;letter-spacing:.15em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid #1e2230;padding-bottom:.35rem;margin:1.1rem 0 .7rem}
.tip{background:linear-gradient(135deg,#161922 60%,#1a1f2e);border-left:3px solid var(--good);border-radius:0 8px 8px 0;padding:.75rem 1rem;font-size:.87rem;color:#b0bcc8;margin-bottom:.45rem}
.thresh-box{background:#1a1f2e;border:1px solid #2a3040;border-radius:8px;padding:.6rem .9rem;font-size:.8rem;color:#8899bb;margin-top:.3rem;font-family:'Space Mono',monospace}
.thresh-box span{color:#e8eaf0;font-weight:700}
.red-overlay{position:fixed;inset:0;pointer-events:none;z-index:9999;animation:pr 1s ease-in-out infinite alternate}
@keyframes pr{from{background:rgba(255,23,68,.10)}to{background:rgba(255,23,68,.28)}}
.warn-banner{background:rgba(255,23,68,.12);border:1px solid rgba(255,23,68,.3);border-radius:8px;padding:.7rem 1rem;color:#ff6b8a;font-size:.88rem;margin-bottom:.8rem}
#MainMenu,footer,header{visibility:hidden;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PERSISTENT SHARED STATE via st.cache_resource
# Survives st.rerun(), safe to use across threads.
# The video thread writes here; Streamlit main thread reads here.
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_shared_state():
    return {
        "posture":     "Waiting…",
        "bad_thresh":  0.10,
        "warn_thresh": 0.075,
        "camera_on":   False,       # set True when video thread first runs
        "lock":        threading.Lock(),
    }

_S = get_shared_state()


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════════════
_defaults = dict(
    session_start=None, session_active=False,
    total_good=0, total_warn=0, total_bad=0,
    alert_count=0, last_alert_time=0,
    history=deque(maxlen=120),
    # store slider values in session_state so they persist across reruns
    sensitivity="Medium",
    alert_cooldown=15,
    voice_alerts=True,
    red_overlay_on=True,
)
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
_THRESH_MAP = {
    "Low":    (0.13, 0.10),
    "Medium": (0.10, 0.075),
    "High":   (0.07, 0.05),
}
_THRESH_LABELS = {
    "Low":    "Tolerant — only flags severe tilts",
    "Medium": "Balanced — recommended default",
    "High":   "Strict — flags even small tilts",
}

with st.sidebar:
    st.markdown("## 🧘 PostureSense")

    st.markdown("<div class='sh'>Detection Settings</div>", unsafe_allow_html=True)
    sensitivity = st.select_slider(
        "Shoulder tilt sensitivity",
        options=["Low", "Medium", "High"],
        value=st.session_state.sensitivity,
        key="sensitivity",
    )
    bad_t, warn_t = _THRESH_MAP[sensitivity]
    # Push to shared state so video thread picks it up immediately
    with _S["lock"]:
        _S["bad_thresh"]  = bad_t
        _S["warn_thresh"] = warn_t
    st.markdown(
        f"<div class='thresh-box'>"
        f"{_THRESH_LABELS[sensitivity]}<br>"
        f"Bad &gt; <span>{bad_t:.3f}</span> · Warn &gt; <span>{warn_t:.3f}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='sh'>Alert Settings</div>", unsafe_allow_html=True)
    voice_alerts   = st.toggle("🔊 Voice alerts",     value=st.session_state.voice_alerts,   key="voice_alerts")
    red_overlay_on = st.toggle("🔴 Red screen flash", value=st.session_state.red_overlay_on, key="red_overlay_on")
    alert_cooldown = st.slider(
        "Alert cooldown (sec)",
        min_value=5, max_value=60, step=5,
        value=st.session_state.alert_cooldown,
        key="alert_cooldown",
        help="Minimum seconds between voice/visual alerts",
    )
    st.markdown(
        f"<div class='thresh-box'>Alert fires at most every <span>{alert_cooldown}s</span></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='sh'>Posture Tips</div>", unsafe_allow_html=True)
    for tip in [
        "Keep shoulders level and relaxed.",
        "Ears should align over shoulders.",
        "Sit with hips pushed back in chair.",
        "Screen at eye level, arm's length away.",
        "Take a break every 30 minutes.",
    ]:
        st.markdown(f"<div class='tip'>💡 {tip}</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# VOICE ALERT
# Uses a JS interval that polls a hidden <input> value — works inside Streamlit
# iframes without relying on MutationObserver across iframe boundaries.
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<input type="hidden" id="_ps_ak" value="0"/>
<script>
(function(){
  var _last = "0";
  setInterval(function(){
    var el  = document.getElementById("_ps_ak");
    if(!el) return;
    var cur = el.value;
    if(cur !== "0" && cur !== _last){
      _last = cur;
      try{
        window.speechSynthesis.cancel();
        var u = new SpeechSynthesisUtterance(
          "Bad posture detected! Please sit up straight.");
        u.rate=0.92; u.pitch=1.0; u.volume=1.0;
        window.speechSynthesis.speak(u);
      }catch(e){}
    }
  }, 500);
})();
</script>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MEDIAPIPE DETECTOR — IMAGE mode (no timestamps, no freeze)
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def load_detector():
    opts = vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path="pose_landmarker_lite.task"),
        running_mode=vision.RunningMode.IMAGE,
    )
    return vision.PoseLandmarker.create_from_options(opts)

detector = load_detector()


# ══════════════════════════════════════════════════════════════════════════════
# VIDEO PROCESSOR
# Uses VideoProcessorBase (newer API) instead of VideoTransformerBase.
# Reads thresholds from _S live on every frame.
# Writes posture + camera_on flag back to _S.
# ══════════════════════════════════════════════════════════════════════════════
class PostureDetector(VideoProcessorBase):
    def recv(self, frame):
        import av
        img = frame.to_ndarray(format="bgr24")

        # Signal that camera is live
        with _S["lock"]:
            _S["camera_on"] = True

        rgb    = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        try:
            result = detector.detect(mp_img)
        except Exception:
            with _S["lock"]:
                _S["posture"] = "No Pose"
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        posture = "No Pose"
        color   = (120, 120, 120)

        if result.pose_landmarks:
            lms     = result.pose_landmarks[0]
            h, w, _ = img.shape
            left    = lms[11]   # left shoulder
            right   = lms[12]   # right shoulder
            diff    = abs(left.y - right.y)

            with _S["lock"]:
                bad_t  = _S["bad_thresh"]
                warn_t = _S["warn_thresh"]

            if diff > bad_t:
                posture, color = "Bad Posture",   (0, 0, 255)
            elif diff > warn_t:
                posture, color = "Slightly Bent", (0, 200, 255)
            else:
                posture, color = "Good Posture",  (0, 220, 100)

            # Draw skeleton
            for lm in lms:
                cv2.circle(img, (int(lm.x * w), int(lm.y * h)), 4, color, -1)
            cv2.line(img,
                     (int(left.x * w),  int(left.y * h)),
                     (int(right.x * w), int(right.y * h)),
                     color, 2)

        # Label overlay
        bg_col = {"Bad Posture": (0,0,180), "Slightly Bent": (0,130,130),
                  "Good Posture": (0,110,50)}.get(posture, (55, 55, 55))
        cv2.rectangle(img, (10, 10), (295, 60), bg_col, -1)
        cv2.putText(img, posture, (18, 47),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2, cv2.LINE_AA)

        with _S["lock"]:
            _S["posture"] = posture

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ══════════════════════════════════════════════════════════════════════════════
# READ POSTURE & UPDATE COUNTERS  (main Streamlit thread only)
# ══════════════════════════════════════════════════════════════════════════════
with _S["lock"]:
    posture_now = _S["posture"]
    camera_on   = _S["camera_on"]

if st.session_state.session_active and posture_now not in ("Waiting…", "No Pose"):
    now = time.time()
    if posture_now == "Good Posture":
        st.session_state.total_good += 1
    elif posture_now == "Slightly Bent":
        st.session_state.total_warn += 1
    elif posture_now == "Bad Posture":
        st.session_state.total_bad  += 1

    st.session_state.history.append(posture_now)

    if posture_now == "Bad Posture":
        if now - st.session_state.last_alert_time > st.session_state.alert_cooldown:
            st.session_state.last_alert_time = now
            st.session_state.alert_count    += 1


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("# 🧘 PostureSense")
st.markdown("##### Real-time posture monitoring · sit tall, work better")

col_cam, col_stats = st.columns([3, 2], gap="large")

# ─── Camera column ─────────────────────────────────────────────────────────────
with col_cam:

    # Session control buttons — Start is disabled until camera is live
    b1, b2 = st.columns(2)
    with b1:
        start_disabled = not camera_on   # can't start if no camera feed
        if st.button(
            "▶ Start Session",
            use_container_width=True,
            type="primary",
            disabled=start_disabled,
            help="Start the camera feed first, then click here" if start_disabled else None,
        ):
            st.session_state.update(
                session_active=True,
                session_start=time.time(),
                total_good=0, total_warn=0, total_bad=0,
                alert_count=0, last_alert_time=0,
                history=deque(maxlen=120),
            )
            st.rerun()

    with b2:
        if st.button("⏹ Stop Session", use_container_width=True,
                     disabled=not st.session_state.session_active):
            st.session_state.session_active = False
            # Reset camera_on flag so button disables again if stream restarts
            with _S["lock"]:
                _S["camera_on"] = False
            st.rerun()

    # Camera-not-started hint
    if not camera_on:
        st.markdown(
            "<div class='warn-banner'>📷 Click <b>START</b> in the camera widget below, "
            "allow camera access, then press ▶ Start Session above.</div>",
            unsafe_allow_html=True,
        )

    # WebRTC — multiple STUN servers + free TURN for Streamlit Cloud
   webrtc_streamer(
    key="posture",
    video_transformer_factory=PostureDetector,
    rtc_configuration={
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {
                "urls": ["turn:openrelay.metered.ca:80"],
                "username": "openrelayproject",
                "credential": "openrelayproject",
            },
        ]
    },
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)
    # Red overlay
    if st.session_state.red_overlay_on and posture_now == "Bad Posture" and st.session_state.session_active:
        st.markdown("<div class='red-overlay'></div>", unsafe_allow_html=True)

    # Trigger voice alert by updating the hidden input value
    if st.session_state.voice_alerts and st.session_state.session_active and st.session_state.alert_count > 0:
        ak = str(st.session_state.alert_count)
        st.markdown(
            f"<script>"
            f"(function(){{ var e=document.getElementById('_ps_ak'); if(e) e.value='{ak}'; }})();"
            f"</script>",
            unsafe_allow_html=True,
        )


# ─── Stats column ──────────────────────────────────────────────────────────────
with col_stats:
    st.markdown("<div class='sh'>Live Status</div>", unsafe_allow_html=True)

    pill_cls = {"Good Posture":"pg","Slightly Bent":"pw","Bad Posture":"pb"}.get(posture_now,"pi")
    st.markdown(f"<span class='pill {pill_cls}'>{posture_now}</span>", unsafe_allow_html=True)

    # Session timer
    elapsed = "--:--"
    if st.session_state.session_start:
        s   = int(time.time() - st.session_state.session_start)
        sfx = "" if st.session_state.session_active else " (ended)"
        elapsed = f"{s//60:02d}:{s%60:02d}{sfx}"

    t1, t2 = st.columns(2)
    with t1:
        st.markdown(f"<div class='mc'><div class='lbl'>Session Time</div>"
                    f"<div class='val wht'>{elapsed}</div></div>", unsafe_allow_html=True)
    with t2:
        st.markdown(f"<div class='mc'><div class='lbl'>Alerts Sent</div>"
                    f"<div class='val bad'>{st.session_state.alert_count}</div></div>",
                    unsafe_allow_html=True)

    # Posture breakdown %
    total    = st.session_state.total_good + st.session_state.total_warn + st.session_state.total_bad
    good_pct = round(st.session_state.total_good / total * 100) if total else 0
    warn_pct = round(st.session_state.total_warn / total * 100) if total else 0
    bad_pct  = round(st.session_state.total_bad  / total * 100) if total else 0

    st.markdown("<div class='sh'>Posture Breakdown</div>", unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)
    for col, lbl, pct, cls in [
        (g1, "Good",          good_pct, "good"),
        (g2, "Slightly Bent", warn_pct, "warn"),
        (g3, "Bad",           bad_pct,  "bad"),
    ]:
        with col:
            st.markdown(f"<div class='mc'><div class='lbl'>{lbl}</div>"
                        f"<div class='val {cls}'>{pct}%</div></div>", unsafe_allow_html=True)

    # Live timeline bar chart
    st.markdown("<div class='sh'>Posture Timeline (last 2 min)</div>", unsafe_allow_html=True)
    hl = list(st.session_state.history)
    if hl:
        n        = len(hl)
        svw, svh = 380, 80
        bw       = max(2, svw // n - 1)
        bars     = ""
        for i, p in enumerate(hl):
            if p == "Good Posture":
                v, c = 1.0, "#00e676"
            elif p == "Slightly Bent":
                v, c = 0.5, "#ffea00"
            else:
                v, c = 0.15, "#ff1744"
            bh = int(v * svh)
            x  = i * (svw // n)
            bars += f'<rect x="{x}" y="{svh-bh}" width="{bw}" height="{bh}" fill="{c}" rx="1"/>'
        st.markdown(
            f'<svg viewBox="0 0 {svw} {svh}" xmlns="http://www.w3.org/2000/svg" '
            f'style="width:100%;border-radius:8px;background:#161922;display:block;">'
            f'{bars}</svg>',
            unsafe_allow_html=True,
        )
        st.caption("🟢 Good  🟡 Slightly Bent  🔴 Bad")
    else:
        st.info("Start a session to see your posture history.")

    # Session summary (shown after Stop)
    if not st.session_state.session_active and st.session_state.session_start and total > 0:
        st.markdown("<div class='sh'>📋 Session Summary</div>", unsafe_allow_html=True)
        dur   = int(time.time() - st.session_state.session_start)
        gs    = round(st.session_state.total_good / total * dur)
        bs    = round(st.session_state.total_bad  / total * dur)
        grade = ("🏆 Excellent" if good_pct >= 80 else
                 "👍 Good"       if good_pct >= 60 else
                 "⚠️ Needs Work" if good_pct >= 40 else "❌ Poor")
        for ln in [
            f"**Duration:** {dur//60}m {dur%60}s",
            f"**Posture Score:** {good_pct}/100 — {grade}",
            f"**Good posture time:** ~{gs//60}m {gs%60}s ({good_pct}%)",
            f"**Bad posture time:** ~{bs//60}m {bs%60}s ({bad_pct}%)",
            f"**Alerts triggered:** {st.session_state.alert_count}",
        ]:
            st.markdown(ln)
        if good_pct >= 80:
            st.success("Great session! Keep up the excellent posture habits.")
        elif good_pct >= 60:
            st.warning("Decent session. Try to be more mindful during longer work blocks.")
        else:
            st.error("Your posture needs attention. Consider ergonomic adjustments.")


# ══════════════════════════════════════════════════════════════════════════════
# AUTO-REFRESH using st.fragment to avoid blocking the server thread
# Only reruns this fragment, not the entire page — safe for cloud deployment
# ══════════════════════════════════════════════════════════════════════════════
@st.fragment(run_every=1)
def _auto_refresh():
    """Lightweight fragment that triggers a stats refresh every second."""
    if st.session_state.session_active:
        # Just reading _S is enough to cause the fragment to re-render stats
        with _S["lock"]:
            _ = _S["posture"]

_auto_refresh()
