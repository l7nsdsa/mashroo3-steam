import os
import json
import urllib.request
import urllib.error
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI, APIError, AuthenticationError, RateLimitError

load_dotenv()

APP_VERSION = "1.0.0"
DEFAULT_UPDATE_MANIFEST = os.getenv("STEM_UPDATE_MANIFEST_URL", "").strip()

st.set_page_config(
    page_title="مشروع STEM | مساعد ذكي",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { direction: rtl; }
    [data-testid="stSidebar"] { direction: rtl; }
    .hero {
        padding: 1.4rem 1.5rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #172554 0%, #312e81 55%, #4338ca 100%);
        color: white;
        margin-bottom: 1rem;
    }
    .hero h1 { margin: 0; font-size: 2rem; }
    .hero p { margin: .5rem 0 0 0; opacity: .9; }
    .small-note { color: #9ca3af; font-size: .85rem; }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("⚙️ إعدادات مساعد STEM")
    st.caption("مساعد ذكي لمشروع STEM")
    env_key = os.getenv("OPENAI_API_KEY", "")
    typed_key = st.text_input(
        "مفتاح OpenAI API (اختياري)",
        value="",
        type="password",
        help="الأفضل وضع المفتاح في ملف .env على جهازك. لا تشاركه مع أحد.",
    )
    api_key = typed_key.strip() or env_key.strip()

    model = st.text_input(
        "اسم النموذج",
        value=os.getenv("OPENAI_MODEL", "gpt-5.5"),
        help="استخدم اسم نموذج متاح في حساب API الخاص بك.",
    )
    persona = st.selectbox(
        "شخصية المساعد",
        [
            "مساعد عام",
            "مدرس STEM",
            "مساعد برمجة",
            "مساعد إبداعي",
        ],
    )
    answer_style = st.selectbox(
        "طول الإجابة",
        ["متوازن", "مختصر", "مفصل"],
        index=0,
    )
    if st.button("🗑️ مسح المحادثة", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("**🔄 تحديثات البرنامج**")
    st.caption(f"الإصدار الحالي: {APP_VERSION}")
    manifest_url = st.text_input(
        "رابط ملف التحديثات (JSON)",
        value=DEFAULT_UPDATE_MANIFEST,
        help="ضع رابط HTTPS لملف version.json المنشور في مستودعك أو خادمك.",
    ).strip()
    if st.button("التحقق من التحديثات", use_container_width=True):
        if not manifest_url.startswith("https://"):
            st.warning("أضف رابط HTTPS صالحًا لملف version.json حتى يمكن التحقق من الإصدار المنشور.")
        else:
            try:
                request = urllib.request.Request(
                    manifest_url,
                    headers={"User-Agent": "STEM-Assistant-Updater/1.0"},
                )
                with urllib.request.urlopen(request, timeout=8) as response:
                    manifest = json.loads(response.read().decode("utf-8"))
                latest_version = str(manifest.get("version", "")).strip()
                release_url = str(manifest.get("release_url", "")).strip()
                if not latest_version:
                    st.error("ملف التحديثات لا يحتوي على حقل version.")
                elif latest_version == APP_VERSION:
                    st.success("أنت تستخدم أحدث إصدار.")
                else:
                    st.info(f"الإصدار المنشور: {latest_version} — إصدارك الحالي: {APP_VERSION}")
                    if release_url.startswith("https://"):
                        st.markdown(f"[فتح صفحة التحديث أو الإصدار الجديد]({release_url})")
                    st.caption(
                        "إذا كان التطبيق مستضافًا على الويب، على مالك المشروع نشر الكود الجديد على الخادم؛ "
                        "الزر يتحقق من الإصدار ولا يستطيع استبدال كود الخادم من متصفح المستخدم."
                    )
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                st.error(f"تعذّر التحقق من التحديثات. راجع الرابط واتصال الإنترنت. التفاصيل: {exc}")
            except Exception as exc:
                st.error(f"تعذّر قراءة ملف التحديثات: {exc}")

    st.divider()
    st.markdown("**حالة الاتصال**")
    if api_key:
        st.success("مفتاح API موجود")
    else:
        st.warning("أضف مفتاح API لبدء المحادثة")
    st.markdown(
        '<p class="small-note">تنبيه: استخدام API قد يترتب عليه رسوم حسب حسابك واستهلاكك.</p>',
        unsafe_allow_html=True,
    )

st.markdown("""
<div class="hero">
  <h1>🤖 مساعد STEM</h1>
  <p>مساعدك الذكي للتعلّم، البرمجة، العلوم، والأفكار الجديدة.</p>
</div>
""", unsafe_allow_html=True)

st.write("اسألني أي سؤال، أو اختر أحد الاقتراحات للبدء:")

suggestions = [
    "اشرح لي الذكاء الاصطناعي بطريقة سهلة",
    "اقترح تجربة STEM آمنة للمدرسة",
    "اكتب لي برنامج بايثون بسيط",
]
cols = st.columns(len(suggestions))
for col, suggestion in zip(cols, suggestions):
    if col.button(suggestion, use_container_width=True):
        st.session_state.pending_prompt = suggestion

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("اكتب رسالتك هنا...")

if "pending_prompt" in st.session_state:
    prompt = st.session_state.pop("pending_prompt")

if prompt:
    if not api_key:
        st.error(
            "ما فيه مفتاح API. أنشئ مفتاحًا من منصة OpenAI، ثم ضعه في ملف .env "
            "أو في خانة مفتاح API في الشريط الجانبي."
        )
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    persona_instructions = {
        "مساعد عام": "أنت مساعد STEM، مساعد مفيد وواضح. أجب بلغة المستخدم، وكن صادقًا إذا لم تعرف الإجابة.",
        "مدرس STEM": "أنت مساعد STEM، مدرس STEM. اشرح العلوم والتقنية والهندسة والرياضيات خطوة بخطوة، مع أمثلة بسيطة وآمنة.",
        "مساعد برمجة": "أنت مساعد STEM، مساعد برمجة. قدم كودًا واضحًا، واشرح طريقة تشغيله، واذكر المتطلبات والأخطاء المحتملة.",
        "مساعد إبداعي": "أنت مساعد STEM، مساعد إبداعي. ساعد في العصف الذهني والكتابة وتصميم الأفكار مع تنظيم الإجابة.",
    }
    length_instructions = {
        "مختصر": "اجعل الإجابات قصيرة ومباشرة ما لم يطلب المستخدم التفصيل.",
        "متوازن": "قدّم إجابة متوازنة مع أمثلة عند الحاجة.",
        "مفصل": "قدّم شرحًا مفصلًا ومنظمًا مع خطوات وأمثلة عند الحاجة.",
    }
    instructions = (
        persona_instructions[persona]
        + "\n"
        + length_instructions[answer_style]
        + "\nإذا كتب المستخدم بالعربية، أجب بالعربية. استخدم تنسيق Markdown عند الحاجة."
    )

    # Keep the conversation context available to the model.
    conversation = [
        {"role": item["role"], "content": item["content"]}
        for item in st.session_state.messages[-20:]
    ]

    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=model.strip(),
                instructions=instructions,
                input=conversation,
            )
            answer = response.output_text or "لم يصل نص في الرد. جرّب مرة أخرى."
            placeholder.markdown(answer)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )
        except AuthenticationError:
            placeholder.error("مفتاح API غير صحيح أو غير مفعّل. راجع المفتاح ثم حاول مجددًا.")
        except RateLimitError:
            placeholder.error("وصلت إلى حد الاستخدام أو لا يوجد رصيد API كافٍ. راجع إعدادات حساب API.")
        except APIError as exc:
            placeholder.error(f"حدث خطأ من خدمة API: {exc}")
        except Exception as exc:
            placeholder.error(f"حدث خطأ غير متوقع: {exc}")

st.markdown(
    '<p class="small-note">نسخة تعليمية قابلة للتطوير. لا تضع مفاتيح API في مستودع عام أو تشاركها.</p>',
    unsafe_allow_html=True,
)
