import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai

# ۱. تنظیمات هوش مصنوعی (Gemini API)
GOOGLE_API_KEY = "YOUR_GEMINI_API_KEY" 
if GOOGLE_API_KEY != "YOUR_GEMINI_API_KEY":
    genai.configure(api_key=GOOGLE_API_KEY)

st.set_page_config(page_title="سیستم تحلیل هوشمند دستگیره ایران", layout="wide")
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏢 پلتفرم هوش تجاری و تحلیل پیشرفته دستگیره ایران</h1>", unsafe_allow_html=True)
st.write("---")

# منوی انتخاب دپارتمان
st.sidebar.header("📁 منوی دسترسی")
department = st.sidebar.selectbox(
    "بخش مورد نظر را انتخاب کنید:",
    ["🛒 فروش استوک", "🏢 فروش پروژه‌ای", "🚪 بخش درب‌سازی"]
)

st.title(f"📊 {department}")

# ۲. آپلود فایل اکسل
uploaded_file = st.file_uploader(f"لطفاً فایل اکسل مربوط به {department} را آپلود کنید", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [c.strip() for c in df.columns] # حذف فاصله‌های اضافی در نام ستون‌ها

        st.subheader("📋 مشاهده داده‌های بارگذاری شده")
        st.dataframe(df.head(), use_container_width=True)
        st.write("---")

        # ==========================================
        # بخش اول: تحلیل فروش استوک
        # ==========================================
        if "استوک" in department:
            st.subheader("🎯 تحلیل ماتریس فروش و پتانسیل‌یابی بازار")

            # محاسبه مبلغ کل فروش هر ردیف: (تعداد کارتن  تعداد دست در هر کارتن  قیمت واحد) با اعمال تخفیف
            # فرمول: تعداد کل = تعداد کارتن  تعداد دست در کارتن
            # مبلغ نهایی = (تعداد کل  قیمت)  (1 - درصد تخفیف)
            df['تعداد کل (عدد)'] = df['چند کارتن خریده']  df['تعداد دست هر کارتن']
            df['مبلغ نهایی (تومان)'] = (df['تعداد کل (عدد)']  df['قیمت اش'])  (1 - df['درصد تخفیف کل'] / 100 if 'درصد تخفیف کل' in df.columns else 1)

            # الف) چه کدی را کیا فروختن و مشتری‌ها کیا بودن؟
            st.markdown("### 🔍 ردیابی محصولات (کد محصول را انتخاب کنید):")
            selected_code = st.selectbox("کد محصول مورد نظر:", df['کد محصول'].unique())

            product_data = df[df['کد محصول'] == selected_code]
            st.write(f"📊 اطلاعات فروش کد محصول *{selected_code}:")
            st.dataframe(product_data[['کارشناس مربوط', 'مشتری', 'چند کارتن خریده', 'چند کارتن مانده']], use_container_width=True)

            # ب) سیستم هوشمند پیشنهاددهی (Recommendation)
            st.markdown("### 💡 پیشنهادات هوشمند سیستم هوش تجاری (BI)")

            # پیدا کردن بهترین فروشنده برای هر کد محصول
            best_sellers = df.groupby(['کد محصول', 'کارشناس مربوط'])['چند کارتن خریده'].sum().reset_index()
            best_sellers = best_sellers.sort_values('چند کارتن خریده', ascending=False).drop_duplicates('کد محصول')

            # پیدا کردن مشتریانی که پتانسیل خرید دارند (مثلاً یک محصول را قبلاً زیاد خریدند، اما کدهای مشابه را نخریدند)
            col_rec1, col_rec2 = st.columns(2)
            with col_rec1:
                st.info("🔥 پیشنهاد کارشناس برای محصول:")
                for idx, row in best_sellers.head(3).iter_rows():
                    st.write(f"🔹 کد محصول {row['کد محصول']} را به کارشناس {row['کارشناس مربوط']} بسپارید؛ چون بیشترین حجم فروش این کد را داشته است.")

            with col_rec2:
                st.warning("🛍️ پتانسیل خرید مشتریان (کارتن‌های مانده در انبار):")
                high_stock_remained = df[df['چند کارتن مانده'] > 5].sort_values('چند کارتن مانده', ascending=False)
                for idx, row in high_stock_remained.head(3).iterrows():
                    st.write(f"🔸 مشتری {row['مشتری']} هنوز {row['چند کارتن مانده']} کارتن از کد {row['کد محصول']}* در انبارش مانده؛ پیشنهاد می‌شود کارشناس تخفیف بهتری برای شارژ مجدد به او بدهد.")

            # سیستم امتیازدهی استوک
            agent_perf = df.groupby('کارشناس مربوط').agg({'مبلغ نهایی (تومان)': 'sum', 'درصد تخفیف': 'mean', 'چند کارتن خریده': 'sum'}).reset_index()
            # امتیاز

دهی: فروش بالا امتیاز مثبت، تخفیف زیاد امتیاز منفی!
            agent_perf['نمره عملکرد (از ۱۰۰)'] = ((agent_perf['مبلغ نهایی (تومان)'] / agent_perf['مبلغ نهایی (تومان)'].max()  80) + (20 - agent_perf['درصد تخفیف'])).round(1)

            st.write("---")
            st.subheader("🥇 رتبه‌بندی کارشناسان استوک")
            st.dataframe(agent_perf.sort_values('نمره عملکرد (از ۱۰۰)', ascending=False), use_container_width=True)

        # ==========================================
        # بخش دوم و سوم: تحلیل پروژه و درب‌سازی
        # ==========================================
        else:
            st.subheader("🏢 تحلیل وضعیت پروژه‌ها و پیگیری‌ها")

            # شاخص تلاش: تعداد ویزیت‌ها
            # امتیازدهی بر اساس: تعداد ویزیت (۳۰ نمره) + مبلغ فروخته شده (۷۰ نمره)
            agent_perf = df.groupby('کارشناس مربوطه').agg({
                'تعداد ویزیت': 'sum',
                'مبلغ اش': 'sum',
                'نام پروژه / مشتری': 'count'
            }).rename(columns={'نام پروژه / مشتری': 'تعداد پروژه‌ها'}).reset_index()

            agent_perf['نمره عملکرد (از ۱۰۰)'] = (
                ((agent_perf['تعداد ویزیت'] / agent_perf['تعداد ویزیت'].max())  30) + 
                ((agent_perf['مبلغ اش'] / agent_perf['مبلغ اش'].max()) * 70)
            ).round(1)

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown("### 📊 جدول عملکرد کارشناسان پروژه")
                st.dataframe(agent_perf.sort_values('نمره عملکرد (از ۱۰۰)', ascending=False), use_container_width=True)

            with col_p2:
                # رسم نمودار ویزیت در برابر فروش
                fig, ax = plt.subplots()
                ax.scatter(agent_perf['تعداد ویزیت'], agent_perf['مبلغ اش'], s=200, color='purple', alpha=0.7)
                for i, txt in enumerate(agent_perf['کارشناس مربوطه']):
                    ax.annotate(txt, (agent_perf['تعداد ویزیت'].iloc[i], agent_perf['مبلغ اش'].iloc[i]))
                ax.set_xlabel("تعداد ویزیت")
                ax.set_ylabel("مبلغ فروش")
                ax.set_title("رابطه تعداد ویزیت و میزان فروش کارشناسان")
                st.pyplot(fig)

        # ==========================================
        # موتور هوش مصنوعی برای تحلیل متن و گزارش مدیریتی
        # ==========================================
        st.write("---")
        st.subheader("🤖 تحلیل داینامیک مدیریتی (هوش مصنوعی)")

        # خلاصه کردن داده‌های کلیدی برای فرستادن به AI
        if "استوک" in department:
            ai_data = df[['کد محصول', 'مشتری', 'کارشناس مربوط', 'چند کارتن خریده', 'چند کارتن مانده']].to_string()
        else:
            ai_data = df[['نام پروژه / مشتری', 'کارشناس مربوطه', 'نتیجه', 'توضیحات']].to_string()

        prompt = f"""
        شما مشاور ارشد سیستم‌های BI شرکت دستگیره ایران هستید. داده‌های زیر مربوط به بخش {department} است.
        با توجه به نتایج، تعداد کارتن‌ها، نتایج ویزیت‌ها و "توضیحات" کارشناسان، یک تحلیل عمیق ارائه دهید:
        ۱. تحلیل کنید کدهای پرفروش دستگیره کدامند و کدام مشتری‌ها پتانسیل خرید بیشتری دارند؟
        ۲. بر اساس ستون نتیجه و توضیحات در پروژه‌ها، بگویید کدام پروژه‌ها در مرحله خطرناک (قفل شده) هستند و کدام‌ها در آستانه قراردادند؟
        ۳. نقاط قوت و ضعف عملکرد کارشناسان را بگویید (به چه کسی باید پاداش داد، به چه کسی آموزش؟).
        ۴. راهکار عملیاتی برای افزایش فروش دستگیره ایران.

        داده‌های خام:
        {ai_data}
        """

        if GOOGLE_API_KEY == "YOUR_GEMINI_API_KEY":
            st.warning("💡 کلید Gemini API تنظیم نشده است. برای دریافت گزارش داینامیک متنی، کلید هوش مصنوعی را در کد قرار دهید.")
        else:
            with st.spinner("🤖 هوش مصنوعی در حال خواندن سطر به سطر اکسل و توضیحات پروژه هاست..."):
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                st.markdown(response.text)

    except Exception as e:
        st.error(f"❌ خطا در ساختار فایل! مطمئن شوید نام ستون‌های اکسل دقیقاً با توضیحات هماهنگ باشد. جزئیات خطا: {e}")
