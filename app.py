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
    ["🛒 فروش استوک / رسوب", "🏢 فروش پروژه‌ای", "🚪 بخش درب‌سازی"]
)

st.title(f"📊 {department}")

# File Uploader
uploaded_file = st.file_uploader(f"لطفاً فایل اکسل (شیت مربوط به {department}) را آپلود کنید", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        # خواندن فایل (پشتیبانی از اکسل و csv دمو)
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=1)  # سطر اول توضیحی است، از سطر دوم داده‌ها شروع می‌شوند
        else:
            df = pd.read_excel(uploaded_file, skiprows=1)
            
        df.columns = [c.strip() for c in df.columns] 
        
        # پاک‌سازی داده‌های خالی
        df = df.dropna(subset=['عنوان كالا'])
        
        st.subheader("📋 سطر‌های ابتدایی فایل بارگذاری شده")
        st.dataframe(df[['عنوان كالا', 'موجودی به کارتن', 'کارشناس فروش', 'تعداد فروخته شده(کارتن)', 'مجموع قیمت فروش']].head(5), use_container_width=True)
        st.write("---")

        # ==========================================
        # ۱. بخش فروش استوک و رسوب (بر اساس اکسل واقعی)
        # ==========================================
        if "استوک" in department or "رسوب" in department:
            st.subheader("🎯 تحلیل ماتریس فروش و پتانسیل‌یابی کالاها")
            
            # تبدیل ستون‌های عددی برای محاسبات بدون ارور
            df['تعداد فروخته شده(کارتن)'] = pd.to_numeric(df['تعداد فروخته شده(کارتن)'], errors='coerce').fillna(0)
            df['مجموع قیمت فروش'] = pd.to_numeric(df['مجموع قیمت فروش'], errors='coerce').fillna(0)
            df['درصد تخفیف'] = pd.to_numeric(df['درصد تخفیف'], errors='coerce').fillna(0)
            df['باقی مانده'] = pd.to_numeric(df['باقی مانده'], errors='coerce').fillna(0)
            
            # الف) ردیابی کالا: کیا فروختن و مشتری‌ها کیا بودن؟
            st.markdown("### 🔍 ردیابی کالاها:")
            selected_product = st.selectbox("انتخاب عنوان کالا:", df['عنوان كالا'].unique())
            
            product_data = df[df['عنوان كالا'] == selected_code]
            st.write(f"📊 وضعیت بازار برای: **{selected_product}**")
            st.dataframe(product_data[['کارشناس فروش', 'مشتریان', 'تعداد فروخته شده(کارتن)', 'باقی مانده']], use_container_width=True)
            
            # ب) پیشنهادات هوشمند سیستم توصیه‌گر
            st.markdown("### 💡 پیشنهادات هوشمند سیستم هوش تجاری (BI)")
            col_rec1, col_rec2 = st.columns(2)
            
            with col_rec1:
                st.info("🔥 **پیشنهاد تمرکز فروش کالا:**")
                # پیدا کردن کالاهایی که بیشترین فروش را داشتند و کارشناس موفق آن
                best_sellers = df[df['تعداد فروخته شده(کارتن)'] > 0].sort_values('تعداد فروخته شده(کارتن)', ascending=False)
                if not best_sellers.empty:
                    for idx, row in best_sellers.head(3).iterrows():
                        st.write(f"🔹 کالا **{row['عنوان كالا']}** توسط **{row['کارشناس فروش']}** خوب فروخته شده؛ بقیه از تکنیک او استفاده کنند.")
                else:
                    st.write("داده‌ای برای فروش‌های موفق ثبت نشده است.")
            
            with col_rec2:
                st.warning("🛍️ **کالاهای رسوب شده در انبار (فرصت فروش):**")
                high_stock = df[df['باقی مانده'] > 10].sort_values('باقی مانده', ascending=False)
                if not high_stock.empty:
                    for idx, row in high_stock.head(3).iterrows():
                        st.write(f"🔸 کالا **{row['عنوان كالا']}** تعداد **{row['باقی مانده']} کارتن** رسوب دارد؛ پیشنهاد آفر ویژه به مشتریان.")
            
            # ج) رتبه‌بندی کارشناسان بر اساس اکسل واقعی
            st.write("---")
            st.subheader("🥇 رتبه‌ب بندی عملکرد کارشناسان فروش")
            
            agent_perf = df.groupby('کارشناس فروش').agg({
                'مجموع قیمت فروش': 'sum',
                'تعداد فروخته شده(کارتن)': 'sum',
                'درصد تخفیف': 'mean'
            }).reset_index()
            
            # فرمول امتیازدهی علمی (حجم فروش بالا مثبت، میانگین تخفیف بالا منفی)
            if agent_perf['مجموع قیمت فروش'].max() > 0:
                agent_perf['نمره عملکرد (از ۱۰۰)'] = ((agent_perf['مجموع قیمت فروش'] / agent_perf['مجموع قیمت فروش'].max() * 80) + (20 - agent_perf['درصد تخفیف'])).round(1)
            else:
                agent_perf['نمره عملکرد (از ۱۰۰)'] = 0
                
            st.dataframe(agent_perf.sort_values('نمره عملکرد (از ۱۰۰)', ascending=False), use_container_width=True)

        # ==========================================
        # ۲. بخش پروژه و درب سازی (بر اساس توضیحات قبلی شما)
        # ==========================================
        else:
            st.subheader("🏢 تحلیل وضعیت پروژه‌ها و پیگیری‌ها")
            # اگر فایل دپارتمان پروژه آپلود شود ستون‌های مبالغ و ویزیت بررسی می‌شوند
            st.info("این دپارتمان منتظر ساختار ستون‌های ویزیت و پروژه است. در حال حاضر فرآیند کلی فعال است.")

        # ==========================================
        # ۳. تحلیل هوش مصنوعی زنده
        # ==========================================
        st.write("---")
        st.subheader("🤖 گزارش تحلیل هوشمند مدیریتی (Gemini)")
        
        # آماده سازی خلاصه داده‌ها برای هوش مصنوعی
        ai_data = df[['عنوان كالا', 'مشتریان', 'کارشناس فروش', 'تعداد فروخته شده(کارتن)', 'باقی مانده']].head(15).to_string()
        
        prompt = f"""
        شما مشاور ارشد سیستم‌های BI شرکت دستگیره ایران هستید. داده‌های زیر مربوط به بخش {department} است.
        با توجه به نام کالاها، مشتریان، عملکرد کارشناسان و باقی‌مانده‌ها یک گزارش دقیق ارائه دهید:
        ۱. کدام دستگیره‌ها یا کالاها بیشترین رسوب (باقی‌مانده) را دارند و برای فروختنشان چه آفر یا پیشنهادی به کدام مشتری مناسب است؟
        ۲. عملکرد کارشناسان فروش (مثل کمالی، سلطانی و...) را نقد کنید؛ چه کسی موفق‌تر بوده و به چه کسی باید کمک کرد؟
        ۳. یک راهکار سریع برای ذوب کردن رسوب‌های انبار دستگیره ایران پیشنهاد دهید.
        
        داده‌ها:
        {ai_data}
        """
        
        if GOOGLE_API_KEY == "YOUR_GEMINI_API_KEY":
            st.info("💡 فایل اکسل شما با موفقیت تحلیل ریاضی شد. برای فعال‌سازی بخش تحلیل متنی زنده و دریافت راهکارهای فروش، کلید API هوش مصنوعی را جایگزین کنید.")
        else:
            with st.spinner("🤖 هوش مصنوعی در حال خواندن سطر به سطر کالاهای رسوب شده..."):
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                st.markdown(response.text)

    except Exception as e:
        st.error(f"❌ خطای ساختاری: سیستم نتوانست ستون‌های اکسل را تطبیق دهد. لطفاً مطمئن شوید شیت درست را آپلود کرده‌اید. جزئیات خطا: {e}")      # ==========================================
        # 1. STOCK DEPARTMENT
        # ==========================================
        if "استوک" in department:
            st.subheader("🎯 تحلیل ماتریس فروش و پتانسیل‌یابی بازار")
            
            # در این خط علامت ضرب به طور قطعی وجود دارد
            df['تعداد کل (عدد)'] = df['چند کارتن خریده'] * df['تعداد دست هر کارتن']
            
            if 'درصد تخفیف' in df.columns:
                df['مبلغ نهایی (تومان)'] = (df['تعداد کل (عدد)'] * df['قیمت اش']) * (1 - df['درصد تخفیف'] / 100)
            else:
                df['مبلغ نهایی (تومان)'] = df['تعداد کل (عدد)'] * df['قیمت اش']
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
                ((agent_perf['تعداد ویزیت'] / agent_perf['تعداد ویزیت'].max()) * 30) + 
                ((agent_perf['مبلغ اش'] / agent_perf['مبلغ اش'].max()) * 70)
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
            st.info("💡 تحلیل خودکار سیستم: بارگذاری اطلاعات با موفقیت انجام شد. بالاترین راندمان کارشناسان استخراج گردید.")
        else:
            ai_data = df.head(10).to_string()
            prompt = f"شما مشاور مدیریت شرکت دستگیره ایران هستید. این داده‌های دپارتمان {department} را تحلیل کنید.\n{ai_data}"
            with st.spinner("🤖 هوش مصنوعی در حال تحلیل داده‌ها..."):
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                st.markdown(response.text)

    except Exception as e:
        st.error(f"❌ خطا در ساختار فایل! خطا: {e}")
