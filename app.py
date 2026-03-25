import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Traktör Vites Kutusu Analizi", page_icon="🚜", layout="wide")

st.title("🚜 Traktör Mekanik Hız Kutusu Seçim Yazılımı")
st.markdown("Bu sistem; girdiğiniz motor özelliklerine göre transmisyon oranlarını hesaplar. Her vites için motorun ideal çalışma devirleri arasındaki hız ve çekiş kuvveti aralıklarını tez verileriyle uyumlu olarak analiz eder.")

# --- SOL MENÜ (KULLANICI GİRDİLERİ) ---
st.sidebar.header("⚙️ Vites Kutusu Parametreleri")
z = st.sidebar.number_input("Toplam Vites Sayısı (z)", min_value=2, value=8, step=1)
i_g_max = st.sidebar.number_input("1. Vites Şanzıman Oranı (i_G,max)", value=12.003, format="%.3f", help="Örn: Ana Vites 1 x Takviye L")
i_g_min = st.sidebar.number_input("Son Vites Şanzıman Oranı (i_G,min)", value=0.600, format="%.3f")
i_sabit = st.sidebar.number_input("Diferansiyel ve Cer Sabit Oranı", value=22.35, format="%.2f", help="Şanzıman çıkışını tekerleğe ileten son indirgeme oranı.")
r_statik = st.sidebar.number_input("Lastik Statik Yarıçapı (m)", value=0.510, format="%.3f")

st.sidebar.markdown("---")
st.sidebar.subheader("Motor Karakteristikleri")
N_m_min = st.sidebar.number_input("Maks. Tork Devri (Min Devir)", value=1350, step=50) 
N_m_max = st.sidebar.number_input("Maks. Güç Devri (Max Devir)", value=2300, step=50)
M_m_max = st.sidebar.number_input("Maksimum Motor Torku (Nm)", value=155, step=5)
M_m_nom = st.sidebar.number_input("Nominal Devirdeki Tork (Nm)", value=125, step=5)
verim = st.sidebar.number_input("Aktarım Organları Verimi (%)", value=90.2, step=1.0) / 100

# --- HESAPLAMA MOTORU ---
r_dinamik = r_statik * 0.91 
i_g_tot = i_g_max / i_g_min
phi_th = i_g_tot ** (1 / (z - 1))
devir_orani = N_m_max / N_m_min

vitesler, oranlar = [], []
hizlar_min, hizlar_max, hiz_farki = [], [], []
kuvvetler_min, kuvvetler_max, kuvvet_farki = [], [], []
uygun_vites_sayisi = 0

for n in range(1, z + 1):
    # Denklem 6: Sadece vites kutusu oranı
    i_n = i_g_min * (phi_th ** (z - n)) 
    
    # KRİTİK DÜZELTME: Toplam Aktarım Oranı (i_top) hesabı
    i_top = i_n * i_sabit
    
    # Denklem 1: İlerleme Hızı (i_top kullanılarak)
    v_min = (0.377 * r_dinamik * N_m_min) / i_top 
    v_max = (0.377 * r_dinamik * N_m_max) / i_top 
    
    # Denklem 2: Çevre Kuvveti (i_top kullanılarak)
    f_u_max = (M_m_max * i_top * verim) / r_dinamik 
    f_u_min = (M_m_nom * i_top * verim) / r_dinamik 
    
    vitesler.append(f"V{n}") 
    oranlar.append(round(i_n, 3))
    
    hizlar_min.append(round(v_min, 2))
    hizlar_max.append(round(v_max, 2))
    hiz_farki.append(round(v_max - v_min, 2))
    
    kuvvetler_min.append(round(f_u_min, 0))
    kuvvetler_max.append(round(f_u_max, 0))
    kuvvet_farki.append(round(f_u_max - f_u_min, 0))
    
    if (v_max >= 4) and (v_min <= 12):
        uygun_vites_sayisi += 1

df = pd.DataFrame({"Vites": vitesler, "Şanzıman Oranı": oranlar, "Min Hız (km/h)": hizlar_min, "Max Hız (km/h)": hizlar_max, "Min Çekiş (N)": kuvvetler_min, "Max Çekiş (N)": kuvvetler_max})

# --- EKRAN ÇIKTILARI VE ANALİZ ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 Analiz Raporu")
    st.write(f"**Geometrik Çarpan ($\phi_{{th}}$):** {phi_th:.3f}")
    if phi_th > devir_orani:
        st.error(f"🚨 **KRİTİK HATA:** Geometrik çarpan ({phi_th:.3f}), motor devir oranını ({devir_orani:.3f}) aşıyor. Vitesler arası kopukluk var!")
    else:
        st.success("✅ **ÖRTÜŞME ONAYI:** Vitesler arası boşluk yok.")

    if uygun_vites_sayisi >= 4:
        st.success(f"✅ **ÇALIŞMA ONAYI:** 4-12 km/h aralığında {uygun_vites_sayisi} vites var.")
    else:
        st.warning(f"⚠️ **ÇALIŞMA UYARISI:** 4-12 km/h aralığında vites yetersiz.")
        
    st.dataframe(df, use_container_width=True, height=400)

with col2:
    tab1, tab2 = st.tabs(["📈 Hız Grafiği", "💪 Çekiş Kuvveti Grafiği"])
    dinamik_yukseklik = max(500, z * 25) 
    
    with tab1:
        fig_hiz = go.Figure()
        fig_hiz.add_trace(go.Bar(y=df["Vites"], x=hiz_farki, base=df["Min Hız (km/h)"], orientation='h', marker_color='#F39C12', hovertemplate="Min Hız: %{base} km/h<br>Max Hız: %{x} km/h<extra></extra>"))
        fig_hiz.update_layout(title="Hız Aralıkları", xaxis_title="İlerleme Hızı (km/h)", barmode='overlay', height=dinamik_yukseklik, plot_bgcolor='rgba(0,0,0,0)')
        fig_hiz.add_vrect(x0=4, x1=12, fillcolor="rgba(46, 204, 113, 0.15)", layer="below", line_width=0)
        st.plotly_chart(fig_hiz, use_container_width=True)

    with tab2:
        fig_kuvvet = go.Figure()
        fig_kuvvet.add_trace(go.Bar(y=df["Vites"], x=kuvvet_farki, base=df["Min Çekiş (N)"], orientation='h', marker_color='#E74C3C', hovertemplate="Min Çekiş: %{base} N<br>Max Çekiş: %{x} N<extra></extra>"))
        fig_kuvvet.update_layout(title="Çekiş Kuvveti Aralıkları", xaxis_title="Çevre Kuvveti (N)", barmode='overlay', height=dinamik_yukseklik, plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_kuvvet, use_container_width=True)