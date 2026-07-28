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

def calculate_trajectory_with_forces(v0, theta_deg, spin_rpm, rho, spin_type):
    """오일러 방법을 사용한 2D 궤적 계산기 (힘 벡터 반환)"""
    dt = 0.005 # 더 부드러운 애니메이션을 위해 dt를 줄임
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
        
    # 모든 리스트를 빈 상태로 시작하여 길이를 완벽하게 일치시킵니다.
    x_traj, y_traj = [], []
    Fg_traj, Fd_traj, Fm_traj, v_traj = [], [], [], []
    
    while y > 0 and x < 20: 
        # 1. 현재 위치 저장
        x_traj.append(x)
        y_traj.append(y)
        
        v = np.sqrt(vx**2 + vy**2)
        v_traj.append((vx, vy))

        # 2. 중력 (항상 아래로 일정)
        F_g = (0, -m * g)
        Fg_traj.append(F_g)
        
        # 3. 공기 저항력 (이동 반대 방향)
        Fd_mag = 0.5 * rho * v**2 * Cd * A
        Fd = (-Fd_mag * (vx / v) if v > 0 else 0, -Fd_mag * (vy / v) if v > 0 else 0)
        Fd_traj.append(Fd)
        
        # 4. 마그누스 힘 (회전 방향에 따라 수직으로 작용)
        Fm_mag = 0.5 * rho * v**2 * (Cl_factor * (r * omega / v)) * A if v > 0 else 0
        if spin_type == "백스핀 (포심 패스트볼)":
            Fm = (-Fm_mag * (vy / v) if v > 0 else 0, Fm_mag * (vx / v) if v > 0 else 0)
        elif spin_type == "톱스핀 (커브볼)":
            Fm = (Fm_mag * (vy / v) if v > 0 else 0, -Fm_mag * (vx / v) if v > 0 else 0)
        else:
            Fm = (0, 0)
        Fm_traj.append(Fm)
        
        # 5. 가속도 적용 및 다음 위치(x, y) 업데이트
        ax = (Fd[0] + Fm[0]) / m
        ay = (F_g[1] + Fd[1] + Fm[1]) / m
        
        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt
        
    return x_traj, y_traj, Fg_traj, Fd_traj, Fm_traj, v_traj

# --- Streamlit UI 구성 ---
st.set_page_config(page_title="야구공 궤적 및 힘 벡터 시뮬레이터", layout="wide")
st.title("⚾ 야구공 투구 궤적 및 힘 벡터 시뮬레이터 (애니메이션)")
st.markdown("왼쪽에서 투구 설정을 맞춘 뒤, 그래프 아래의 **'▶ 투구 시작!'** 버튼을 눌러 공이 날아가는 궤적과 힘 벡터의 변화를 확인하세요.")
st.markdown("💡 **도움말:** 화살표는 각 힘의 방향과 크기를 나타냅니다. 구속과 회전수를 바꾸면 화살표 길이가 어떻게 달라지는지 관찰해 보세요!")

with st.sidebar:
    st.header("투구 설정")
    v0_kmh = st.slider("구속 (km/h)", 100, 160, 145)
    v0_ms = v0_kmh / 3.6 
    
    spin_rpm = st.slider("회전수 (RPM)", 0, 3000, 2200)
    spin_type = st.radio("회전 방향 (구종)", ["백스핀 (포심 패스트볼)", "톱스핀 (커브볼)", "무회전 (너클볼/포크볼)"])
    
    st.header("환경 설정 (공기 밀도)")
    st.markdown("해수면 기준 1.225 / 쿠어스 필드(고지대) 약 1.000")
    rho = st.slider("공기 밀도 (kg/m³)", 0.8, 1.3, 1.225, 0.005)

    st.header("화살표 설정")
    arrow_scale = st.slider("화살표 크기 스케일 (힘)", 0.1, 2.0, 1.0, 0.1)

# --- 궤적 계산 ---
x_val, y_val, Fg_val, Fd_val, Fm_val, v_val = calculate_trajectory_with_forces(v0_ms, 1.0, spin_rpm, rho, spin_type)
x_base, y_base, _, _, _, _ = calculate_trajectory_with_forces(v0_ms, 1.0, 0, rho, "무회전") # 비교용 무회전 궤적

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

# 3. 힘 벡터 화살표 껍데기 생성 (모드: lines+markers)
# 중력 (녹색)
fig.add_trace(go.Scatter(x=[x_val[0], x_val[0] + Fg_val[0][0] * arrow_scale], y=[y_val[0], y_val[0] + Fg_val[0][1] * arrow_scale],
                         mode='lines+markers', line=dict(color='green', width=2), 
                         marker=dict(symbol='triangle-up', size=10, angleref='previous'), name='중력 (Gravity)'))
# 공기 저항력 (빨간색)
fig.add_trace(go.Scatter(x=[x_val[0], x_val[0] + Fd_val[0][0] * arrow_scale], y=[y_val[0], y_val[0] + Fd_val[0][1] * arrow_scale],
                         mode='lines+markers', line=dict(color='red', width=2), 
                         marker=dict(symbol='triangle-up', size=10, angleref='previous'), name='공기 저항력 (Drag Force)'))
# 마그누스 힘 (보라색)
fig.add_trace(go.Scatter(x=[x_val[0], x_val[0] + Fm_val[0][0] * arrow_scale], y=[y_val[0], y_val[0] + Fm_val[0][1] * arrow_scale],
                         mode='lines+markers', line=dict(color='purple', width=2), 
                         marker=dict(symbol='triangle-up', size=10, angleref='previous'), name='마그누스 힘 (Magnus Force)'))

# 4. 애니메이션 프레임 생성 (공이 날아가는 과정)
frames = []
interval = 5 # 성능을 위해 5스텝 간격으로 프레임 생성
for i in range(0, len(x_val), interval): 
    # 현재 위치에서의 힘 벡터 업데이트 데이터 구성
    frames.append(go.Frame(
        data=[
            go.Scatter(x=x_base, y=y_base), # 무회전 선 (유지)
            go.Scatter(x=x_val[:i+1], y=y_val[:i+1]), # 투구 궤적 선 그려짐
            go.Scatter(x=[x_val[i]], y=[y_val[i]]),  # 야구공 위치 이동
            # 중력 화살표 업데이트 (선+머리)
            go.Scatter(x=[x_val[i], x_val[i] + Fg_val[i][0] * arrow_scale], y=[y_val[i], y_val[i] + Fg_val[i][1] * arrow_scale]),
            # 공기 저항력 화살표 업데이트 (선+머리)
            go.Scatter(x=[x_val[i], x_val[i] + Fd_val[i][0] * arrow_scale], y=[y_val[i], y_val[i] + Fd_val[i][1] * arrow_scale]),
            # 마그누스 힘 화살표 업데이트 (선+머리)
            go.Scatter(x=[x_val[i], x_val[i] + Fm_val[i][0] * arrow_scale], y=[y_val[i], y_val[i] + Fm_val[i][1] * arrow_scale])
        ]
    ))
fig.frames = frames

# 5. 레이아웃 및 플레이 버튼 디자인
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
                      args=[None, dict(frame=dict(duration=dt*interval*1000, redraw=True), 
                                       transition=dict(duration=0),
                                       fromcurrent=True)])]
    )]
)

# 홈플레이트 위치 표시
fig.add_vline(x=18.44, line_width=2, line_dash="dash", line_color="green", 
              annotation_text="홈플레이트 (18.44m)", annotation_position="top left")

st.plotly_chart(fig, use_container_width=True)
