import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 물리 상수 설정 ---
m = 0.145
r = 0.036
A = np.pi * r**2
g = 9.81
Cd = 0.3
Cl_factor = 1.5
dt = 0.005

def calculate_trajectory_3d(v0, theta_deg, spin_rpm, rho, spin_type):
    theta = np.radians(theta_deg)
    pos = np.array([0.0, 2.0, 0.0])
    vel = np.array([v0 * np.cos(theta), v0 * np.sin(theta), 0.0])
    
    omega_mag = spin_rpm * (2 * np.pi / 60)
    if "백스핀" in spin_type: omega = np.array([0.0, 0.0, omega_mag]) 
    elif "톱스핀" in spin_type: omega = np.array([0.0, 0.0, -omega_mag]) 
    elif "사이드스핀" in spin_type: omega = np.array([0.0, omega_mag, 0.0]) 
    else: omega = np.array([0.0, 0.0, 0.0])
        
    x_t, y_t, z_t = [], [], []
    while pos[1] > 0 and pos[0] < 20: 
        x_t.append(pos[0])
        y_t.append(pos[1])
        z_t.append(pos[2])
        v_mag = np.linalg.norm(vel)
        
        F_g = np.array([0.0, -m * g, 0.0])
        F_d = - (0.5 * rho * v_mag**2 * Cd * A) * (vel / v_mag) if v_mag > 0 else np.array([0.0, 0.0, 0.0])
        
        F_m = np.array([0.0, 0.0, 0.0])
        if v_mag > 0 and np.linalg.norm(omega) > 0:
            F_m = 0.5 * rho * A * Cl_factor * r * np.cross(omega, vel)
        
        acc = (F_g + F_d + F_m) / m
        vel += acc * dt
        pos += vel * dt
        
    return x_t, y_t, z_t

# --- SVG 마커 및 기본 도형 정의 ---
svg_defs = """
<defs>
    <marker id="arrow-blue" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#457b9d" />
    </marker>
    <marker id="arrow-purple" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#9d4edd" />
    </marker>
    <marker id="arrow-green" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#2a9d8f" />
    </marker>
    <marker id="arrow-black" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#000000" />
    </marker>
    <marker id="arrow-red" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#e63946" />
    </marker>
</defs>
"""
svg_wrapper = '<div style="display: flex; justify-content: center; align-items: center; margin: 10px 0;">{}</div>'
ball_base = '<circle cx="50" cy="50" r="35" fill="#f8f9fa" stroke="#343a40" stroke-width="2"/><path d="M 25 25 Q 55 50 25 75" fill="none" stroke="#e63946" stroke-width="2" stroke-dasharray="4,4"/><path d="M 75 25 Q 45 50 75 75" fill="none" stroke="#e63946" stroke-width="2" stroke-dasharray="4,4"/>'

# --- Streamlit UI 구성 ---
st.set_page_config(page_title="3D 야구공 물리 시뮬레이터", layout="wide")
st.title("⚾ 3D 야구공 궤적 시뮬레이터")
st.markdown("선택한 구종의 그립, **던지는 순간의 손가락 스냅**, 물리적 힘의 작용 원리를 단계별 그림으로 직관적으로 확인하세요!")

with st.sidebar:
    st.header("투구 설정")
    v0_kmh = st.slider("구속 (km/h)", 100, 160, 145)
    v0_ms = v0_kmh / 3.6 
    spin_rpm = st.slider("회전수 (RPM)", 0, 3000, 2200)
    spin_type = st.radio("회전 방향 (구종 선택)", ["백스핀 (포심 패스트볼)", "톱스핀 (커브볼)", "사이드스핀 (슬라이더)", "무회전 (너클볼/포크볼)"])
    st.header("환경 설정 (공기 밀도)")
    rho = st.slider("공기 밀도 (kg/m³)", 0.8, 1.3, 1.225, 0.005)

# --- 구종별 그림(SVG) UI 패널 ---
st.markdown("---")
st.subheader(f"💡 {spin_type}의 물리적 특성")
col1, col2, col3, col4 = st.columns(4)

