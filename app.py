import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Traktör Vites Kutusu Tasarım Yazılımı", page_icon="🚜", layout="wide")

st.title("🚜 Traktör Mekanik Hız Kutusu Tasarım Yazılımı")
st.markdown("Bu yazılım; girdiğiniz motor karakteristikleri ve tasarım sınırlarına göre, **Geometrik Kademelendirme** yöntemiyle gerekli şanzıman oranlarını otomatik olarak sentezler ve transmisyon sisteminin hareket diyagramlarını oluşturur.")

# --- SABİT TASARIM PARAMETRELERİ ---
# Hocanın isteği doğrultusunda en yüksek hız 40 km/h olarak sabitlenmiştir ve değiştirilemez.
v_hedef_max = 40.00

# --- SOL MENÜ (KULLANICI GİRDİLERİ) ---
st.sidebar.header("⚙️ 1. Motor Karakteristikleri")
N_m_min = st.sidebar.number_input("Maks. Tork Devri (Min Devir - dev/dak)", value=None, step=50, help="Örnek değer: 1350") 
N_m_max = st.sidebar.number_input("Maks. Güç Devri (Max Devir - dev/dak)", value=None, step=50, help="Örnek değer: 2300")
M_m_max = st.sidebar.number_input("Maksimum Motor Torku (Nm)", value=None, step=5, help="Örnek değer: 155")
M_m_nom = st.sidebar.number_input("Nominal Devirdeki Tork (Nm)", value=None, step=5, help="Örnek değer: 125")

st.sidebar.markdown("---")

st.sidebar.header("🎯 2. Hedef İlerleme Hızları")
sanziman_tipi = st.sidebar.radio("Traktör Şanzıman Tipi", ("Normal Şanzıman", "Sürüngen (Creeper) Vitesli"))

if sanziman_tipi == "Normal Şanzıman":
    yardim_metni = "Normal tarımsal işlemler için 1. vites alt sınırı genellikle 1.0 km/h kabul edilir."
else:
    yardim_metni = "Özel yavaş işlemler (fide dikimi vb.) için sürüngen vites alt sınırı 0.5 km/h alınır."

v_hedef_min = st.sidebar.number_input("Hedef En Düşük Hız (km/h)", value=None, format="%.2f", help=yardim_metni)

st.sidebar.markdown("---")

st.sidebar.header("⚙️ 3. Transmisyon ve Donanım")
z = st.sidebar.number_input("Toplam Vites Sayısı (z)", min_value=2, value=None, step=1, help="Örnek değer: 8")
i_diferansiyel = st.sidebar.number_input("Diferansiyel Oranı", value=None, format="%.3f", help="Örnek değer: 4.966")

cer_durumu = st.sidebar.radio("Son Redüksiyon (Cer) Dişlisi Var mı?", ("Evet, Cer Dişlisi Var", "Hayır, Cer Dişlisi Yok"))

i_cer = 1.0 # Varsayılan etkisiz eleman
if cer_durumu == "Evet, Cer Dişlisi Var":
    cer_secimi = st.sidebar.selectbox(
        "Piyasa Standartlarına Göre Cer Seçimi",
        (
            "Standart Tarla Tipi (Oran: 4.500)", 
            "Hafif / Bahçe Tipi (Oran: 3.150)", 
            "Ağır Tip / Çift Çeker (Oran: 5.250)", 
            "Ekstra Ağır Tip (Oran: 6.000)",
            "Özel Değer Gir (Manuel)"
        )
    )
    
    if cer_secimi == "Standart Tarla Tipi (Oran: 4.500)":
        i_cer = 4.500
    elif cer_secimi == "Hafif / Bahçe Tipi (Oran: 3.150)":
        i_cer = 3.150
    elif cer_secimi == "Ağır Tip / Çift Çeker (Oran: 5.250)":
        i_cer = 5.250
    elif cer_secimi == "Ekstra Ağır Tip (Oran: 6.000)":
        i_cer = 6.000
    else:
        i_cer = st.sidebar.number_input("Manuel Cer Dişlisi Oranı Girin", value=None, format="%.3f")

