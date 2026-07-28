import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 물리 상수 설정 ---
m = 0.145  # 야구공 질량 (kg)
r = 0.036  # 야구공 반지름 (m)
A = np.pi * r**2  # 공 단면적 (m^2)
g = 9.81  # 중력가속도 (m/s^2)
Cd = 0.3  # 항력 계수
Cl_factor = 1.5  # 마그누스 양력 계수 비례상수

dt = 0.005  # 시간 간격 (초)
arrow_scale = 0.4  # 화살표 크기 고정

def calculate_trajectory_3d(v0, theta_deg, spin_rpm, rho, spin_type):
    """3D 벡터 외적을 활용한 정교한 3차원 궤적 및 힘 계산기"""
    theta = np.radians(theta_deg)
    
    # 초기 위치 (x: 홈플레이트 방향, y: 높이, z: 좌우 폭)
    pos = np.array([0.0, 2.0, 0.0])
    # 초기 속도
    vel = np.array([v0 * np.cos(theta), v0 * np.sin(theta), 0.0])
    
    # 각속도 벡터 (Spin Vector) 설정
    omega_mag = spin_rpm * (2 * np.pi / 60)
    if spin_type == "백스핀 (포심 패스트볼)":
        omega = np.array([0.0, 0.0, omega_mag]) # Z축 기준 회전 -> 위로 떠오름 (Y축 양수)
    elif spin_type == "톱스핀 (커브볼)":
        omega = np.array([0.0, 0.0, -omega_mag]) # Z축 반대 회전 -> 아래로 떨어짐 (Y축 음수)
    elif spin_type == "사이드스핀 (슬라이더)":
        omega = np.array([0.0, omega_mag, 0.0]) # Y축 기준 회전 -> 옆으로 휨 (Z축 이동)
    else:
        omega = np.array([0.0, 0.0, 0.0])
        
    x_t, y_t, z_t = [], [], []
    Fg_t, Fd_t, Fm_t = [], [], []
    
    while pos[1] > 0 and pos[0] < 20: 
        x_t.append(pos[0])
        y_t.append(pos[1])
        z_t.append(pos[2])
        
        v_mag = np.linalg.norm(vel)
        
        # 1. 중력 벡터
        F_g = np.array([0.0, -m * g, 0.0])
        Fg_t.append(F_g)
        
        # 2. 공기 저항력 벡터 (속도의 반대 방향)
        F_d = np.array([0.0, 0.0, 0.0])
        if v_mag > 0:
            Fd_mag = 0.5 * rho * v_mag**2 * Cd * A
            F_d = -Fd_mag * (vel / v_mag)
        Fd_t.append(F_d)
        
        # 3. 마그누스 힘 벡터 (회전축과 속도 벡터의 외적)
        F_m = np.array([0.0, 0.0, 0.0])
        if v_mag > 0 and np.linalg.norm(omega) > 0:
            # F_m ∝ ω × v
            cross_product = np.cross(omega, vel)
            F_m = 0.5 * rho * A * Cl_factor * r * cross_product
        Fm_t.append(F_m)
        
        # 가속도 및 위치 업데이트
        F_net = F_g + F_d + F_m
        acc = F_net / m
        
        vel += acc * dt
        pos += vel * dt
        
    return x_t, y_t, z_t, Fg_t, Fd_t, Fm_t

# --- Streamlit UI 구성 ---
st.set_page_config(page_title="3D 야구공 물리 시뮬레이터", layout="wide")
st.title("⚾ 3D 야구공 궤적 및 힘 벡터 시뮬레이터")
st.markdown("""
- **회전(관찰) 방법:** 그래프 안을 **클릭한 채로 요리조리 드래그**하시면 투수 시점, 타자 시점, 위에서 본 뷰 등으로 자유롭게 돌려볼 수 있습니다.
- **일시정지:** 공이 날아가는 도중 힘 벡터를 자세히 보고 싶다면 하단의 **[⏸ 일시정지]** 버튼을 눌러주세요.
""")

with st.sidebar:
    st.header("투구 설정")
    v0_kmh = st.slider("구속 (km/h)", 100, 160, 145)
    v0_ms = v0_kmh / 3.6 
    
    spin_rpm = st.slider("회전수 (RPM)", 0, 3000, 2200)
    spin_type = st.radio("회전 방향 (구종)", [
        "백스핀 (포심 패스트볼)", 
        "톱스핀 (커브볼)", 
        "사이드스핀 (슬라이더)", # 3D 체감을 위한 슬라이더 추가!
        "무회전 (너클볼/포크볼)"
    ])
    
    st.header("환경 설정 (공기 밀도)")
    st.markdown("해수면 기준 1.225 / 쿠어스 필드(고지대) 약 1.000")
    rho = st.slider("공기 밀도 (kg/m³)", 0.8, 1.3, 1.225, 0.005)

# --- 궤적 계산 ---
x_val, y_val, z_val, Fg_val, Fd_val, Fm_val = calculate_trajectory_3d(v0_ms, 1.0, spin_rpm, rho, spin_type)
x_base, y_base, z_base, _, _, _ = calculate_trajectory_3d(v0_ms, 1.0, 0, rho, "무회전") 

