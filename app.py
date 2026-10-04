import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Thailand Wood Industry Dashboard",
    page_icon="🪵",
    layout="wide"
)

# โหลดข้อมูลพร้อม Cache
@st.cache_data
def load_all_data():
    df_exp = pd.read_csv("wood_export_cleaned.csv")
    df_prod = pd.read_csv("wood_products_detailed_cleaned.csv")
    try:
        df_fac = pd.read_csv("dim_wood_factories.csv")
    except Exception:
        df_fac = pd.DataFrame()
    return df_exp, df_prod, df_fac

df_export, df_products, df_factories = load_all_data()

st.title("🪵 ระบบแดชบอร์ดวิเคราะห์อุตสาหกรรมไม้ไทย (Wood Industry Dashboard)")
st.caption("วิเคราะห์สถิติการค้าระหว่างประเทศตามพิกัดศุลกากร (ปี 2563 - 2568) และโครงสร้างอุตสาหกรรมแปรรูปไม้")

# แบ่งเป็น 3 แท็บตาม Roadmap
tab1, tab2, tab3 = st.tabs([
    "🌐 Tab 1: ตลาดส่งออกรายประเทศ (Export Markets)",
    "📦 Tab 2: สัดส่วนสินค้าและราคา (Product & Price Trends)",
    "🏭 Tab 3: ที่ตั้งโรงงานในประเทศ (Domestic Footprint)"
])