# 그림 코드(SVG) 생성 분기
if "백스핀" in spin_type:
    svg_grip = f'<svg viewBox="0 0 100 100" width="130" height="130">{ball_base}<rect x="38" y="0" width="10" height="45" rx="5" fill="#ffcdb2" stroke="#343a40" stroke-width="1.5"/><rect x="52" y="0" width="10" height="45" rx="5" fill="#ffcdb2" stroke="#343a40" stroke-width="1.5"/></svg>'
    svg_snap = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<path d="M 50 15 C 75 15, 80 50, 50 85" fill="none" stroke="#e63946" stroke-width="4" marker-end="url(#arrow-red)"/></svg>'
    svg_magnus = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<path d="M 80 50 A 30 30 0 0 0 20 50" fill="none" stroke="#457b9d" stroke-width="3" marker-end="url(#arrow-blue)"/><line x1="50" y1="50" x2="50" y2="5" stroke="#9d4edd" stroke-width="4" marker-end="url(#arrow-purple)"/></svg>'
    svg_force = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<line x1="45" y1="50" x2="45" y2="85" stroke="#2a9d8f" stroke-width="3" marker-end="url(#arrow-green)"/><line x1="55" y1="50" x2="55" y2="15" stroke="#9d4edd" stroke-width="3" marker-end="url(#arrow-purple)"/><line x1="50" y1="50" x2="50" y2="40" stroke="#000000" stroke-width="4" stroke-dasharray="3,3" marker-end="url(#arrow-black)"/></svg>'
    desc1, desc2, desc3, desc4 = "수직으로 넓게 얹은 두 손가락", "위에서 아래로 실밥을 강하게 긁어내림 (스냅)", "공 아랫부분이 앞으로 구르는 백스핀 (양력)", "마그누스가 중력을 상쇄하여 덜 떨어짐"

elif "톱스핀" in spin_type:
    svg_grip = f'<svg viewBox="0 0 100 100" width="130" height="130">{ball_base}<rect x="55" y="5" width="10" height="45" rx="5" fill="#ffcdb2" stroke="#343a40" stroke-width="1.5" transform="rotate(30, 55, 5)"/><rect x="68" y="10" width="10" height="45" rx="5" fill="#ffcdb2" stroke="#343a40" stroke-width="1.5" transform="rotate(30, 68, 10)"/></svg>'
    svg_snap = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<path d="M 50 15 C 25 15, 20 50, 50 85" fill="none" stroke="#e63946" stroke-width="4" marker-end="url(#arrow-red)"/></svg>'
    svg_magnus = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<path d="M 20 50 A 30 30 0 0 0 80 50" fill="none" stroke="#457b9d" stroke-width="3" marker-end="url(#arrow-blue)"/><line x1="50" y1="50" x2="50" y2="95" stroke="#9d4edd" stroke-width="4" marker-end="url(#arrow-purple)"/></svg>'
    svg_force = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<line x1="45" y1="50" x2="45" y2="75" stroke="#2a9d8f" stroke-width="3" marker-end="url(#arrow-green)"/><line x1="55" y1="50" x2="55" y2="75" stroke="#9d4edd" stroke-width="3" marker-end="url(#arrow-purple)"/><line x1="50" y1="50" x2="50" y2="95" stroke="#000000" stroke-width="4" stroke-dasharray="3,3" marker-end="url(#arrow-black)"/></svg>'
    desc1, desc2, desc3, desc4 = "실밥 선을 따라 감싸 쥔 손가락", "손목을 꺾어 공 앞면을 덮어 씌우듯 긁어내림", "공 윗부분이 앞으로 구르는 톱스핀 (하향력)", "중력과 마그누스가 합쳐져 급격히 떨어짐"

elif "사이드스핀" in spin_type:
    svg_grip = f'<svg viewBox="0 0 100 100" width="130" height="130">{ball_base}<rect x="55" y="0" width="10" height="45" rx="5" fill="#ffcdb2" stroke="#343a40" stroke-width="1.5" transform="rotate(15, 55, 0)"/><rect x="68" y="-5" width="10" height="45" rx="5" fill="#ffcdb2" stroke="#343a40" stroke-width="1.5" transform="rotate(15, 68, -5)"/></svg>'
    svg_snap = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<path d="M 65 15 C 90 35, 90 65, 65 85" fill="none" stroke="#e63946" stroke-width="4" marker-end="url(#arrow-red)"/></svg>'
    svg_magnus = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<ellipse cx="50" cy="50" rx="35" ry="12" fill="none" stroke="#457b9d" stroke-width="3" stroke-dasharray="3,3"/><line x1="50" y1="50" x2="95" y2="50" stroke="#9d4edd" stroke-width="4" marker-end="url(#arrow-purple)"/></svg>'
    svg_force = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<line x1="50" y1="50" x2="50" y2="85" stroke="#2a9d8f" stroke-width="3" marker-end="url(#arrow-green)"/><line x1="50" y1="50" x2="85" y2="50" stroke="#9d4edd" stroke-width="3" marker-end="url(#arrow-purple)"/><line x1="50" y1="50" x2="85" y2="85" stroke="#000000" stroke-width="4" stroke-dasharray="3,3" marker-end="url(#arrow-black)"/></svg>'
    desc1, desc2, desc3, desc4 = "중심축 바깥쪽으로 치우쳐 쥔 손가락", "공의 측면 실밥을 팽이 돌리듯 비껴 베어냄", "측면으로 도는 사이드스핀 (수평력)", "아래로 떨어지며 옆으로 예리하게 꺾임"

