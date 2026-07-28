import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- 물리 상수 설정 ---
m = 0.145  # 야구공 질량 (kg)
r = 0.036  # 야구공 반지름 (m)
A = np.pi * r**2  # 공 단면적 (m^2)
g = 9.81  # 중력가속도 (m/s^2)
Cd = 0.3  # 항력 계수 (간소화)
Cl_factor = 1.5  # 마그누스 양력 계수 비례상수 (간소화)

def calculate_trajectory(v0, theta_deg, spin_rpm, rho, spin_type):
    """오일러 방법을 사용한 2D 궤적 계산기"""
    dt = 0.01
    theta = np.radians(theta_deg)
    
    # 초기 상태
    x, y = 0.0, 2.0  # 투수의 릴리스 포인트 높이 (약 2m)
    vx = v0 * np.cos(theta)
    vy = v0 * np.sin(theta)
    
    # 스핀 방향 설정 (백스핀은 양수, 톱스핀은 음수)
    if spin_type == "백스핀 (포심 패스트볼)":
        omega = spin_rpm * (2 * np.pi / 60)
    elif spin_type == "톱스핀 (커브볼)":
        omega = -spin_rpm * (2 * np.pi / 60)
    else:
        omega = 0.0 # 무회전
        
    x_traj, y_traj = [x], [y]
    
    # 지면에 닿을 때까지 반복
    while y > 0 and x < 20: # 18.44m가 홈플레이트지만 여유있게 20m까지 계산
        v = np.sqrt(vx**2 + vy**2)
        
        # 항력 (Drag Force)
        Fd = 0.5 * rho * v**2 * Cd * A
        Fdx = -Fd * (vx / v)
        Fdy = -Fd * (vy / v)
        
        # 마그누스 힘 (Magnus Force)
        # 회전(omega)과 속도(v)에 비례
        Fm = 0.5 * rho * v**2 * (Cl_factor * (r * omega / v)) * A if v > 0 else 0
        Fmx = -Fm * (vy / v)  # y축 속도에 수직
        Fmy = Fm * (vx / v)   # x축 속도에 수직
        
        # 가속도 계산 (F = ma -> a = F/m)
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
st.title("⚾ 야구공 마그누스 효과 시뮬레이터")
st.markdown("투구의 회전(마그누스 힘)과 공기 밀도가 궤적에 미치는 영향을 확인해보세요!")

with st.sidebar:
    st.header("투구 설정")
    v0_kmh = st.slider("구속 (km/h)", 100, 160, 145)
    v0_ms = v0_kmh / 3.6  # m/s 변환
    
    spin_rpm = st.slider("회전수 (RPM)", 0, 3000, 2200)
    spin_type = st.radio("회전 방향 (구종)", ["백스핀 (포심 패스트볼)", "톱스핀 (커브볼)", "무회전 (너클볼/포크볼)"])
    
    st.header("환경 설정")
    st.markdown("💡 **참고:** 해수면의 공기 밀도는 약 1.225 kg/m³이며, 쿠어스 필드(고지대)는 약 1.000 kg/m³ 입니다.")
    rho = st.slider("공기 밀도 (kg/m³)", 0.8, 1.3, 1.225, 0.005)

# --- 궤적 계산 및 시각화 ---
x_val, y_val = calculate_trajectory(v0_ms, 1.0, spin_rpm, rho, spin_type)

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(x_val, y_val, label=f'{spin_type}', color='blue', linewidth=2)

# 무회전 기준선(비교용) 계산
x_base, y_base = calculate_trajectory(v0_ms, 1.0, 0, rho, "무회전")
ax.plot(x_base, y_base, '--', color='gray', label='무회전 궤적 (비교용)', alpha=0.7)

# 마운드와 홈플레이트 표시
ax.axvline(x=0, color='black', linestyle='-') # 마운드
ax.axvline(x=18.44, color='red', linestyle='--', label='홈플레이트 (18.44m)') 

ax.set_title("Pitch Trajectory (Side View)", fontsize=14)
ax.set_xlabel("Distance (m)", fontsize=12)
ax.set_ylabel("Height (m)", fontsize=12)
ax.set_xlim(0, 20)
ax.set_ylim(0, 3)
ax.legend()
ax.grid(True)

st.pyplot(fig)

st.info("그래프 해석: 백스핀을 걸면 무회전보다 덜 떨어지고(양력), 톱스핀을 걸면 급격하게 떨어집니다. 환경 설정에서 공기 밀도를 쿠어스 필드 수준(약 1.0)으로 낮추면 무브먼트가 어떻게 줄어드는지 확인해 보세요!")