# --- Plotly 3D 애니메이션 구성 ---
fig = go.Figure()

# 1. 무회전 비교선 추가
fig.add_trace(go.Scatter3d(x=x_base, y=z_base, z=y_base, mode='lines', 
                           line=dict(color='lightgray', dash='dash', width=4), 
                           name='무회전 궤적'))

# 2. 실제 궤적 선 및 야구공 마커 껍데기
fig.add_trace(go.Scatter3d(x=[x_val[0]], y=[z_val[0]], z=[y_val[0]], mode='lines', 
                           line=dict(color='blue', width=6), name=spin_type))
fig.add_trace(go.Scatter3d(x=[x_val[0]], y=[z_val[0]], z=[y_val[0]], mode='markers', 
                           marker=dict(color='red', size=8), name='야구공'))

# 3. 힘 벡터 껍데기 (size=[0, 8]을 사용하여 화살표 머리 쪽에만 점을 찍어 방향 표시)
fig.add_trace(go.Scatter3d(x=[x_val[0], x_val[0] + Fg_val[0][0]*arrow_scale], y=[z_val[0], z_val[0] + Fg_val[0][2]*arrow_scale], z=[y_val[0], y_val[0] + Fg_val[0][1]*arrow_scale],
                           mode='lines+markers', line=dict(color='green', width=4), marker=dict(size=[0, 6], color='green'), name='중력'))
fig.add_trace(go.Scatter3d(x=[x_val[0], x_val[0] + Fd_val[0][0]*arrow_scale], y=[z_val[0], z_val[0] + Fd_val[0][2]*arrow_scale], z=[y_val[0], y_val[0] + Fd_val[0][1]*arrow_scale],
                           mode='lines+markers', line=dict(color='red', width=4), marker=dict(size=[0, 6], color='red'), name='공기 저항력'))
fig.add_trace(go.Scatter3d(x=[x_val[0], x_val[0] + Fm_val[0][0]*arrow_scale], y=[z_val[0], z_val[0] + Fm_val[0][2]*arrow_scale], z=[y_val[0], y_val[0] + Fm_val[0][1]*arrow_scale],
                           mode='lines+markers', line=dict(color='purple', width=4), marker=dict(size=[0, 6], color='purple'), name='마그누스 힘'))

# 4. 애니메이션 프레임 생성
frames = []
interval = 5 
for i in range(0, len(x_val), interval):
    # Plotly 3D에서는 통상적으로 x:깊이, y:좌우, z:높이 로 매핑하면 보기 편합니다.
    frames.append(go.Frame(
        data=[
            go.Scatter3d(x=x_base, y=z_base, z=y_base), 
            go.Scatter3d(x=x_val[:i+1], y=z_val[:i+1], z=y_val[:i+1]), 
            go.Scatter3d(x=[x_val[i]], y=[z_val[i]], z=[y_val[i]]),  
            # 힘 벡터들
            go.Scatter3d(x=[x_val[i], x_val[i] + Fg_val[i][0]*arrow_scale], y=[z_val[i], z_val[i] + Fg_val[i][2]*arrow_scale], z=[y_val[i], y_val[i] + Fg_val[i][1]*arrow_scale]),
            go.Scatter3d(x=[x_val[i], x_val[i] + Fd_val[i][0]*arrow_scale], y=[z_val[i], z_val[i] + Fd_val[i][2]*arrow_scale], z=[y_val[i], y_val[i] + Fd_val[i][1]*arrow_scale]),
            go.Scatter3d(x=[x_val[i], x_val[i] + Fm_val[i][0]*arrow_scale], y=[z_val[i], z_val[i] + Fm_val[i][2]*arrow_scale], z=[y_val[i], y_val[i] + Fm_val[i][1]*arrow_scale])
        ]
    ))
fig.frames = frames

# 5. 레이아웃 및 3D 카메라 설정
fig.update_layout(
    scene=dict(
        xaxis=dict(range=[0, 20], title="투구 거리 (m)", showgrid=True),
        yaxis=dict(range=[-2, 2], title="좌우 폭 (m)", showgrid=True), # 좌우 이동 관찰을 위한 y축(그래프상)
        zaxis=dict(range=[0, 3], title="높이 (m)", showgrid=True),
        aspectmode='manual',
        aspectratio=dict(x=3, y=1, z=1), # 3D 박스 비율 조정 (거리가 길게 보이도록)
        camera=dict(
            eye=dict(x=2.5, y=-1.5, z=0.8) # 초기 관찰자 시점
        )
    ),
    height=700,
    margin=dict(l=0, r=0, b=0, t=30),
    updatemenus=[dict(
        type="buttons",
        showactive=False,
        direction="left",
        x=0.5, y=-0.1,
        xanchor="center", yanchor="top",
        buttons=[
            dict(label="▶ 재생",
                 method="animate",
                 # duration을 100으로 늘려 애니메이션 속도를 체감하기 좋게 늦춤
                 args=[None, dict(frame=dict(duration=100, redraw=True), transition=dict(duration=0), fromcurrent=True)]),
            dict(label="⏸ 일시정지",
                 method="animate",
                 args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))])
        ]
    )]
)

st.plotly_chart(fig, use_container_width=True)