r_statik = st.sidebar.number_input("Lastik Statik Yarıçapı (m)", value=None, format="%.3f", help="Örnek değer: 0.510")
verim = st.sidebar.number_input("Aktarım Organları Verimi (%)", value=None, step=1.0, help="Örnek değer: 90.2")

# --- GÜVENLİK KONTROLÜ VE HESAPLAMA MOTORU ---
# Tüm girdilerin kullanıcı tarafından doldurulduğundan emin oluyoruz (Boş bırakılırsa sistem bekler)
girdiler = [N_m_min, N_m_max, M_m_max, M_m_nom, v_hedef_min, z, i_diferansiyel, r_statik, verim]
if cer_durumu == "Evet, Cer Dişlisi Var" and cer_secimi == "Özel Değer Gir (Manuel)":
    girdiler.append(i_cer)

if any(v is None for v in girdiler):
    st.info("👋 **Hoş Geldiniz!** Hesaplamaların ve analiz grafiklerinin oluşturulabilmesi için lütfen sol menüdeki boş alanları traktör ve motor verilerinize göre doldurun.")
else:
    # Verim yüzdesini ondalığa çevirme
    verim_orani = verim / 100
    i_sabit = i_diferansiyel * i_cer
    r_dinamik = r_statik * 0.91 

    # Hesaplamalar (Tersine Mühendislik)
    i_top_max = (0.377 * r_dinamik * N_m_min) / v_hedef_min
    i_top_min = (0.377 * r_dinamik * N_m_max) / v_hedef_max

    i_g_max = i_top_max / i_sabit
    i_g_min = i_top_min / i_sabit

    i_g_tot = i_g_max / i_g_min
    phi_th = i_g_tot ** (1 / (z - 1))
    devir_orani = N_m_max / N_m_min

    vitesler, oranlar = [], []
    hizlar_min, hizlar_max, hiz_farki = [], [], []
    kuvvetler_min, kuvvetler_max = [], []
    uygun_vites_sayisi = 0

    for n in range(1, int(z) + 1):
        i_n = i_g_min * (phi_th ** (z - n)) 
        i_top = i_n * i_sabit
        
        v_min = (0.377 * r_dinamik * N_m_min) / i_top 
        v_max = (0.377 * r_dinamik * N_m_max) / i_top 
        
        f_u_max = (M_m_max * i_top * verim_orani) / r_dinamik 
        f_u_min = (M_m_nom * i_top * verim_orani) / r_dinamik 
        
        vitesler.append(f"V{n}") 
        oranlar.append(round(i_n, 3))
        
        hizlar_min.append(round(v_min, 2))
        hizlar_max.append(round(v_max, 2))
        hiz_farki.append(round(v_max - v_min, 2))
        
        kuvvetler_min.append(round(f_u_min, 0))
        kuvvetler_max.append(round(f_u_max, 0))
        
        if (v_max >= 4) and (v_min <= 12):
            uygun_vites_sayisi += 1

    df = pd.DataFrame({"Vites": vitesler, "Sentezlendiği Şanzıman Oranı": oranlar, "Min Hız (km/h)": hizlar_min, "Max Hız (km/h)": hizlar_max, "Min Çekiş (N)": kuvvetler_min, "Max Çekiş (N)": kuvvetler_max})

    # --- EKRAN ÇIKTILARI VE ANALİZ ---
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📊 Transmisyon Tasarım Raporu")
        st.info(f"ℹ️ **Tasarım Standardı:** Karayolları yönetmeliği ve traktör dinamik limitleri gereği hedef en yüksek hız **{v_hedef_max:.2f} km/h** olarak değerlendirilmiş ve şanzıman üst sınırı buna göre kilitlenmiştir.")
        st.write(f"**Hesaplanan Başlangıç Oranı ($i_{{G,max}}$):** {i_g_max:.3f}")
        st.write(f"**Hesaplanan Bitiş Oranı ($i_{{G,min}}$):** {i_g_min:.3f}")
        st.write(f"**Geometrik Çarpan ($\phi_{{th}}$):** {phi_th:.3f}")
        
        if phi_th > devir_orani:
            st.error(f"🚨 **KRİTİK HATA:** Sentezlenen geometrik çarpan ({phi_th:.3f}), motor devir oranını ({devir_orani:.3f}) aşıyor! Vitesler arası hız boşluğu var.")
        else:
            st.success("✅ **ÖRTÜŞME ONAYI:** Vites geçişleri kinematik olarak kusursuz.")
            
        st.dataframe(df, use_container_width=True, height=400)

    with col2:
        tab1, tab2, tab3 = st.tabs(["🧱 Hız Kirişleri", "💪 Çevre Kuvveti - İlerleme Hızı", "📈 Hareket Diyagramı"])
        dinamik_yukseklik = max(500, int(z) * 25) 
        
        with tab1:
            fig_kiris = go.Figure()
            fig_kiris.add_trace(go.Bar(y=df["Vites"], x=hiz_farki, base=df["Min Hız (km/h)"], orientation='h', marker_color='#3498DB', hovertemplate="Min Hız: %{base} km/h<br>Max Hız: %{x} km/h<extra></extra>"))
            fig_kiris.update_layout(title="Hız Kirişleri (Vites Çalışma Aralıkları)", xaxis_title="İlerleme Hızı (km/h)", barmode='overlay', height=dinamik_yukseklik, plot_bgcolor='rgba(0,0,0,0)')
            fig_kiris.add_vrect(x0=4, x1=12, fillcolor="rgba(46, 204, 113, 0.15)", layer="below", line_width=0)
            st.plotly_chart(fig_kiris, use_container_width=True)

        with tab2:
            fig_kuvvet_hiz = go.Figure()
            for i in range(len(vitesler)):
                fig_kuvvet_hiz.add_trace(go.Scatter(
                    x=[hizlar_min[i], hizlar_max[i]], 
                    y=[kuvvetler_max[i], kuvvetler_min[i]], 
                    mode='lines+markers',
                    name=vitesler[i],
                    line=dict(width=4),
                    marker=dict(size=8),
                    hovertemplate="Hız: %{x} km/h<br>Çevre Kuvveti: %{y} N<extra></extra>"
                ))
            fig_kuvvet_hiz.update_layout(
                title="Çevre Kuvveti ve İlerleme Hızı Grafiği (Z-Diyagramı)",
                xaxis_title="İlerleme Hızı (km/h)", 
                yaxis_title="Çevre Kuvveti (N)",
                height=600, 
                plot_bgcolor='rgba(0,0,0,0)',
                hovermode="x unified"
            )
            fig_kuvvet_hiz.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
            fig_kuvvet_hiz.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
            st.plotly_chart(fig_kuvvet_hiz, use_container_width=True)

        with tab3:
            fig_hareket = go.Figure()
            fig_hareket.add_trace(go.Scatter(
                x=vitesler, y=hizlar_max, mode='lines+markers', name="Maksimum Hız Sınırı",
                line=dict(color='#E74C3C', width=3), marker=dict(size=8)
            ))
            fig_hareket.add_trace(go.Scatter(
                x=vitesler, y=hizlar_min, mode='lines+markers', name="Minimum Hız Sınırı",
                line=dict(color='#2ECC71', width=3), marker=dict(size=8)
            ))
            fig_hareket.update_layout(
                title="Hareket Diyagramı (Geometrik Hız Kademelendirmesi)",
                xaxis_title="Vites Kademeleri",
                yaxis_title="İlerleme Hızı (km/h) - Logaritmik Ölçek",
                height=600,
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis_type="log" 
            )
            fig_hareket.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
            fig_hareket.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
            st.plotly_chart(fig_hareket, use_container_width=True)
