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

def calculate_trajectory_3d(v0, theta_deg, spin_rpm, rho, spin_type):
    """3D 벡터 외적을 활용한 정교한 3차원 궤적 계산기 (화살표용 힘 벡터 저장 생략)"""
    theta = np.radians(theta_deg)
    
    pos = np.array([0.0, 2.0, 0.0])
    vel = np.array([v0 * np.cos(theta), v0 * np.sin(theta), 0.0])
    
    omega_mag = spin_rpm * (2 * np.pi / 60)
    if "백스핀" in spin_type:
        omega = np.array([0.0, 0.0, omega_mag]) 
    elif "톱스핀" in spin_type:
        omega = np.array([0.0, 0.0, -omega_mag]) 
    elif "사이드스핀" in spin_type:
        omega = np.array([0.0, omega_mag, 0.0]) 
    else:
        omega = np.array([0.0, 0.0, 0.0])
        
    x_t, y_t, z_t = [], [], []
    
    while pos[1] > 0 and pos[0] < 20: 
        x_t.append(pos[0])
        y_t.append(pos[1])
        z_t.append(pos[2])
        
        v_mag = np.linalg.norm(vel)
        
        F_g = np.array([0.0, -m * g, 0.0])
        
        F_d = np.array([0.0, 0.0, 0.0])
        if v_mag > 0:
            Fd_mag = 0.5 * rho * v_mag**2 * Cd * A
            F_d = -Fd_mag * (vel / v_mag)
        
        F_m = np.array([0.0, 0.0, 0.0])
        if v_mag > 0 and np.linalg.norm(omega) > 0:
            cross_product = np.cross(omega, vel)
            F_m = 0.5 * rho * A * Cl_factor * r * cross_product
        
        F_net = F_g + F_d + F_m
        acc = F_net / m
        
        vel += acc * dt
        pos += vel * dt
        
    return x_t, y_t, z_t

# --- Streamlit UI 구성 ---
st.set_page_config(page_title="3D 야구공 물리 시뮬레이터", layout="wide")
st.title("⚾ 3D 야구공 궤적 시뮬레이터")
st.markdown("선택한 구종에 따른 물리적 특성을 확인하고, 3D 그래프를 이리저리 돌려보며 궤적을 관찰하세요!")

with st.sidebar:
    st.header("투구 설정")
    v0_kmh = st.slider("구속 (km/h)", 100, 160, 145)
    v0_ms = v0_kmh / 3.6 
    
    spin_rpm = st.slider("회전수 (RPM)", 0, 3000, 2200)
    spin_type = st.radio("회전 방향 (구종 선택)", [
        "백스핀 (포심 패스트볼)", 
        "톱스핀 (커브볼)", 
        "사이드스핀 (슬라이더)", 
        "무회전 (너클볼/포크볼)"
    ])
    
    st.header("환경 설정 (공기 밀도)")
    rho = st.slider("공기 밀도 (kg/m³)", 0.8, 1.3, 1.225, 0.005)

# --- 구종별 물리적 설명 UI (새로 추가된 부분) ---
st.markdown("---")
st.subheader(f"💡 {spin_type}의 물리적 특성")
col1, col2, col3 = st.columns(3)

if "백스핀" in spin_type:
    col1.info("**🖐️ 1. 공을 쥔 모습 (그립)**\n\n검지와 중지를 말발굽 모양의 실밥 위에 넓고 수직으로 교차하게 얹어 쥡니다. (포심 그립) 강하게 채서 뒤로 도는 회전을 만듭니다.")
    col2.success("**🌪️ 2. 마그누스 효과 방향**\n\n⬆️ **위쪽 (양력)**\n\n공 위쪽의 공기 압력이 낮아져 위로 떠오르려는 힘이 발생합니다.")
    col3.warning("**⚙️ 3. 종합 작용 힘**\n\n⬇️ 중력 ➖ ⬆️ 마그누스 힘\n\n마그누스 힘이 중력을 상쇄시킵니다. 타자 눈에는 공이 떨어지지 않고 떠오르는(라이징) 것처럼 보입니다.")

