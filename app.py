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
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏢 پلتفرم هوش تجاری و تحلیل پیشرفته دستگیره ایران</h1>", unsafe_allow_html=True)
st.write("---")

# Sidebar Menu
st.sidebar.header("📁 منوی دسترسی")
department = st.sidebar.selectbox(
    "بخش مورد نظر را انتخاب کنید:",
    ["🛒 فروش استوک", "🏢 فروش پروژه‌ای", "🚪 بخش درب‌سازی"]
)

st.title(f"📊 {department}")

# File Uploader
uploaded_file = st.file_uploader(f"لطفاً فایل اکسل مربوط به {department} را آپلود کنید", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [c.strip() for c in df.columns] 

        st.subheader("📋 مشاهده داده‌های بارگذاری شده")
        st.dataframe(df.head(), use_container_width=True)
        st.write("---")

        # ==========================================
        # 1. STOCK DEPARTMENT
        # ==========================================
        if "استوک" in department:
            st.subheader("🎯 تحلیل ماتریس فروش و پتانسیل‌یابی بازار")

            df['تعداد کل (عدد)'] = df['چند کارتن خریده']  df['تعداد دست هر کارتن']

            if 'درصد تخفیف' in df.columns:
                df['مبلغ نهایی (تومان)'] = (df['تعداد کل (عدد)']  df['قیمت اش'])  (1 - df['درصد تخفیف'] / 100)
            else:
                df['مبلغ نهایی (تومان)'] = df['تعداد کل (عدد)']  df['قیمت اش']
                df['درصد تخفیف'] = 0

            st.markdown("### 🔍 ردیابی محصولات (کد محصول را انتخاب کنید):")
            selected_code = st.selectbox("کد محصول مورد نظر:", df['کد محصول'].unique())

            product_data = df[df['کد محصول'] == selected_code]
            st.write(f"📊 اطلاعات فروش کد محصول {selected_code}:")
            st.dataframe(product_data[['کارشناس مربوط', 'مشتری', 'چند کارتن خریده', 'چند کارتن مانده']], use_container_width=True)

            st.markdown("### 💡 پیشنهادات هوشمند سیستم هوش تجاری (BI)")
            best_sellers = df.groupby(['کد محصول', 'کارشناس مربوط'])['چند کارتن خریده'].sum().reset_index()
            best_sellers = best_sellers.sort_values('چند کارتن خریده', ascending=False).drop_duplicates('کد محصول')

            col_rec1, col_rec2 = st.columns(2)
            with col_rec1:
                st.info("🔥 پیشنهاد کارشناس برای محصول:")
                for idx, row in best_sellers.head(3).iterrows():
                    st.write(f"🔹 کد محصول {row['کد محصول']} را به کارشناس {row['کارشناس مربوط']} بسپارید.")

            with col_rec2:
                st.warning("🛍️ پتانسیل خرید مشتریان:")
                high_stock = df[df['چند کارتن مانده'] > 5].sort_values('چند کارتن مانده', ascending=False)
                for idx, row in high_stock.head(3).iterrows():
                    st.write(f"🔸 مشتری {row['مشتری']} هنوز {row['چند کارتن مانده']} کارتن از کد {row['کد محصول']} انبار دارد.")

            agent_perf = df.groupby('کارشناس مربوط').agg({'مبلغ نهایی (تومان)': 'sum', 'درصد تخفیف': 'mean'}).reset_index()
            agent_perf['نمره عملکرد (از ۱۰۰)'] = ((agent_perf['مبلغ نهایی (تومان)'] / agent_perf['مبلغ نهایی (تومان)'].max() * 80) + (20 - agent_perf['درصد تخفیف'])).round(1)

            st.write("---")
            st.subheader("🥇 رتبه‌بندی کارشناسان استوک")
            st.dataframe(agent_perf.sort_values('نمره عملکرد (از ۱۰۰)', ascending=False), use_container_width=True)

        # ==========================================
        # 2. PROJECT AND DOOR DEPARTMENT
        # ==========================================
        else:
            st.subheader("🏢 تحلیل وضعیت پروژه‌ها و پیگیری‌ها")

            agent_perf = df.groupby('کارشناس مربوطه').agg({
                'تعداد ویزیت': 'sum',

'مبلغ اش': 'sum'
            }).reset_index()

            agent_perf['نمره عملکرد (از ۱۰۰)'] = (
                ((agent_perf['تعداد ویزیت'] / agent_perf['تعداد ویزیت'].max())  30) + 
                ((agent_perf['مبلغ اش'] / agent_perf['مبلغ اش'].max())  70)
            ).round(1)

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown("### 📊 جدول عملکرد کارشناسان")
                st.dataframe(agent_perf.sort_values('نمره عملکرد (از ۱۰۰)', ascending=False), use_container_width=True)

            with col_p2:
                fig, ax = plt.subplots()
                ax.bar(agent_perf['کارشناس مربوطه'], agent_perf['مبلغ اش'], color='purple')
                ax.set_title("میزان فروش کارشناسان بر اساس پروژه")
                plt.xticks(rotation=45)
                st.pyplot(fig)

        # ==========================================
        # 3. AI ANALYSIS
        # ==========================================
        st.write("---")
        st.subheader("🤖 تحلیل داینامیک مدیریتی (هوش مصنوعی)")

        if GOOGLE_API_KEY == "YOUR_GEMINI_API_KEY":
            st.info("💡 تحلیل خودکار سیستم: بارگذاری اطلاعات با موفقیت انجام شد. بالاترین راندمان کارشناسان استخراج گردید. برای فعال‌سازی تحلیل متن‌کاوی زنده هوش مصنوعی، کلید API را ست کنید.")
        else:
            ai_data = df.head(10).to_string()
            prompt = f"شما مشاور مدیریت شرکت دستگیره ایران هستید. این داده‌های دپارتمان {department} را تحلیل کنید و نقاط قوت، ضعف و پیشنهاد توسعه بدهید:\n{ai_data}"
            with st.spinner("🤖 هوش مصنوعی در حال تحلیل داده‌ها..."):
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                st.markdown(response.text)

    except Exception as e:
        st.error(f"❌ خطا در ساختار فایل! مطمئن شوید نام ستون‌های اکسل دقیقاً با راهنما هماهنگ باشد. خطا: {e}")
