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
arrow_scale = 0.4  # 화살표 길이 배율 (고정)
cone_scale = 0.3   # 화살표 머리(원뿔) 크기 배율

def calculate_trajectory_3d(v0, theta_deg, spin_rpm, rho, spin_type):
    """3D 벡터 외적을 활용한 정교한 3차원 궤적 및 힘 계산기"""
    theta = np.radians(theta_deg)
    
    pos = np.array([0.0, 2.0, 0.0])
    vel = np.array([v0 * np.cos(theta), v0 * np.sin(theta), 0.0])
    
    omega_mag = spin_rpm * (2 * np.pi / 60)
    if spin_type == "백스핀 (포심 패스트볼)":
        omega = np.array([0.0, 0.0, omega_mag]) 
    elif spin_type == "톱스핀 (커브볼)":
        omega = np.array([0.0, 0.0, -omega_mag]) 
    elif spin_type == "사이드스핀 (슬라이더)":
        omega = np.array([0.0, omega_mag, 0.0]) 
    else:
        omega = np.array([0.0, 0.0, 0.0])
        
    x_t, y_t, z_t = [], [], []
    Fg_t, Fd_t, Fm_t = [], [], []
    
    while pos[1] > 0 and pos[0] < 20: 
        x_t.append(pos[0])
        y_t.append(pos[1])
        z_t.append(pos[2])
        
        v_mag = np.linalg.norm(vel)
        
        F_g = np.array([0.0, -m * g, 0.0])
        Fg_t.append(F_g)
        
        F_d = np.array([0.0, 0.0, 0.0])
        if v_mag > 0:
            Fd_mag = 0.5 * rho * v_mag**2 * Cd * A
            F_d = -Fd_mag * (vel / v_mag)
        Fd_t.append(F_d)
        
        F_m = np.array([0.0, 0.0, 0.0])
        if v_mag > 0 and np.linalg.norm(omega) > 0:
            cross_product = np.cross(omega, vel)
            F_m = 0.5 * rho * A * Cl_factor * r * cross_product
        Fm_t.append(F_m)
        
        F_net = F_g + F_d + F_m
        acc = F_net / m
        
        vel += acc * dt
        pos += vel * dt
        
    return x_t, y_t, z_t, Fg_t, Fd_t, Fm_t

# --- Streamlit UI 구성 ---
st.set_page_config(page_title="3D 야구공 물리 시뮬레이터", layout="wide")
st.title("⚾ 3D 야구공 궤적 및 힘 벡터 시뮬레이터")
st.markdown("""
- **애니메이션 중 관찰:** 공이 날아가는 동안에도 그래프 안을 마우스로 **드래그**하여 다양한 각도에서 입체적으로 궤적을 확인하실 수 있습니다.
- 화살표는 각 힘의 방향과 크기를 정교하게 나타냅니다.
""")

with st.sidebar:
    st.header("투구 설정")
    v0_kmh = st.slider("구속 (km/h)", 100, 160, 145)
    v0_ms = v0_kmh / 3.6 
    
    spin_rpm = st.slider("회전수 (RPM)", 0, 3000, 2200)
    spin_type = st.radio("회전 방향 (구종)", [
        "백스핀 (포심 패스트볼)", 
        "톱스핀 (커브볼)", 
        "사이드스핀 (슬라이더)", 
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
                           line=dict(color='lightgray', dash='dash', width=4), name='무회전 궤적'))

# 2, 3. 실제 궤적 선 및 야구공 마커 껍데기
fig.add_trace(go.Scatter3d(x=[x_val[0]], y=[z_val[0]], z=[y_val[0]], mode='lines', 
                           line=dict(color='blue', width=6), name=spin_type))
fig.add_trace(go.Scatter3d(x=[x_val[0]], y=[z_val[0]], z=[y_val[0]], mode='markers', 
                           marker=dict(color='red', size=8), name='야구공'))

# 초기 프레임의 힘 벡터 데이터 추출 (Plotly 3D: X=전후, Y=좌우(Z), Z=상하(Y))
gx, gy, gz = Fg_val[0][0], Fg_val[0][2], Fg_val[0][1]
dx, dy, dz = Fd_val[0][0], Fd_val[0][2], Fd_val[0][1]
mx, my, mz = Fm_val[0][0], Fm_val[0][2], Fm_val[0][1]

# 4, 5. 중력 화살표 (선 + 원뿔 머리)
fig.add_trace(go.Scatter3d(x=[x_val[0], x_val[0] + gx*arrow_scale], y=[z_val[0], z_val[0] + gy*arrow_scale], z=[y_val[0], y_val[0] + gz*arrow_scale],
                           mode='lines', line=dict(color='green', width=4), name='중력(선)'))
fig.add_trace(go.Cone(x=[x_val[0] + gx*arrow_scale], y=[z_val[0] + gy*arrow_scale], z=[y_val[0] + gz*arrow_scale], u=[gx], v=[gy], w=[gz],
                      colorscale=[[0, 'green'], [1, 'green']], showscale=False, sizemode='absolute', sizeref=cone_scale, anchor='tip', hoverinfo='skip', name='중력'))

