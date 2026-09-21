# hf_spaces_reporter

بوت تليجرام يفحص Hugging Face Spaces كل ساعة، يحلل المشاريع الحديثة عبر Gemini API المجاني، ويرسل تقارير مرتين يومياً في محادثة شخصية. يُستضاف مجاناً على Hugging Face Spaces.

---

## 📋 نظرة عامة

يهدف هذا المشروع إلى أتمتة عملية متابعة وتحليل المشاريع الجديدة على منصة Hugging Face — وتحديداً قسم **Spaces** — باستخدام نموذج Gemini API (الفئة المجانية) من Google AI Studio. يقوم البوت بما يلي:

- **جلب المشاريع الحديثة** من Hugging Face Spaces كل ساعة.
- **تحليل وتقييم** كل مشروع وفق ثلاثة معايير: *ابتكار الفكرة*، *سرعة جمع الإعجابات*، و*سهولة إعادة التنفيذ*.
- **تجميع التقرير وإرساله** مرتين يومياً (وفق الأوقات المحددة بالتوقيت العالمي UTC) عبر بوت تليجرام في محادثة شخصية مباشرة.
- **الاستضافة المجانية** الكاملة على Hugging Face Spaces بدون أي تكلفة تشغيلية.

---

## 🛠 المتطلبات الأساسية