else:
    svg_grip = f'<svg viewBox="0 0 100 100" width="130" height="130">{ball_base}<rect x="25" y="0" width="10" height="40" rx="5" fill="#ffcdb2" stroke="#343a40" stroke-width="1.5" transform="rotate(-20, 25, 0)"/><rect x="65" y="0" width="10" height="40" rx="5" fill="#ffcdb2" stroke="#343a40" stroke-width="1.5" transform="rotate(20, 65, 0)"/></svg>'
    svg_snap = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<line x1="50" y1="30" x2="50" y2="70" stroke="#e63946" stroke-width="4" stroke-dasharray="4,4" marker-end="url(#arrow-red)"/></svg>'
    svg_magnus = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<text x="50" y="55" font-size="16" text-anchor="middle" fill="#6c757d" font-weight="bold">No Spin</text></svg>'
    svg_force = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<line x1="50" y1="50" x2="50" y2="85" stroke="#2a9d8f" stroke-width="3" marker-end="url(#arrow-green)"/><line x1="50" y1="50" x2="50" y2="85" stroke="#000000" stroke-width="4" stroke-dasharray="3,3" marker-end="url(#arrow-black)"/></svg>'
    desc1, desc2, desc3, desc4 = "마찰을 줄이기 위해 넓게 벌린 손가락", "긁어내지 않고 그대로 밀어 밀쳐냄", "회전이 억제되어 마그누스 효과 미발생", "양력이 없어 중력에 의해 아래로 떨어짐"

with col1:
    st.markdown("#### 🖐️ 1. 그립")
    st.markdown(svg_wrapper.format(svg_grip), unsafe_allow_html=True)
    st.caption(desc1)
with col2:
    st.markdown("#### 💥 2. 릴리스 스냅")
    st.markdown(svg_wrapper.format(svg_snap), unsafe_allow_html=True)
    st.caption(desc2)
with col3:
    st.markdown("#### 🌪️ 3. 회전과 양력")
    st.markdown(svg_wrapper.format(svg_magnus), unsafe_allow_html=True)
    st.caption(desc3)
with col4:
    st.markdown("#### ⚙️ 4. 최종 힘")
    st.markdown(svg_wrapper.format(svg_force), unsafe_allow_html=True)
    st.caption(desc4)

st.markdown("---")

# --- 궤적 계산 ---
x_val, y_val, z_val = calculate_trajectory_3d(v0_ms, 1.0, spin_rpm, rho, spin_type)
x_base, y_base, z_base = calculate_trajectory_3d(v0_ms, 1.0, 0, rho, "무회전") 

# --- Plotly 3D 애니메이션 구성 ---
fig = go.Figure()

fig.add_trace(go.Scatter3d(x=x_base, y=z_base, z=y_base, mode='lines', line=dict(color='lightgray', dash='dash', width=4), name='무회전 궤적'))
fig.add_trace(go.Scatter3d(x=[x_val[0]], y=[z_val[0]], z=[y_val[0]], mode='lines', line=dict(color='blue', width=4), name=spin_type))
fig.add_trace(go.Scatter3d(x=[x_val[0]], y=[z_val[0]], z=[y_val[0]], mode='markers', marker=dict(color='black', size=5), name='야구공'))

frames = []
interval = 5 
for i in range(0, len(x_val), interval):
    px, py, pz = x_val[i], z_val[i], y_val[i]
    frames.append(go.Frame(
        data=[
            go.Scatter3d(x=x_base, y=z_base, z=y_base), 
            go.Scatter3d(x=x_val[:i+1], y=z_val[:i+1], z=y_val[:i+1]), 
            go.Scatter3d(x=[px], y=[py], z=[pz])
        ]
    ))
fig.frames = frames

# 5. 레이아웃 및 3D 카메라 설정
fig.update_layout(
    uirevision='constant',
    scene=dict(
        xaxis=dict(range=[0, 20], title="투구 거리 (m)", showgrid=True),
        yaxis=dict(range=[-2, 2], title="좌우 폭 (m)", showgrid=True), 
        zaxis=dict(range=[0, 3], title="높이 (m)", showgrid=True),
        aspectmode='manual',
        aspectratio=dict(x=3, y=1, z=1), 
        camera=dict(eye=dict(x=2.5, y=-1.5, z=0.8))
    ),
    height=600,
    margin=dict(l=0, r=0, b=80, t=10), 
    showlegend=True,
    legend=dict(x=0, y=1, bgcolor='rgba(255,255,255,0.7)'),
    updatemenus=[dict(
        type="buttons", showactive=False, direction="left", x=0.5, y=-0.1, xanchor="center", yanchor="top",
        buttons=[
            dict(label="▶ 재생", method="animate", args=[None, dict(frame=dict(duration=80, redraw=True), transition=dict(duration=0), fromcurrent=True)]),
            dict(label="⏸ 일시정지", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))])
        ]
    )]
)

st.plotly_chart(fig, use_container_width=True)
