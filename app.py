import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# 한글 폰트 깨짐 방지 (시스템에 따라 기본 폰트 적용)
plt.rcParams['axes.unicode_minus'] = False

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
    elif "자이로스핀" in spin_type: omega = np.array([omega_mag, 0.0, 0.0]) 
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
        
    return np.array(x_t), np.array(y_t), np.array(z_t)

# --- SVG 마커 정의 (상단 정보 패널용) ---
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
st.title("⚾ 3D 야구공 궤적 및 물리 시뮬레이터 (WebGL 안전 모드)")
st.markdown("브라우저 WebGL 호환성과 관계없이 완벽하게 작동하는 Matplotlib 기반 3D 시뮬레이터입니다.")

with st.sidebar:
    st.header("투구 설정")
    v0_kmh = st.slider("구속 (km/h)", 100, 160, 145)
    v0_ms = v0_kmh / 3.6 
    spin_rpm = st.slider("회전수 (RPM)", 0, 3000, 2200)
    spin_type = st.radio("회전 방향 (구종 선택)", [
        "백스핀 (포심 패스트볼)", 
        "톱스핀 (커브볼)", 
        "사이드스핀 (슬라이더)", 
        "자이로스핀 (자이로볼)", 
        "무회전 (너클볼/포크볼)"
    ])
    st.header("환경 설정 (공기 밀도)")
    rho = st.slider("공기 밀도 (kg/m³)", 0.8, 1.3, 1.225, 0.005)

# --- 구종별 설명 패널 ---
st.markdown("---")
st.subheader(f"💡 {spin_type}의 물리적 특성 및 릴리즈 스냅")
col1, col2, col3, col4 = st.columns(4)

if "백스핀" in spin_type:
    svg_grip = f'<svg viewBox="0 0 100 100" width="130" height="130">{ball_base}<rect x="38" y="0" width="10" height="45" rx="5" fill="#ffcdb2" stroke="#343a40" stroke-width="1.5"/><rect x="52" y="0" width="10" height="45" rx="5" fill="#ffcdb2" stroke="#343a40" stroke-width="1.5"/></svg>'
    svg_snap = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<path d="M 50 15 C 75 15, 80 50, 50 85" fill="none" stroke="#e63946" stroke-width="4" marker-end="url(#arrow-red)"/></svg>'
    svg_magnus = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<path d="M 80 50 A 30 30 0 0 0 20 50" fill="none" stroke="#457b9d" stroke-width="3" marker-end="url(#arrow-blue)"/><line x1="50" y1="50" x2="50" y2="5" stroke="#9d4edd" stroke-width="4" marker-end="url(#arrow-purple)"/></svg>'
    svg_force = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<line x1="45" y1="50" x2="45" y2="85" stroke="#2a9d8f" stroke-width="3" marker-end="url(#arrow-green)"/><line x1="55" y1="50" x2="55" y2="15" stroke="#9d4edd" stroke-width="3" marker-end="url(#arrow-purple)"/><line x1="50" y1="50" x2="50" y2="40" stroke="#000000" stroke-width="4" stroke-dasharray="3,3" marker-end="url(#arrow-black)"/></svg>'
    desc1, desc2, desc3, desc4 = "수직으로 넓게 얹은 두 손가락", "위에서 아래로 실밥을 강하게 긁어내림", "공 아랫부분이 앞으로 구르는 백스핀 (양력)", "마그누스가 중력을 상쇄하여 덜 떨어짐"
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
    desc1, desc2, desc3, desc4 = "중심축 바깥쪽으로 치우쳐 쥔 손가락", "공 측면 실밥을 팽이 돌리듯 비껴 베어냄", "측면으로 도는 사이드스핀 (수평력)", "아래로 떨어지며 옆으로 예리하게 꺾임"
elif "자이로스핀" in spin_type:
    svg_grip = f'<svg viewBox="0 0 100 100" width="130" height="130">{ball_base}<circle cx="50" cy="50" r="15" fill="#ffcdb2" stroke="#343a40" stroke-width="1.5"/></svg>'
    svg_snap = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<path d="M 30 50 Q 50 30, 70 50 Q 50 70, 30 50" fill="none" stroke="#e63946" stroke-width="4" marker-end="url(#arrow-red)"/></svg>'
    svg_magnus = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<text x="50" y="55" font-size="14" text-anchor="middle" fill="#9d4edd" font-weight="bold">Force = 0</text></svg>'
    svg_force = f'<svg viewBox="0 0 100 100" width="130" height="130">{svg_defs}{ball_base}<line x1="50" y1="50" x2="50" y2="85" stroke="#2a9d8f" stroke-width="3" marker-end="url(#arrow-green)"/><line x1="50" y1="50" x2="50" y2="85" stroke="#000000" stroke-width="4" stroke-dasharray="3,3" marker-end="url(#arrow-black)"/></svg>'
    desc1, desc2, desc3, desc4 = "총알처럼 감싸 쥔 그립", "손목을 비틀어 나선형 회전(총알 회전) 가함", "진행 방향과 평행하여 마그누스 힘 0", "오직 중력만 받아 홈플레이트에서 뚝 떨어짐"
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

# --- 궤적 데이터 계산 ---
x_val, y_val, z_val = calculate_trajectory_3d(v0_ms, 1.0, spin_rpm, rho, spin_type)
x_base, y_base, z_base = calculate_trajectory_3d(v0_ms, 1.0, 0, rho, "무회전")

# --- Matplotlib 기반 3D 비행 궤적 시각화 ---
st.subheader("✈️ 홈플레이트까지의 3D 비행 궤적 (Matplotlib 렌더링)")
st.markdown("슬라이더를 움직여 공이 날아가는 위치를 실시간으로 확인하거나, 각도 조절로 입체적으로 관찰하세요.")

# 시점(각도) 조절 슬라이더
col_ang1, col_ang2 = st.columns(2)
with col_ang1:
    elev = st.slider("상하 각도 (Elevation)", 0, 90, 20)
with col_ang2:
    azim = st.slider("좌우 각도 (Azimuth)", -180, 180, -60)

# 진행 상황 조절 슬라이더 (애니메이션 대체)
max_idx = len(x_val) - 1
frame_idx = st.slider("공의 비행 위치 조절", 0, max_idx, max_idx)

# Matplotlib 3D 플롯 생성
fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(projection='3d')

# 1. 무회전 비교선
ax.plot(x_base, z_base, y_base, color='lightgray', linestyle='--', linewidth=2, label='무회전 궤적')

# 2. 전체 회전 궤적선
ax.plot(x_val, z_val, y_val, color='blue', linewidth=3, label=spin_type)

# 3.현재 공 위치 마커
ax.scatter([x_val[frame_idx]], [z_val[frame_idx]], [y_val[frame_idx]], color='black', s=80, label='야구공')

# 축 설정 (Matplotlib 3D 좌표 변환: X=전후, Y=높이, Z=좌우폭에 맞게 매핑)
ax.set_xlim(0, 20)
ax.set_ylim(0, 3)
ax.set_zlim(-2, 2)
ax.set_xlabel("투구 거리 (m)")
ax.set_ylabel("높이 (m)")
ax.set_zlabel("좌우 폭 (m)")
ax.view_init(elev=elev, azim=azim)
ax.legend(loc='upper left')

st.pyplot(fig)
