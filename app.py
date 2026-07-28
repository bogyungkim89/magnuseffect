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

def calculate_trajectory_with_forces(v0, theta_deg, spin_rpm, rho, spin_type):
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
    Fg_t, Fd_t, Fm_t = [], [], []
    
    while pos[1] > 0 and pos[0] < 20: 
        x_t.append(pos[0])
        y_t.append(pos[1])
        z_t.append(pos[2])
        v_mag = np.linalg.norm(vel)
        
        # 1. 중력
        F_g = np.array([0.0, -m * g, 0.0])
        Fg_t.append(F_g)
        
        # 2. 공기 저항력
        F_d = np.array([0.0, 0.0, 0.0])
        if v_mag > 0:
            Fd_mag = 0.5 * rho * v_mag**2 * Cd * A
            F_d = -Fd_mag * (vel / v_mag)
        Fd_t.append(F_d)
        
        # 3. 마그누스 힘
        F_m = np.array([0.0, 0.0, 0.0])
        if v_mag > 0 and np.linalg.norm(omega) > 0:
            F_m = 0.5 * rho * A * Cl_factor * r * np.cross(omega, vel)
        Fm_t.append(F_m)
        
        acc = (F_g + F_d + F_m) / m
        vel += acc * dt
        pos += vel * dt
        
    return np.array(x_t), np.array(y_t), np.array(z_t), Fg_t, Fd_t, Fm_t

# --- Streamlit UI 구성 ---
st.set_page_config(page_title="3D 야구공 궤적 및 힘 시뮬레이터", layout="wide")
st.title("⚾ 3D 야구공 궤적 및 힘 벡터 시뮬레이터 (안정화 버전)")
st.markdown("마우스로 3D 그래프를 자유롭게 돌려가며 공이 날아가는 동안 **매 순간 작용하는 힘(중력, 공기저항, 마그누스 힘)**을 확인하세요!")

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

# --- 데이터 계산 ---
x_val, y_val, z_val, Fg_val, Fd_val, Fm_val = calculate_trajectory_with_forces(v0_ms, 1.0, spin_rpm, rho, spin_type)
x_base, y_base, z_base, _, _, _ = calculate_trajectory_with_forces(v0_ms, 1.0, 0, rho, "무회전")

# --- 시간(위치) 조절 슬라이더 (애니메이션 대체) ---
max_idx = len(x_val) - 1
frame_idx = st.slider("⏱️ 공의 비행 위치 조절 (슬라이더를 움직여 매 순간의 힘을 관찰하세요)", 0, max_idx, max_idx // 2)

# 현재 위치 및 힘 벡터 추출 (Plotly 3D 축 매핑: X=거리, Y=좌우폭, Z=높이)
px, py, pz = x_val[frame_idx], z_val[frame_idx], y_val[frame_idx]

arrow_scale = 0.375
cone_scale = 0.2

# 중력 (Y축이 높이이므로 Z값에 매핑)
gx, gy, gz = Fg_val[frame_idx][0], Fg_val[frame_idx][2], Fg_val[frame_idx][1]
# 공기저항
dx, dy, dz = Fd_val[frame_idx][0], Fd_val[frame_idx][2], Fd_val[frame_idx][1]
# 마그누스 힘
mx, my, mz = Fm_val[frame_idx][0], Fm_val[frame_idx][2], Fm_val[frame_idx][1]

# --- Plotly 3D 그래프 구성 ---
fig = go.Figure()

# 1. 무회전 비교선
fig.add_trace(go.Scatter3d(x=x_base, y=z_base, z=y_base, mode='lines', line=dict(color='lightgray', dash='dash', width=3), name='무회전 궤적'))

# 2. 지나온 궤적선
fig.add_trace(go.Scatter3d(x=x_val[:frame_idx+1], y=z_val[:frame_idx+1], z=y_val[:frame_idx+1], mode='lines', line=dict(color='blue', width=4), name=spin_type))

# 3. 현재 야구공 마커
fig.add_trace(go.Scatter3d(x=[px], y=[py], z=[pz], mode='markers', marker=dict(color='black', size=6), name='야구공'))

# 4. 중력 화살표 (초록색)
fig.add_trace(go.Scatter3d(x=[px, px + gx*arrow_scale], y=[py, py + gy*arrow_scale], z=[pz, pz + gz*arrow_scale], mode='lines', line=dict(color='green', width=5), name='중력'))
fig.add_trace(go.Cone(x=[px + gx*arrow_scale], y=[py + gy*arrow_scale], z=[pz + gz*arrow_scale], u=[gx], v=[gy], w=[gz], colorscale=[[0, 'green'], [1, 'green']], showscale=False, sizemode='absolute', sizeref=cone_scale, anchor='tip', hoverinfo='skip'))

# 5. 공기 저항력 화살표 (빨간색)
fig.add_trace(go.Scatter3d(x=[px, px + dx*arrow_scale], y=[py, py + dy*arrow_scale], z=[pz, pz + dz*arrow_scale], mode='lines', line=dict(color='red', width=5), name='공기저항'))
fig.add_trace(go.Cone(x=[px + dx*arrow_scale], y=[py + dy*arrow_scale], z=[pz + dz*arrow_scale], u=[dx], v=[dy], w=[dz], colorscale=[[0, 'red'], [1, 'red']], showscale=False, sizemode='absolute', sizeref=cone_scale, anchor='tip', hoverinfo='skip'))

# 6. 마그누스 힘 화살표 (보라색)
if np.linalg.norm([mx, my, mz]) > 0.01:
    fig.add_trace(go.Scatter3d(x=[px, px + mx*arrow_scale], y=[py, py + my*arrow_scale], z=[pz, pz + mz*arrow_scale], mode='lines', line=dict(color='purple', width=5), name='마그누스 힘'))
    fig.add_trace(go.Cone(x=[px + mx*arrow_scale], y=[py + my*arrow_scale], z=[pz + mz*arrow_scale], u=[mx], v=[my], w=[mz], colorscale=[[0, 'purple'], [1, 'purple']], showscale=False, sizemode='absolute', sizeref=cone_scale, anchor='tip', hoverinfo='skip'))

fig.update_layout(
    scene=dict(
        xaxis=dict(range=[0, 20], title="투구 거리 (m)", showgrid=True),
        yaxis=dict(range=[-2, 2], title="좌우 폭 (m)", showgrid=True), 
        zaxis=dict(range=[0, 3], title="높이 (m)", showgrid=True),
        aspectmode='manual',
        aspectratio=dict(x=3, y=1, z=1),
        camera=dict(eye=dict(x=2.0, y=-1.8, z=0.8))
    ),
    height=650,
    margin=dict(l=0, r=0, b=0, t=30),
    legend=dict(x=0, y=1, bgcolor='rgba(255,255,255,0.8)')
)

st.plotly_chart(fig, use_container_width=True)
st.markdown("👉 **그래프 활용법:** 마우스로 그래프 안쪽을 클릭한 채 드래그하시면 **원하는 각도에서 입체적으로 회전**시켜 가며 볼 수 있습니다. 상단의 슬라이더를 움직여 공이 날아가는 타임라인별 힘의 변화를 관찰해보세요!")
