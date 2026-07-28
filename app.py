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

def calculate_trajectory(v0, theta_deg, spin_rpm, rho, spin_type):
    """오일러 방법을 사용한 2D 궤적 계산기"""
    dt = 0.01
    theta = np.radians(theta_deg)
    
    x, y = 0.0, 2.0  # 투수의 릴리스 포인트 높이 (2m)
    vx = v0 * np.cos(theta)
    vy = v0 * np.sin(theta)
    
    if spin_type == "백스핀 (포심 패스트볼)":
        omega = spin_rpm * (2 * np.pi / 60)
    elif spin_type == "톱스핀 (커브볼)":
        omega = -spin_rpm * (2 * np.pi / 60)
    else:
        omega = 0.0 
        
    x_traj, y_traj = [x], [y]
    
    while y > 0 and x < 20: 
        v = np.sqrt(vx**2 + vy**2)
        
        # 항력
        Fd = 0.5 * rho * v**2 * Cd * A
        Fdx = -Fd * (vx / v)
        Fdy = -Fd * (vy / v)
        
        # 마그누스 힘
        Fm = 0.5 * rho * v**2 * (Cl_factor * (r * omega / v)) * A if v > 0 else 0
        Fmx = -Fm * (vy / v) 
        Fmy = Fm * (vx / v)  
        
        # 가속도
        ax = (Fdx + Fmx) / m
        ay = (-m * g + Fdy + Fmy) / m
        
        # 속도 및 위치 업데이트
        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt
        
        x_traj.append(x)
        y_traj.append(y)
        
    return x_traj, y_traj

# --- Streamlit UI 구성 ---
st.set_page_config(page_title="야구공 궤적 시뮬레이터", layout="wide")
st.title("⚾ 야구공 투구 궤적 시뮬레이터 (애니메이션)")
st.markdown("왼쪽에서 투구 설정을 맞춘 뒤, 그래프 아래의 **'▶ 투구 시작!'** 버튼을 눌러 공이 날아가는 궤적을 확인하세요.")

with st.sidebar:
    st.header("투구 설정")
    v0_kmh = st.slider("구속 (km/h)", 100, 160, 145)
    v0_ms = v0_kmh / 3.6 
    
    spin_rpm = st.slider("회전수 (RPM)", 0, 3000, 2200)
    spin_type = st.radio("회전 방향 (구종)", ["백스핀 (포심 패스트볼)", "톱스핀 (커브볼)", "무회전 (너클볼/포크볼)"])
    
    st.header("환경 설정 (공기 밀도)")
    st.markdown("해수면 기준 1.225 / 쿠어스 필드(고지대) 약 1.000")
    rho = st.slider("공기 밀도 (kg/m³)", 0.8, 1.3, 1.225, 0.005)

# --- 궤적 계산 ---
x_val, y_val = calculate_trajectory(v0_ms, 1.0, spin_rpm, rho, spin_type)
x_base, y_base = calculate_trajectory(v0_ms, 1.0, 0, rho, "무회전") # 비교용 무회전 궤적

# --- Plotly 애니메이션 그래프 구성 ---
fig = go.Figure()

# 1. 무회전 비교선 추가 (고정된 회색 점선)
fig.add_trace(go.Scatter(x=x_base, y=y_base, mode='lines', 
                         line=dict(color='lightgray', dash='dash', width=2), 
                         name='무회전 궤적 (비교용)'))

# 2. 실제 궤적 (파란색 선) 및 야구공 (빨간 점) 껍데기 생성
fig.add_trace(go.Scatter(x=[x_val[0]], y=[y_val[0]], mode='lines', 
                         line=dict(color='blue', width=3), name=spin_type))
fig.add_trace(go.Scatter(x=[x_val[0]], y=[y_val[0]], mode='markers', 
                         marker=dict(color='red', size=12), name='야구공'))

# 3. 애니메이션 프레임 생성 (공이 날아가는 과정)
frames = []
for i in range(0, len(x_val), 2): # 부드러운 재생을 위해 2스텝 단위로 프레임 생성
    frames.append(go.Frame(
        data=[
            go.Scatter(x=x_base, y=y_base), # 무회전 선 (유지)
            go.Scatter(x=x_val[:i+1], y=y_val[:i+1]), # 투구 궤적 선 그려짐
            go.Scatter(x=[x_val[i]], y=[y_val[i]])  # 야구공 위치 이동
        ]
    ))
fig.frames = frames

# 4. 레이아웃 및 플레이 버튼 디자인
fig.update_layout(
    xaxis=dict(range=[0, 20], title="투구 거리 (m)"),
    yaxis=dict(range=[0, 3], title="높이 (m)"),
    height=600,
    hovermode=False,
    updatemenus=[dict(
        type="buttons",
        showactive=False,
        x=0.1, y=-0.15,
        xanchor="right", yanchor="top",
        buttons=[dict(label="▶ 투구 시작!",
                      method="animate",
                      args=[None, dict(frame=dict(duration=20, redraw=True), 
                                       transition=dict(duration=0),
                                       fromcurrent=True)])]
    )]
)

# 홈플레이트 위치 표시
fig.add_vline(x=18.44, line_width=2, line_dash="dash", line_color="green", 
              annotation_text="홈플레이트 (18.44m)", annotation_position="top left")

st.plotly_chart(fig, use_container_width=True)