- حساب على [Hugging Face](https://huggingface.co/) مع **Token** صالح.
- حساب على [Telegram](https://telegram.org/) مع **Bot Token** من [@BotFather](https://t.me/BotFather).
- مفتاح API من [Google AI Studio](https://aistudio.google.com/) (الفئة المجانية).
- **Chat ID** الخاص بمحادثتك الشخصية على تليجرام (يمكن الحصول عليه عبر [@userinfobot](https://t.me/userinfobot)).
- Python 3.10+ (للتطوير المحلي).

---

## ⚙️ الإعداد

### 1. استنساخ المستودع

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/hf_spaces_reporter
cd hf_spaces_reporter
```

### 2. تثبيت المكتبات المطلوبة

```bash
pip install -r requirements.txt
```

### 3. إعداد متغيرات البيئة

أنشئ ملف `.env` في الجذر أو قم بتهيئة متغيرات البيئة مباشرة على Hugging Face Spaces عبر واجهة الإعدادات.

| المتغير | الوصف | مثال |
|---|---|---|
| `HF_TOKEN` | رمز الوصول إلى Hugging Face API | `hf_xxxxxxxxxxxxxxxx` |
| `TELEGRAM_BOT_TOKEN` | رمز بوت تليجرام | `7123456789:AAH...` |
| `GEMINI_API_KEY` | مفتاح Gemini API المجاني | `AIzaSy...` |
| `TELEGRAM_CHAT_ID` | معرف المحادثة الشخصية | `123456789` |
| `HF_SPACES_LIMIT` | الحد الأقصى لعدد المساحات المُفحَصة في كل دورة | `50` |
| `REPORT_HOURS` | أوقار إرسال التقرير اليومي (UTC)، مفصولة بفواصل | `8,20` |

---

## 🚀 النشر على Hugging Face Spaces

1. أنشئ Space جديدًا على [huggingface.co/new-space](https://huggingface.co/new-space) بنوع **Docker** أو **Static**.
2. ارفع جميع ملفات المشروع (بما فيها `requirements.txt`).
3. أضف متغيرات البيئة المطلوبة عبر تبويب **Settings → Variables and Secrets**.
4. اضغط **Create Space** — سيتم بناء الحاوية وتشغيل البوت تلقائياً.
5. تأكد من أن الـ Space يعمل دائماً عبر تفعيل **Always-on** (متاح في خطة المجانية مع بعض القيود) أو استخدم خدمة خارجية مثل Kowlactyl للحفاظ على التشغيل.

---

## 🔄 آلية العمل

```
┌─────────────────────────────────────────────────────────┐
│                    Hugging Face Spaces                   │
│  ┌──────────────┐   كل ساعة     ┌─────────────────────┐ │
│  │  HF API      │──────────────▶│  fetch_recent_spaces │ │
│  │  (Spaces)    │               │  (جلب المساحات)      │ │
│  └──────────────┘               └─────────┬───────────┘ │
│                                           │             │
│                                           ▼             │
│                              ┌────────────────────────┐ │
│                              │    analyzer.py          │ │
│                              │  Gemini API (مجاني)     │ │
│                              │  تقييم + تقرير مفصل    │ │
│                              └─────────┬──────────────┘ │
│                                        │                │
│                                        ▼                │
│                              ┌────────────────────────┐ │
│                              │   telegram_client.py    │ │
│                              │  إرسال التقرير إلى      │ │
│                              │  محادثتك الشخصية        │ │
│                              └────────────────────────┘ │
│                                                           │
│              ┌──────────────────────────────┐             │
│              │     scheduler.py             │             │
│              │  • فحص كل ساعة               │             │
│              │  • تقرير مرتين يومياً (UTC)   │             │
│              └──────────────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

### الجدولة الزمنية

| المهمة | التكرار |
|---|---|
| فحص المساحات الجديدة (`_hourly_check`) | كل ساعة |
| تجميع التقرير وإرساله (`_daily_report`) | مرتين يومياً حسب `REPORT_HOURS` |

---

## 📁 بنية المشروع

```
hf_spaces_reporter/
├── config.py            # قراءة وتخزين إعدادات المشروع من متغيرات البيئة
├── hf_scraper.py        # جلب أحدث المساحات من Hugging Face API
├── analyzer.py          # تحليل المساحات باستخدام Gemini API وتقييمها
├── telegram_client.py   # إرسال التقارير عبر بوت تليجرام
├── scheduler.py         # جدولة المهام (فحص ساعي + تقارير يومية)
├── main.py              # نقطة الدخول: FastAPI + APScheduler
├── requirements.txt     # المكتبات المطلوبة
└── README.md            # هذا الملف
```

### شرح الملفات

| الملف | المسؤولية |
|---|---|
| `config.py` | يقرأ جميع متغيرات البيئة (`HF_TOKEN`, `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, `TELEGRAM_CHAT_ID`, `HF_SPACES_LIMIT`, `REPORT_HOURS`) ويوفر كائن `Settings` ونسخة `settings` العامة. |
| `hf_scraper.py` | يستدعي Hugging Face API لجلب آخر المساحات مع فلترة حسب التاريخ والحد الأقصى المحدد. يُصدّر `SpaceInfo` و`fetch_recent_spaces`. |
| `analyzer.py` | يحلل المساحات المجلوبة عبر Gemini API المجاني، يقيّم كل مشروع حسب الابتكار وسرعة الإعجابات وسهولة التنفيذ، ويعيد تقريراً مفصلاً. يُصدّر `AnalysisReport` و`analyze_spaces`. |
| `telegram_client.py` | يُدعم إرسال تقارير التحليل عبر بوت تليجرام إلى محادثة شخصية مباشرة. يُصدّر `TelegramClient` و`send_report`. |
| `scheduler.py` | يُجدول فحص المساحات كل ساعة وتجميع التقارير وإرسالها مرتين يومياً. يُصدّر `start_scheduler`. |
| `main.py` | نقطة الدخول الرئيسية: يبدأ خادم FastAPI ويُطلق جدولة المهام في الخلفية عند الاستضافة على Hugging Face Spaces. يُصدّر `app`, `main`, والمسارات `/` و`/health`. |
| `requirements.txt` | المكتبات: `apscheduler`, `fastapi`, `google-generativeai`, `httpx`, `telegram`, `uvicorn[standard]`. |

---

## 📊 نماذج البيانات

### `SpaceInfo` (من `hf_scraper.py`)

| الحقل | النوع | الوصف |
|---|---|---|
| `name` | `str` | اسم المساحة |
| `url` | `str` | الرابط الكامل للمساحة |
| `likes` | `int` | عدد الإعجابات |
| `created_at` | `str` | تاريخ الإنشاء |
| `description` | `str` | وصف المساحة |

### `AnalysisReport` (من `analyzer.py`)

| الحقل | النوع | الوصف |
|---|---|---|
| `name` | `str` | اسم المساحة |
| `url` | `str` | رابط المساحة |
| `innovation_score` | `float` | تقييم ابتكار الفكرة (0–10) |
| `like_speed_score` | `float` | تقييم سرعة جمع الإعجابات (0–10) |
| `ease_score` | `float` | تقييم سهولة إعادة التنفيذ (0–10) |
| `summary` | `str` | ملخص التحليل والسبب في التميز |
| `suggestions` | `str` | مقترحات التطوير |

---

## 🧪 الاستخدام المحلي

```bash
# تعيين متغيرات البيئة
export HF_TOKEN="hf_xxxxxxxx"
export TELEGRAM_BOT_TOKEN="7123456789:AAH..."
export GEMINI_API_KEY="AIzaSy..."
export TELEGRAM_CHAT_ID="123456789"
export HF_SPACES_LIMIT="50"
export REPORT_HOURS="8,20"

# تشغيل البوت محلياً
python main.py
```

سيبدأ الخادم على المنفذ المحدد (افتراضياً `8000`) وستُطلق المهام المجدولة في الخلفية.

---

## 📡 نقاط النهاية (API Endpoints)

| المسار | الطريقة | الوصف |
|---|---|---|
| `/` | `GET` | صفحة الترحيب |
| `/health` | `GET` | فحص حالة الخدمة |

---

## 📜 الرخصة

هذا المشروع مفتوح المصدر ومتاح مجاناً بالكامل.
