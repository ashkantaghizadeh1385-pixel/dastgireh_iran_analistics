import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai

# API Config
GOOGLE_API_KEY = "YOUR_GEMINI_API_KEY" 
if GOOGLE_API_KEY != "YOUR_GEMINI_API_KEY":
    genai.configure(api_key=GOOGLE_API_KEY)

# Page Settings
st.set_page_config(page_title="Dastgireh Iran BI", layout="wide")
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏢 پلتفرم هوش تجاری دستگیره ایران</h1>", unsafe_allow_html=True)
st.write("---")

# Sidebar Menu
st.sidebar.header("📁 منوی دسترسی")
department = st.sidebar.selectbox(
    "بخش مورد نظر را انتخاب کنید:",
    ["🛒 فروش استوک و رسوب", "🏢 فروش پروژه‌ای", "🚪 بخش درب‌سازی"]
)

st.title(f"📊 {department}")

# File Uploader
uploaded_file = st.file_uploader(f"لطفاً فایل اکسل (شیت مربوط به {department}) را آپلود کنید", type=["xlsx"])

if uploaded_file is not None:
    try:
        # خواندن داده‌ها از سطر دوم (چون سطر اول تایتل های غیرمرتبط دارد)
        df = pd.read_excel(uploaded_file, skiprows=1)
        df.columns = [str(c).strip() for c in df.columns] 
        
        # پاک‌سازی داده‌های خالی بر اساس ستون اصلی کالا
        if 'عنوان كالا' in df.columns:
            df = df.dropna(subset=['عنوان كالا'])
        else:
            st.error("⚠️ ستون 'عنوان كالا' در این فایل پیدا نشد! لطفاً فایل صحیح را آپلود کنید.")
            st.stop()
            
        st.subheader("📋 سطر‌های ابتدایی فایل بارگذاری شده")
        show_cols = [c for c in ['عنوان كالا', 'کارشناس فروش', 'مشتریان', 'تعداد فروخته شده(کارتن)', 'باقی مانده'] if c in df.columns]
        st.dataframe(df[show_cols].head(5), use_container_width=True)
        st.write("---")

        # ==========================================
        # 1. STOCK & ROSOOB DEPARTMENT
        # ==========================================
        if "استوک" in department or "رسوب" in department:
            st.subheader("🎯 تحلیل ماتریس فروش و پتانسیل‌یابی کالاها")
            
            # عددی کردن ستون‌ها برای محاسبات ایمن
            df['تعداد فروخته شده(کارتن)'] = pd.to_numeric(df['تعداد فروخته شده(کارتن)'], errors='coerce').fillna(0)
            df['مجموع قیمت فروش'] = pd.to_numeric(df['مجموع قیمت فروش'], errors='coerce').fillna(0)
            df['درصد تخفیف'] = pd.to_numeric(df['درصد تخفیف'], errors='coerce').fillna(0)
            df['باقی مانده'] = pd.to_numeric(df['باقی مانده'], errors='coerce').fillna(0)
            
            # الف) ردیابی کالا
            st.markdown("### 🔍 ردیابی کالاها:")
            selected_product = st.selectbox("انتخاب عنوان کالا:", df['عنوان كالا'].unique())
            
            product_data = df[df['عنوان كالا'] == selected_product]
            st.write(f"📊 وضعیت بازار برای: **{selected_product}**")
            valid_cols = [c for c in ['کارشناس فروش', 'مشتریان', 'تعداد فروخته شده(کارتن)', 'باقی مانده'] if c in product_data.columns]
            st.dataframe(product_data[valid_cols], use_container_width=True)
            
            # ب) پیشنهادات هوشمند سیستم توصیه‌گر
            st.markdown("### 💡 پیشنهادات هوشمند سیستم هوش تجاری (BI)")
            col_rec1, col_rec2 = st.columns(2)
            
            with col_rec1:
                st.info("🔥 **پیشنهاد تمرکز فروش کالا:**")
                best_sellers = df[df['تعداد فروخته شده(کارتن)'] > 0].sort_values('تعداد فروخته شده(کارتن)', ascending=False)
                if not best_sellers.empty:
                    count = 0
                    for idx, row in best_sellers.iterrows():
                        if count >= 3: break
                        st.write(f"🔹 کالا **{row['عنوان كالا']}** توسط **{row.get('کارشناس فروش', 'کارشناسان')}** خوب فروخته شده؛ بقیه از روش او الگو بگیرند.")
                        count += 1
                else:
                    st.write("داده‌ای برای فروش‌های موفق در این کالا ثبت نشده است.")
            
            with col_rec2:
                st.warning("🛍️ **کالاهای رسوب شده در انبار (فرصت فروش):**")
                high_stock = df[df['باقی مانده'] > 5].sort_values('باقی مانده', ascending=False)
                if not high_stock.empty:
                    count = 0
                    for idx, row in high_stock.iterrows():
                        if count >= 3: break
                        st.write(f"🔸 کالا **{row['عنوان كالا']}** تعداد **{row['باقی مانده']} کارتن** رسوب دارد؛ پیشنهاد آفر ویژه به مشتریان هدف.")
                        count += 1

            # ج) رتبه‌بندی کارشناسان
            if 'کارشناس فروش' in df.columns:
                st.write("---")
                st.subheader("🥇 رتبه‌بندی عملکرد کارشناسان فروش")
                
                agent_perf = df.groupby('کارشناس فروش').agg({
                    'مجموع قیمت فروش': 'sum',
                    'تعداد فروخته شده(کارتن)': 'sum',
                    'درصد تخفیف': 'mean'
                }).reset_index()
                
                if agent_perf['مجموع قیمت فروش'].max() > 0:
                    agent_perf['نمره عملکرد (از ۱۰۰)'] = ((agent_perf['مجموع قیمت فروش'] / agent_perf['مجموع قیمت فروش'].max() * 80) + (20 - agent_perf['درصد تخفیف'])).round(1)
                else:
                    agent_perf['نمره عملکرد (از ۱۰۰)'] = 0
                    
                st.dataframe(agent_perf.sort_values('نمره عملکرد (از ۱۰۰)', ascending=False), use_container_width=True)

        # ==========================================
        # 2. PROJECT AND DOOR DEPARTMENT
        # ==========================================
        else:
            st.subheader("🏢 تحلیل وضعیت پروژه‌ها و پیگیری‌ها")
            st.info("این بخش برای تحلیل متن‌کاوی توضیحات پروژه‌ها و ویزیت‌ها در نظر گرفته شده است. لطفاً فایل دپارتمان پروژه را آپلود کنید.")

        # ==========================================
        # 3. AI ANALYSIS
        # ==========================================
        st.write("---")
        st.subheader("🤖 گزارش تحلیل هوشمند مدیریتی (Gemini)")
        
        ai_cols = [c for c in ['عنوان كالا', 'مشتریان', 'کارشناس فروش', 'تعداد فروخته شده(کارتن)', 'باقی مانده'] if c in df.columns]
        ai_data = df[ai_cols].head(15).to_string()
        
        prompt = f"""
        شما مشاور ارشد سیستم‌های BI شرکت دستگیره ایران هستید. داده‌های زیر مربوط به بخش {department} است.
        با توجه به نام کالاها، مشتریان و باقی‌مانده‌ها یک گزارش دقیق ارائه دهید:
        ۱. کدام دستگیره‌ها بیشترین رسوب (باقی‌مانده) را دارند و برای فروختنشان چه پیشنهادی مناسب است؟
        ۲. عملکرد کارشناسان فروش (مثل کمالی، سلطانی و...) را تحلیل کنید.
        
        داده‌ها:
        {ai_data}
        """
        
        if GOOGLE_API_KEY == "YOUR_GEMINI_API_KEY":
            st.info("💡 فایل شما با موفقیت پردازش شد. برای فعال‌سازی بخش هوش مصنوعی و متن‌کاوی زنده، کلید API را ست کنید.")
        else:
            with st.spinner("🤖 هوش مصنوعی در حال تحلیل مدل‌های رسوب..."):
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                st.markdown(response.text)

    except Exception as e:
        st.error(f"❌ خطای فنی در پردازش فایل: {e}")