# ==============================================================================
# TAB 1: ตลาดส่งออกรายประเทศ และช่วงปี 2563 - 2568
# ==============================================================================
with tab1:
    st.subheader("วิเคราะห์การส่งออกรายประเทศและแนวโน้มช่วงปี 2563 - 2568")
    
    # ส่วนควบคุม Filter (ช่วงปี และ ประเทศ)
    f_col1, f_col2 = st.columns([1, 1.2])
    
    with f_col1:
        year_range = st.slider(
            "📅 เลือกช่วงปีงบประมาณ (พ.ศ.):",
            min_value=2563,
            max_value=2568,
            value=(2563, 2568),
            step=1,
            key="slider_years"
        )
        
    top_country_list = df_export.groupby("country")["export_value_thb"].sum().sort_values(ascending=False).index.tolist()
    country_options = ["ทุกประเทศ (ภาพรวมตลาดโลก)"] + top_country_list
    
    with f_col2:
        selected_country = st.selectbox(
            "🌍 เลือกประเทศปลายทางที่ต้องการเจาะลึก:",
            options=country_options,
            index=0,
            key="sb_country"
        )
        
    start_year, end_year = year_range
    df_exp_filtered = df_export[
        (df_export["year_be"] >= start_year) & 
        (df_export["year_be"] <= end_year)
    ].copy()
    
    st.divider()
    
    # กรณีเลือก "ทุกประเทศ (ภาพรวมตลาดโลก)"
    if selected_country == "ทุกประเทศ (ภาพรวมตลาดโลก)":
        total_period_val = df_exp_filtered["export_value_thb"].sum()
        latest_val = df_export[df_export["year_be"] == end_year]["export_value_thb"].sum()
        
        prev_val = df_export[df_export["year_be"] == (end_year - 1)]["export_value_thb"].sum() if (end_year - 1) in df_export["year_be"].values else None
        yoy_val = ((latest_val - prev_val) / prev_val * 100) if prev_val and prev_val > 0 else None
        
        top_dest = df_export[df_export["year_be"] == end_year].sort_values(by="export_value_thb", ascending=False).iloc[0]
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric(f"มูลค่าส่งออกรวม ({start_year} - {end_year})", f"{total_period_val / 1e9:,.2f} พันล้านบาท")
        kpi2.metric(f"มูลค่าปีล่าสุด ({end_year})", f"{latest_val / 1e9:,.2f} พันล้านบาท", f"{yoy_val:.2f}% YoY" if yoy_val else None)
        kpi3.metric(f"ตลาดเบอร์ 1 ปี {end_year}", f"{top_dest['country']}", f"{(top_dest['export_value_thb']/latest_val)*100:.1f}% ของยอดรวม")
        
        c1, c2 = st.columns([1.1, 1])
        with c1:
            st.markdown(f"**🏆 10 ประเทศคู่ค้าส่งออกสูงสุด (สะสม {start_year} - {end_year})**")
            top10 = df_exp_filtered.groupby("country")["export_value_thb"].sum().reset_index().sort_values(by="export_value_thb", ascending=False).head(10)
            fig_bar = px.bar(
                top10, x="export_value_thb", y="country", orientation="h",
                color="export_value_thb", color_continuous_scale="Blues",
                labels={"export_value_thb": "มูลค่ารวม (บาท)", "country": "ประเทศ"},
                text_auto=".2s"
            )
            fig_bar.update_layout(yaxis={"autorange": "reversed"}, coloraxis_showscale=False, height=420)
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with c2:
            st.markdown(f"**📈 แนวโน้มมูลค่าส่งออกรวมรายปี (พ.ศ. {start_year} - {end_year})**")
            yearly_trend = df_exp_filtered.groupby("year_be")["export_value_thb"].sum().reset_index()
            fig_line = px.line(
                yearly_trend, x="year_be", y="export_value_thb", markers=True,
                labels={"year_be": "ปี พ.ศ.", "export_value_thb": "มูลค่า (บาท)"}
            )
            fig_line.update_traces(line_color="#1f77b4", line_width=3)
            fig_line.update_layout(height=420)
            st.plotly_chart(fig_line, use_container_width=True)
            
    # กรณีเจาะลึกเฉพาะรายประเทศ
    else:
        df_target = df_exp_filtered[df_exp_filtered["country"] == selected_country].copy()
        target_total = df_target["export_value_thb"].sum()
        
        target_latest = df_target[df_target["year_be"] == end_year]["export_value_thb"].sum() if not df_target[df_target["year_be"] == end_year].empty else 0
        target_prev = df_export[(df_export["country"] == selected_country) & (df_export["year_be"] == (end_year - 1))]["export_value_thb"].sum()
        yoy_target = ((target_latest - target_prev) / target_prev * 100) if target_prev > 0 else None
        
        world_period = df_exp_filtered["export_value_thb"].sum()
        share_target = (target_total / world_period * 100) if world_period > 0 else 0
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric(f"มูลค่าส่งออกไป {selected_country} รวม ({start_year} - {end_year})", f"{target_total / 1e9:,.2f} พันล้านบาท")
        kpi2.metric(f"มูลค่าปี {end_year}", f"{target_latest / 1e9:,.2f} พันล้านบาท", f"{yoy_target:.2f}% YoY" if yoy_target else None)
        kpi3.metric("สัดส่วนในตลาดส่งออกไทย", f"{share_target:.2f}%", f"จากทั้งหมด {world_period/1e9:,.1f} พันล้านบาท")
        
        c1, c2 = st.columns([1.1, 1])
        with c1:
            st.markdown(f"**📈 แนวโน้มมูลค่าส่งออกไป {selected_country} (พ.ศ. {start_year} - {end_year})**")
            fig_target_line = px.bar(
                df_target, x="year_be", y="export_value_thb",
                labels={"year_be": "ปี พ.ศ.", "export_value_thb": "มูลค่า (บาท)"},
                color="export_value_thb", color_continuous_scale="Teal",
                text_auto=".2s"
            )
            fig_target_line.update_layout(coloraxis_showscale=False, height=420)
            st.plotly_chart(fig_target_line, use_container_width=True)
            
        with c2:
            st.markdown(f"**📦 สินค้าหลักที่ส่งออกไป {selected_country} (จาก 4 เสาหลัก)**")
            df_prod_country = df_products[
                (df_products["country"] == selected_country) &
                (df_products["year_be"] >= start_year) &
                (df_products["year_be"] <= end_year)
            ].groupby("product_th")["export_value_thb"].sum().reset_index()
            
            if not df_prod_country.empty and df_prod_country["export_value_thb"].sum() > 0:
                fig_prod_c = px.pie(
                    df_prod_country, names="product_th", values="export_value_thb", hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_prod_c.update_traces(textinfo="percent+label")
                fig_prod_c.update_layout(height=420)
                st.plotly_chart(fig_prod_c, use_container_width=True)
            else:
                st.info(f"ไม่พบข้อมูลสินค้า 4 เสาหลักส่งออกไป {selected_country} หรือส่งออกในหมวดอื่น")

# ==============================================================================
# TAB 2: สัดส่วนสินค้าและราคา (Product & Price Trends)
# ==============================================================================
with tab2:
    st.subheader("เจาะลึก 4 กลุ่มผลิตภัณฑ์หลักและแนวโน้มราคาต่อหน่วย (ปี 2563 - 2568)")
    
    y_select_tab2 = st.slider("📅 เลือกช่วงปีสำหรับเปรียบเทียบ:", 2563, 2568, (2563, 2568), key="slider_t2")
    df_p_filtered = df_products[
        (df_products["year_be"] >= y_select_tab2[0]) & 
        (df_products["year_be"] <= y_select_tab2[1])
    ]
    
    c_left, c_right = st.columns([1, 1.1])
    
    with c_left:
        st.markdown(f"**🥧 สัดส่วนมูลค่าส่งออกสะสม (พ.ศ. {y_select_tab2[0]} - {y_select_tab2[1]})**")
        df_prod_share = df_p_filtered.groupby(["hs_code", "product_th"])["export_value_thb"].sum().reset_index()
        fig_pie = px.pie(
            df_prod_share, names="product_th", values="export_value_thb", hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_pie.update_traces(textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with c_right:
        st.markdown("**📊 มูลค่าการส่งออกเปรียบเทียบรายกลุ่มสินค้า (2563 - 2568)**")
        prod_trend = df_p_filtered.groupby(["year_be", "product_th"])["export_value_thb"].sum().reset_index()
        fig_stack = px.bar(
            prod_trend, x="year_be", y="export_value_thb", color="product_th",
            labels={"year_be": "ปี พ.ศ.", "export_value_thb": "มูลค่า (บาท)", "product_th": "สินค้า"},
            barmode="stack"
        )
        fig_stack.update_layout(height=400)
        st.plotly_chart(fig_stack, use_container_width=True)
        
    st.divider()
    st.markdown("### 🏷️ แนวโน้มราคาเฉลี่ยต่อหน่วย (Unit Price: บาท/กก. หรือ บาท/ลบ.ม.)")
    
    selected_hs = st.selectbox(
        "เลือกกลุ่มสินค้าเพื่อวิเคราะห์แนวโน้มราคา:",
        df_products["product_th"].unique(),
        key="sb_hs"
    )
    
    df_selected_prod = df_products[df_products["product_th"] == selected_hs]
    unit_name = df_selected_prod["unit"].iloc[0]
    
    price_by_year = df_selected_prod.groupby("year_be").agg({
        "export_value_thb": "sum",
        "quantity": "sum"
    }).reset_index()
    price_by_year["avg_unit_price"] = price_by_year["export_value_thb"] / price_by_year["quantity"]
    
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(
        x=price_by_year["year_be"], y=price_by_year["avg_unit_price"],
        mode="lines+markers+text",
        text=price_by_year["avg_unit_price"].apply(lambda v: f"{v:,.2f}"),
        textposition="top center",
        name=f"ราคาเฉลี่ย (บาทต่อ {unit_name})",
        line=dict(color="#d62728", width=3)
    ))
    fig_price.update_layout(
        title=f"แนวโน้มราคาเฉลี่ยต่อหน่วยของ: {selected_hs} ({unit_name}) พ.ศ. 2563 - 2568",
        xaxis_title="ปี พ.ศ.", yaxis_title=f"ราคาเฉลี่ย (บาท / {unit_name})", height=380
    )
    st.plotly_chart(fig_price, use_container_width=True)

# ==============================================================================
# TAB 3: ที่ตั้งโรงงานในประเทศ (Domestic Footprint)
# ==============================================================================
with tab3:
    st.subheader("โครงสร้างโรงงานแปรรูปไม้และกำลังแรงงานในประเทศ")
    
    if df_factories.empty:
        st.warning("ไม่พบไฟล์ dim_wood_factories.csv ในระบบ กรุณาตรวจสอบตำแหน่งไฟล์")
    else:
        f_col1, f_col2, f_col3 = st.columns(3)
        f_col1.metric("จำนวนโรงงานทั้งหมด", f"{len(df_factories):,} แห่ง")
        f_col2.metric("จำนวนแรงงานในระบบรวม", f"{df_factories['workers'].sum():,} คน")
        f_col3.metric("ทุนจดทะเบียนสะสม", f"{df_factories['capital_million_thb'].sum():,.2f} ล้านบาท")
        
        st.divider()
        m_left, m_right = st.columns([1.2, 0.8])
        
        with m_left:
            st.markdown("**📍 แผนที่พิกัดโรงงานแปรรูปไม้ทั่วประเทศไทย**")
            if hasattr(px, "scatter_map"):
                fig_map = px.scatter_map(
                    df_factories, lat="latitude", lon="longitude", color="factory_type",
                    size="workers", hover_name="factory_name",
                    hover_data={"province": True, "workers": True, "scale": True, "latitude": False, "longitude": False},
                    zoom=5, center={"lat": 12.0, "lon": 100.5}, map_style="open-street-map", height=520
                )
            else:
                fig_map = px.scatter_mapbox(
                    df_factories, lat="latitude", lon="longitude", color="factory_type",
                    size="workers", hover_name="factory_name",
                    hover_data={"province": True, "workers": True, "scale": True, "latitude": False, "longitude": False},
                    zoom=5, center={"lat": 12.0, "lon": 100.5}, mapbox_style="open-street-map", height=520
                )
            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
            
        with m_right:
            st.markdown("**👥 สัดส่วนขนาดโรงงานตามจำนวนแรงงาน (Factory Scale)**")
            fig_scale = px.pie(
                df_factories, names="scale", hole=0.4, color="scale",
                color_discrete_map={
                    "ขนาดย่อม (Small)": "#98df8a",
                    "ขนาดกลาง (Medium)": "#1f77b4",
                    "ขนาดใหญ่ (Large)": "#ff7f0e"
                }
            )
            st.plotly_chart(fig_scale, use_container_width=True)
            
            st.markdown("**🏢 จำนวนโรงงานแยกตามจังหวัดสำคัญ**")
            prov_count = df_factories["province"].value_counts().reset_index()
            prov_count.columns = ["province", "count"]
            fig_prov = px.bar(
                prov_count, x="count", y="province", orientation="h",
                labels={"count": "จำนวนโรงงาน", "province": "จังหวัด"}
            )
            fig_prov.update_layout(yaxis={"autorange": "reversed"}, height=260)
            st.plotly_chart(fig_prov, use_container_width=True)