elif "톱스핀" in spin_type:
    col1.info("**🖐️ 1. 공을 쥔 모습 (그립)**\n\n중지를 실밥에 나란히 대고 감싸 쥡니다. 던질 때 손목을 비틀어 마치 문고리를 돌리듯 위에서 아래로 회전을 줍니다.")
    col2.success("**🌪️ 2. 마그누스 효과 방향**\n\n⬇️ **아래쪽 (하향력)**\n\n공 아래쪽의 공기 압력이 낮아져 아래로 짓누르는 힘이 발생합니다.")
    col3.warning("**⚙️ 3. 종합 작용 힘**\n\n⬇️ 중력 ➕ ⬇️ 마그누스 힘\n\n중력과 마그누스 힘이 같은 방향으로 합쳐져, 타석 앞에서 폭포수처럼 급격히 뚝 떨어집니다.")

elif "사이드스핀" in spin_type:
    col1.info("**🖐️ 1. 공을 쥔 모습 (그립)**\n\n검지와 중지를 실밥 한쪽으로 약간 치우치게 잡고, 공을 채는 순간 팽이를 돌리듯 손가락으로 측면 회전을 가합니다.")
    col2.success("**🌪️ 2. 마그누스 효과 방향**\n\n➡️ **수평 방향 (측면력)**\n\n회전하는 방향의 측면 압력이 낮아져 옆으로 밀어내는 힘이 발생합니다.")
    col3.warning("**⚙️ 3. 종합 작용 힘**\n\n⬇️ 중력 ➕ ➡️ 마그누스 힘\n\n아래로 떨어지는 동시에 수평으로 강하게 밀려 타자 바깥쪽(우투수 기준)으로 날카롭게 휘어져 나갑니다.")

else:
    col1.info("**🖐️ 1. 공을 쥔 모습 (그립)**\n\n손가락 관절로 공을 찍어 잡거나(너클볼), 검지와 중지를 포크처럼 넓게 벌려 잡아(포크볼) 손가락의 채는 힘(마찰)을 극단적으로 줄입니다.")
    col2.success("**🌪️ 2. 마그누스 효과 방향**\n\n❌ **없음 (또는 매우 약함)**\n\n회전이 부족하여 압력 차이가 발생하지 않습니다.")
    col3.warning("**⚙️ 3. 종합 작용 힘**\n\n⬇️ 중력 온전히 작용\n\n양력이 없어 포물선을 그리며 떨어지거나, 불규칙한 실밥 저항에 의해 지그재그로 흔들립니다.")

st.markdown("---")

# --- 궤적 계산 ---
x_val, y_val, z_val = calculate_trajectory_3d(v0_ms, 1.0, spin_rpm, rho, spin_type)
x_base, y_base, z_base = calculate_trajectory_3d(v0_ms, 1.0, 0, rho, "무회전") 

# --- Plotly 3D 애니메이션 구성 (화살표 제거) ---
fig = go.Figure()

# 1. 무회전 비교선 추가
fig.add_trace(go.Scatter3d(x=x_base, y=z_base, z=y_base, mode='lines', 
                           line=dict(color='lightgray', dash='dash', width=4), name='무회전 궤적'))

# 2. 실제 궤적 선 추가
fig.add_trace(go.Scatter3d(x=[x_val[0]], y=[z_val[0]], z=[y_val[0]], mode='lines', 
                           line=dict(color='blue', width=4), name=spin_type))
                           
# 3. 야구공 마커 추가
fig.add_trace(go.Scatter3d(x=[x_val[0]], y=[z_val[0]], z=[y_val[0]], mode='markers', 
                           marker=dict(color='black', size=5), name='야구공'))

# 4. 애니메이션 프레임 생성
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
        camera=dict(
            eye=dict(x=2.5, y=-1.5, z=0.8) 
        )
    ),
    height=600,
    margin=dict(l=0, r=0, b=80, t=10), 
    showlegend=True,
    legend=dict(x=0, y=1, bgcolor='rgba(255,255,255,0.7)'),
    updatemenus=[dict(
        type="buttons",
        showactive=False,
        direction="left",
        x=0.5, y=-0.1,
        xanchor="center", yanchor="top",
        buttons=[
            dict(label="▶ 재생",
                 method="animate",
                 args=[None, dict(frame=dict(duration=80, redraw=True), transition=dict(duration=0), fromcurrent=True)]),
            dict(label="⏸ 일시정지",
                 method="animate",
                 args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))])
        ]
    )]
)

st.plotly_chart(fig, use_container_width=True)