# 6, 7. 공기 저항력 화살표 (선 + 원뿔 머리)
fig.add_trace(go.Scatter3d(x=[x_val[0], x_val[0] + dx*arrow_scale], y=[z_val[0], z_val[0] + dy*arrow_scale], z=[y_val[0], y_val[0] + dz*arrow_scale],
                           mode='lines', line=dict(color='red', width=4), name='공기 저항(선)'))
fig.add_trace(go.Cone(x=[x_val[0] + dx*arrow_scale], y=[z_val[0] + dy*arrow_scale], z=[y_val[0] + dz*arrow_scale], u=[dx], v=[dy], w=[dz],
                      colorscale=[[0, 'red'], [1, 'red']], showscale=False, sizemode='absolute', sizeref=cone_scale, anchor='tip', hoverinfo='skip', name='공기 저항력'))

# 8, 9. 마그누스 힘 화살표 (선 + 원뿔 머리)
fig.add_trace(go.Scatter3d(x=[x_val[0], x_val[0] + mx*arrow_scale], y=[z_val[0], z_val[0] + my*arrow_scale], z=[y_val[0], y_val[0] + mz*arrow_scale],
                           mode='lines', line=dict(color='purple', width=4), name='마그누스 힘(선)'))
fig.add_trace(go.Cone(x=[x_val[0] + mx*arrow_scale], y=[z_val[0] + my*arrow_scale], z=[y_val[0] + mz*arrow_scale], u=[mx], v=[my], w=[mz],
                      colorscale=[[0, 'purple'], [1, 'purple']], showscale=False, sizemode='absolute', sizeref=cone_scale, anchor='tip', hoverinfo='skip', name='마그누스 힘'))

# 10. 애니메이션 프레임 생성
frames = []
interval = 5 
for i in range(0, len(x_val), interval):
    px, py, pz = x_val[i], z_val[i], y_val[i]
    gx, gy, gz = Fg_val[i][0], Fg_val[i][2], Fg_val[i][1]
    dx, dy, dz = Fd_val[i][0], Fd_val[i][2], Fd_val[i][1]
    mx, my, mz = Fm_val[i][0], Fm_val[i][2], Fm_val[i][1]

    frames.append(go.Frame(
        data=[
            go.Scatter3d(x=x_base, y=z_base, z=y_base), 
            go.Scatter3d(x=x_val[:i+1], y=z_val[:i+1], z=y_val[:i+1]), 
            go.Scatter3d(x=[px], y=[py], z=[pz]),  
            
            # 중력 (선 + 원뿔)
            go.Scatter3d(x=[px, px + gx*arrow_scale], y=[py, py + gy*arrow_scale], z=[pz, pz + gz*arrow_scale]),
            go.Cone(x=[px + gx*arrow_scale], y=[py + gy*arrow_scale], z=[pz + gz*arrow_scale], u=[gx], v=[gy], w=[gz]),
            
            # 공기 저항력 (선 + 원뿔)
            go.Scatter3d(x=[px, px + dx*arrow_scale], y=[py, py + dy*arrow_scale], z=[pz, pz + dz*arrow_scale]),
            go.Cone(x=[px + dx*arrow_scale], y=[py + dy*arrow_scale], z=[pz + dz*arrow_scale], u=[dx], v=[dy], w=[dz]),
            
            # 마그누스 힘 (선 + 원뿔)
            go.Scatter3d(x=[px, px + mx*arrow_scale], y=[py, py + my*arrow_scale], z=[pz, pz + mz*arrow_scale]),
            go.Cone(x=[px + mx*arrow_scale], y=[py + my*arrow_scale], z=[pz + mz*arrow_scale], u=[mx], v=[my], w=[mz])
        ]
    ))
fig.frames = frames

# 11. 레이아웃 및 3D 카메라 설정
fig.update_layout(
    scene=dict(
        xaxis=dict(range=[0, 20], title="투구 거리 (m)", showgrid=True),
        yaxis=dict(range=[-2, 2], title="좌우 폭 (m)", showgrid=True), 
        zaxis=dict(range=[0, 3], title="높이 (m)", showgrid=True),
        aspectmode='manual',
        aspectratio=dict(x=3, y=1, z=1), 
        camera=dict(
            eye=dict(x=2.5, y=-1.5, z=0.8) 
        )
    ),
    height=700,
    margin=dict(l=0, r=0, b=0, t=30),
    showlegend=False,
    updatemenus=[dict(
        type="buttons",
        showactive=False,
        direction="left",
        x=0.5, y=-0.1,
        xanchor="center", yanchor="top",
        buttons=[
            dict(label="▶ 재생",
                 method="animate",
                 # redraw=False로 변경하여 애니메이션 중 시점 회전(드래그)을 허용합니다!
                 args=[None, dict(frame=dict(duration=80, redraw=False), transition=dict(duration=0), fromcurrent=True)]),
            dict(label="⏸ 일시정지",
                 method="animate",
                 args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))])
        ]
    )]
)

st.plotly_chart(fig, use_container_width=True)
