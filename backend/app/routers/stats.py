**استدلال:**
ما بر اساس گزارش خطا، خطای 401 (عدم احراز هویت) در هنگام درخواست به endpoint آمار داشبورد داریم.
 در کد فعلی، endpointهای موجود در این فایل همگی وابستگی به `get_current_user` دارند که نیاز به احراز هویت دارد.
 با توجه به اینکه در خطا گفته شده "Not authenticated"، احتمالاً کاربر وارد نشده یا توکن معتبر نیست.

 با این حال، توجه به این نکته مهم است که در گزارش بررسی گفته شده در frontend، AUTH_DISABLED = true است.
 اگر AUTH_DISABLED = true باشد، انتظار داریم که درخواست‌ها نیازی به احراز هویت نداشته باشند و یا از داده‌های جعلی استفاده کنند.

 اما از آنجایی که خطای 401 از بک‌اند دریافت شده، به نظر می‌رسد که درخواست واقعی به بک‌اند فرستاده شده و بک‌اند نیز در حالت نیاز به احراز هویت است.

 ما دو گزینه داریم:
 1. اگر می‌خواهیم در حالت توسعه (یا زمانی که AUTH_DISABLED = true است) نیازی به احراز هویت نباشد، باید وابستگی به `get_current_user` را حذف کنیم یا یک حالت بای‌پس ایجاد کنیم.
 2. اگر باید احراز هویت وجود داشته باشد، باید مطمئن شویم که توکن در درخواست فرانت‌اند ارسال می‌شود.

 اما با توجه به اینکه در گزارش بررسی گفته شده که AUTH_DISABLED = true است و در عین حال خطای 401 داریم، احتمالاً تنظیمات متناقضی وجود دارد.

 از آنجایی که ما فقط مسئول این فایل بک‌اند هستیم و نمی‌توانیم فرانت‌اند را تغییر دهیم، یک راه حل این است که در بک‌اند نیز یک حالت برای غیرفعال کردن احراز هویت داشته باشیم.

 با این حال، در کد فعلی بک‌اند، چنین تنظیمی وجود ندارد. اما می‌توانیم وابستگی به `get_current_user` را به صورت اختیاری کنیم تا اگر کاربری وجود نداشت، اجازه دسترسی بدهد.

 اما این کار ممکن است از نظر امنیتی صحیح نباشد. راه دیگر این است که یک تنظیم محیطی در بک‌اند داشته باشیم که احراز هویت را غیرفعال کند.

 از آنجایی که در گزارش بررسی، از frontend به AUTH_DISABLED اشاره شده، ممکن است در بک‌اند نیز یک تنظیم مشابه وجود داشته باشد. اما در کد فعلی ما چنین تنظیمی نیست.

 بنابراین، ما باید تصمیم بگیریم که آیا می‌خواهیم endpointهای آمار برای کاربران احراز هویت نشده نیز در دسترس باشد؟ احتمالاً خیر.

 اما با توجه به خطا و اینکه در فرانت‌اند AUTH_DISABLED = true است، شاید هدف این است که در حالت توسعه نیازی به احراز هویت نباشد.

 برای حل این مشکل، ما می‌توانیم یک پارامتر اختیاری برای وابستگی `get_current_user` در نظر بگیریم. اما تابع `get_current_user` در حالت فعلی اگر کاربری نباشد، استثنا می‌اندازد.

 ما می‌توانیم یک تابع دیگر ایجاد کنیم که اگر کاربر وجود نداشت، `None` برگرداند و سپس در endpoint بررسی کنیم اگر کاربر `None` بود و تنظیمات غیرفعال بودن احراز هویت فعال بود، اجازه دسترسی بدهیم.

 اما از آنجایی که در کد بک‌اند فعلی، ما از `get_current_user` استفاده می‌کنیم که احتمالاً توکن را بررسی می‌کند و اگر نباشد 401 می‌دهد، باید تغییراتی در `get_current_user` یا نحوه وابستگی ایجاد کنیم.

 از آنجایی که ما فقط می‌توانیم این فایل را تغییر دهیم، و نمی‌خواهیم `get_current_user` را تغییر دهیم (چون فایل دیگری است)، پس راه حل دیگری لازم است.

 یک ایده: می‌توانیم یک dependency تازه ایجاد کنیم که اگر AUTH_DISABLED در تنظیمات بک‌اند true بود، کاربر dummy برگرداند، در غیر این صورت از `get_current_user` استفاده کند.

 اما از آنجایی که ما فقط این فایل را داریم، نمی‌توانیم تنظیمات بک‌اند را بررسی کنیم. مگر اینکه از محیط (environment) بخوانیم.

 بنابراین، ما می‌توانیم یک متغیر محیطی در بک‌اند تعریف کنیم (مثلاً `AUTH_DISABLED`) و سپس بر اساس آن، dependency را تغییر دهیم.

 اما تغییر dependency در این فایل به تنهایی ممکن است دشوار باشد. بنابراین، ما دو endpoint جداگانه ایجاد نمی‌کنیم.

 در عوض، می‌توانیم dependency را به صورت optional درآوریم. اما در FastAPI، می‌توانیم از `Depends(get_current_user)` به صورت optional استفاده کنیم.

 ما می‌توانیم تابعی بنویسیم که اگر کاربر وجود داشت برگرداند، در غیر این صورت None برگرداند. اما تابع `get_current_user` در صورت عدم وجود کاربر، استثنا می‌اندازد.

 بنابراین، ما باید یک dependency جدید ایجاد کنیم که سعی کند کاربر را بگیرد و اگر موفق نشد، None برگرداند.

 از آنجایی که ما نمی‌توانیم `get_current_user` را تغییر دهیم (در فایل دیگری است)، می‌توانیم آن را در یک try-except بگیریم.

 بنابراین، ما یک dependency جدید به نام `optional_user` ایجاد می‌کنیم که اگر `get_current_user` استثنا 401 بدهد، None برگرداند.

 سپس در endpointهای خود، اگر `optional_user` None بود، می‌توانیم بررسی کنیم که آیا AUTH_DISABLED فعال است یا خیر. اگر فعال است، اجازه دسترسی بدهیم.

 اما ما در این فایل به متغیر محیطی دسترسی نداریم. پس باید از config بک‌اند استفاده کنیم.

 از آنجایی که این کار ممکن است پیچیده شود و زمان بر باشد، و با توجه به اینکه گزارش خطا فقط از یک endpoint داشبورد است، شاید راه ساده‌تر این است که در این endpoint خاص، اگر خطای 401 داشتیم، یک پاسخ dummy برگردانیم؟ اما این کار درستی نیست.

 با توجه به دستورالعمل‌ها، ما باید بر اساس شواهد موجود تحلیل کنیم. شواهد نشان می‌دهد که درخواست با 401 مواجه شده است. و در فرانت‌اند AUTH_DISABLED = true است.

 اگر ما در بک‌اند نیز AUTH_DISABLED = true را تنظیم کنیم، باید احراز هویت را غیرفعال کنیم.

 از آنجایی که ما نمی‌توانیم فرض کنیم که در بک‌اند AUTH_DISABLED وجود دارد، یک راه حل این است که dependency را طوری تغییر دهیم که اگر توکن وجود نداشت، یک کاربر dummy برگرداند.

 اما این کار می‌تواند امنیت را کاهش دهد. بنابراین، ما باید با در نظر گرفتن محیطی که برنامه در آن اجرا می‌شود، تصمیم بگیریم.

 با توجه به اینکه این یک برنامه آزمایشی است و AUTH_DISABLED در فرانت‌اند true است، احتمالاً در بک‌اند نیز باید true باشد.

 بنابراین، ما می‌توانیم یک تابع dependency جدید در این فایل ایجاد کنیم که ابتدا سعی کند کاربر را از توکن بگیرد، اگر موفق نشد و AUTH_DISABLED=true بود، یک کاربر dummy برگرداند.

 برای خواندن متغیر محیطی، می‌توانیم از `os.getenv` استفاده کنیم.

 پس مراحل زیر را انجام می‌دهیم:

 1. در ابتدای فایل، `import os` را اضافه می‌کنیم.
 2. یک تابع به نام `get_current_user_or_dummy` ایجاد می‌کنیم که اگر AUTH_DISABLED=true بود و توکن وجود نداشت، یک شیء dummy برگرداند.
 3. در endpointها به جای `get_current_user` از `get_current_user_or_dummy` استفاده کنیم.

 اما توجه: اگر AUTH_DISABLED=false باشد، باید حتما کاربر معتبر باشد.

 بنابراین، کد به صورت زیر تغییر می‌کند:

 با این حال، از آنجایی که تابع `get_current_user` از فایل `app.utils.security` import شده، ما نمی‌خواهیم آن را تغییر دهیم. پس یک تابع جدید می‌نویسیم.

 اما اگر `get_current_user` استثنا بدهد، ما می‌توانیم آن را catch کنیم و اگر AUTH_DISABLED=true بود، یک کاربر dummy برگردانیم.

 اما برای catch کردن استثنا، باید dependency را درون یک تابع دیگر بپیچیم.

 در FastAPI، می‌توانیم یک dependency با چندین dependency دیگر داشته باشیم.

 ما تابع جدیدی به نام `get_current_user_or_dummy` را به صورت زیر تعریف می‌کنیم:

 اما یک مشکل: dependencyها نمی‌توانند به راحتی استثناها را catch کنند مگر اینکه داخل تابع دیگری باشند.

 بنابراین، ما می‌توانیم این کار را انجام دهیم:

 از آنجایی که `get_current_user` یک dependency است، ما می‌توانیم آن را به صورت optional با استفاده از `Depends(get_current_user)` صدا بزنیم و اگر خطا داد، سپس بررسی کنیم.

 اما در FastAPI، اگر `get_current_user` استثنا بدهد، قبل از رسیدن به تابع ما، استثنا抛出 می‌شود.

 بنابراین، ما باید یک dependency جدید بنویسیم که در آن از `get_current_user` استفاده کنیم و استثنا را catch کنیم.

 کد زیر را امتحان می‌کنیم:

 اما توجه: در FastAPI، dependencyها می‌توانند استثناها را throw کنند. ما می‌خواهیم در صورت استثنا، اگر AUTH_DISABLED=true است، None برگردانیم.

 بنابراین، ما یک تابع dependency جدید ایجاد می‌کنیم که:
   - اگر AUTH_DISABLED=true بود و توکن وجود نداشت، یک شیء dummy با حداقل فیلدها برگرداند.
   - در غیر این صورت، سعی کند کاربر واقعی را برگرداند.

 اما برای اینکه بفهمیم AUTH_DISABLED در بک‌اند چطور تنظیم شده، از متغیر محیطی استفاده می‌کنیم.

 ما یک متغیر محیطی به نام `AUTH_DISABLED` در نظر می‌گیریم که اگر برابر با "true" (یا 1) بود، احراز هویت را غیرفعال می‌کنیم.

 اما اگر AUTH_DISABLED=false بود، باید حتما کاربر معتبر باشد.

 در اینجا ما یک تابع dependency جدید به نام `get_current_user_or_dummy` تعریف می‌کنیم.

 با این حال، از آنجایی که `get_current_user` ممکن است به یک شیء کاربر وابسته باشد که از دیتابیس خوانده شده، ما نمی‌توانیم یک dummy user بسازیم مگر اینکه بدانیم مدل کاربر چه فیلدهایی دارد.

 در کد فعلی، `get_current_user` احتمالاً یک شیء `User` برمی‌گرداند. اما در این فایل، ما مدل User را import نکرده‌ایم.

 بنابراین، اگر بخواهیم یک dummy user بسازیم، باید مدل User را import کنیم. اما از آنجایی که در این فایل نیازی به مدل User نداریم، می‌توانیم یک شیء ساده با فیلدهای مورد نیاز ایجاد کنیم.

 اما از آنجایی که endpointهای ما ممکن است به فیلدهای خاصی از کاربر نیاز نداشته باشند، می‌توانیم یک شیء با فیلدهای پیش‌فرض ایجاد کنیم.

 با این حال، این کار ممکن است پیچیده باشد و باعث شود که اگر endpointهای دیگر به فیلدهای کاربر نیاز داشتند، به مشکل بخورند.

 از آنجایی که در endpointهای این فایل، ما از `current_user` استفاده نمی‌کنیم (فقط برای احراز هویت است)، می‌توانیم dummy user را به صورت یک شیء با مقدارهای پیش‌فرض برگردانیم.

 اما در کد فعلی، در پارامترهای تابع، `current_user` را داریم اما از آن استفاده نمی‌کنیم. بنابراین، اگر AUTH_DISABLED=true باشد، می‌توانیم یک شیء با مقدارهای dummy برگردانیم.

 با این حال، ما نمی‌دانیم که `get_current_user` چه نوع شیئی برمی‌گرداند. بنابراین، بهتر است که اگر AUTH_DISABLED=true باشد، dependency را حذف کنیم و اجازه دهیم endpoint بدون کاربر اجرا شود.

 در FastAPI، می‌توانیم dependency را به صورت optional تعریف کنیم. اما در اینجا، ما می‌خواهیم اگر کاربر وجود نداشت و AUTH_DISABLED=true بود، ادامه دهد.

 بنابراین، ما dependency را به صورت زیر تغییر می‌دهیم:

 1. ابتدا بررسی می‌کنیم که آیا AUTH_DISABLED=true است.
 2. اگر true است، then we can skip authentication and return a dummy user or None.
 3. اگر false است، then we must have a valid user.

 اما در کد فعلی، endpointها به `current_user` وابسته هستند. اگر ما `current_user` را optional کنیم (یعنی `= None`)، آنگاه در بدنه تابع باید بررسی کنیم.

 اما اگر `current_user` None باشد و AUTH_DISABLED=false باشد، باید خطای 401 بدهیم.

 بنابراین، ما می‌توانیم dependency را به صورت یک تابع بنویسیم که اگر AUTH_DISABLED=true بود و کاربری نبود، None برگرداند و در بدنه endpoint بررسی کنیم.

 اما از آنجایی که در بدنه endpoint ما از `current_user` استفاده نمی‌کنیم، می‌توانیم آن را نادیده بگیریم.

 پس تغییرات زیر را انجام می‌دهیم:

 1. در ابتدای فایل، `import os` را اضافه می‌کنیم.
 2. یک تابع dependency جدید به نام `get_current_user_or_none` ایجاد می‌کنیم.
 3. در endpointها، به جای `current_user = Depends(get_current_user)` از `current_user = Depends(get_current_user_or_none)` استفاده می‌کنیم.
 4. در بدنه endpoint، اگر AUTH_DISABLED=false و current_user None بود، خطای 401 بدهیم.

 اما در گزارش بررسی، در فرانت‌اند AUTH_DISABLED=true است، بنابراین در بک‌اند هم باید آن را true کنیم.

 ما می‌توانیم متغیر محیطی `AUTH_DISABLED` را در بک‌اند تنظیم کنیم. اما اگر تنظیم نشده باشد، فرض می‌کنیم false است.

 برای ساده‌تر شدن، ما فقط dependency را تغییر می‌دهیم تا اگر AUTH_DISABLED=true بود، اجازه دسترسی بدون کاربر را بدهد.

 کد زیر را در نظر بگیرید:

 اما از آنجایی که ما نمی‌خواهیم کد را بیش از حد تغییر دهیم، و از آنجایی که در endpointها از `current_user` استفاده نمی‌کنیم، می‌توانیم dependency را به صورت زیر تغییر دهیم:

 ما یک تابع dependency جدید می‌سازیم که:

   auth_disabled = os.getenv("AUTH_DISABLED", "false").lower() == "true"

   if auth_disabled:
        return None
   else:
        return Depends(get_current_user)

 اما این کار درست نیست، زیرا در بخش else ما باید یک dependency برگردانیم. می‌توانیم به صورت زیر بنویسیم:

   if auth_disabled:
        return None
   else:
        from app.utils.security import get_current_user
        return get_current_user()

 اما این کار باعث می‌شود که dependency به صورت مستقیم فراخوانی شود، در حالی که FastAPI باید آن را مدیریت کند.

 در عوض، می‌توانیم دو dependency جداگانه داشته باشیم و بر اساس شرایط یکی را انتخاب کنیم. اما FastAPI اجازه نمی‌دهد که dependency را به صورت شرطی در پارامتر تابع endpoint تعریف کنیم.

 بنابراین، ما می‌توانیم dependency را به صورت یک تابع پیاده‌سازی کنیم که داخل آن، یا کاربر واقعی را برگرداند یا None.

 اما تابع `get_current_user` خودش یک dependency است که می‌تواند استثنا throw کند. ما می‌توانیم آن را در یک try-except بگیریم.

 پس تابع جدید به این صورت خواهد بود:

   async def get_current_user_or_none(
        current_user: Union[User, None] = Depends(get_current_user)
   ):
        return current_user

 اما این کار استثنا را catch نمی‌کند. زیرا اگر `get_current_user` استثنا بدهد، قبل از رسیدن به تابع ما، استثنا throw شده است.

 در FastAPI، می‌توانیم از `HTTPException` در dependencyها استفاده کنیم. اما ما می‌خواهیم در صورت استثنا، اگر AUTH_DISABLED=true بود، None برگردانیم.

 بنابراین، ما باید `get_current_user` را مستقیماً فراخوانی کنیم؟ اما `get_current_user` یک تابع است که به dependencyهای دیگری وابسته است (مثل توکن). بنابراین، ما می‌توانیم آن را به صورت یک dependency درون یک تابع دیگر فراخوانی کنیم.

 در FastAPI، می‌توانیم یک dependency را درون تابع دیگر فراخوانی کنیم. اما باید context مدیریت شود.

 راه ساده‌تر این است که یک dependency جدید بنویسیم که سعی کند `get_current_user` را فراخوانی کند و اگر خطای 401 داد، بررسی کند که اگر AUTH_DISABLED=true بود، None برگرداند.

 اما `get_current_user` ممکن است خطاهای دیگری هم بدهد. ما فقط خطای 401 را می‌خواهیم catch کنیم.

 بنابراین، کد زیر را می‌نویسیم:

   from fastapi import Request
   from app.utils.security import get_current_user

   async def get_current_user_or_none(request: Request):
        auth_disabled = os.getenv("AUTH_DISABLED", "false").lower() == "true"
        if auth_disabled:
            return None
        else:
            # سعی می‌کنیم کاربر را بگیریم
            try:
                return await get_current_user(request)
            except HTTPException as e:
                if e.status_code == 401:
                    # اگر احراز هویت غیرفعال بود، خطا را نادیده می‌گیریم و None برمی‌گردانیم
                    if auth_disabled:
                        return None
                    else:
                        raise e
                else:
                    raise e

 اما تابع `get_current_user` به چه پارامترهایی وابسته است؟ احتمالاً به Request وابسته است. بنابراین، ما باید request را به آن پاس بدهیم.

 اما در کد فعلی، `get_current_user` به صورت یک dependency تعریف شده که ممکن است به `Request` وابسته باشد. بنابراین، ما می‌توانیم آن را به صورت زیر فراخوانی کنیم:

   user = await get_current_user(request, ...)

 اما ممکن است `get_current_user` به چیزهای دیگری هم وابسته باشد. بنابراین، این روش قابل اطمینان نیست.

 از آنجایی که زمان محدود است و ما نمی‌خواهیم تغییرات بزرگی ایجاد کنیم، یک راه حل ساده‌تر این است که در این فایل، endpointها را طوری تغییر دهیم که اگر AUTH_DISABLED=true بود، dependency را نادیده بگیرند.

 اما در FastAPI، نمی‌توانیم به راحتی dependency را درون تابع endpoint حذف کنیم.

 بنابراین، ما می‌توانیم دو روتر جداگانه داشته باشیم؟ اما این کار منطقی نیست.

 با توجه به اینکه مشکل فقط در حالت توسعه است و AUTH_DISABLED در فرانت‌اند true است، ما در بک‌اند نیز باید AUTH_DISABLED را true کنیم.

 اما از آنجایی که در گزارش بررسی، خطا از بک‌اند 401 است، پس بک‌اند در حال حاضر AUTH_DISABLED=false است.

 بنابراین، ما باید در بک‌اند AUTH_DISABLED را true کنیم. اما از آنجایی که ما نمی‌توانیم محیط را تغییر دهیم، می‌توانیم کد را طوری تغییر دهیم که اگر AUTH_DISABLED=true بود، dependency را حذف کند.

 اما در FastAPI، یک راه این است که dependency را به صورت optional تعریف کنیم و سپس در بدنه تابع، اگر کاربر None بود و AUTH_DISABLED=false بود، خطا بدهیم.

 اما ما در این فایل، می‌توانیم یک تابع dependency بنویسیم که اگر AUTH_DISABLED=true بود، None برگرداند و در غیر این صورت، از `get_current_user` استفاده کند.

 با توجه به محدودیت‌ها، ما فرض می‌کنیم که `get_current_user` یک تابع است که می‌توان آن را فراخوانی کرد و به یک `Request` نیاز دارد.

 بنابراین، ما request را به عنوان dependency به تابع جدید اضافه می‌کنیم.

 کد نهایی:

 ما در این فایل، تابعی به نام `get_current_user_or_none` تعریف می‌کنیم که:
   - اگر AUTH_DISABLED=true بود، None برگرداند.
   - در غیر این صورت، سعی کند `get_current_user` را فراخوانی کند.

 اما برای فراخوانی `get_current_user`، باید همان dependencyهایی که `get_current_user` نیاز دارد را فراهم کنیم.

 از آنجایی که `get_current_user` احتمالاً به `Request` وابسته است، ما `Request` را به عنوان پارامتر می‌گیریم.

 سپس، ما `get_current_user` را import می‌کنیم و سعی می‌کنیم آن را فراخوانی کنیم.

 اما `get_current_user` ممکن است به چیزهای دیگری مثل دیتابیس وابسته باشد. بنابراین، ما باید تمام dependencyهای آن را فراهم کنیم.

 این کار بسیار پیچیده است.

 بنابراین، یک راه حل ساده‌تر: ما می‌توانیم endpointهای این روتر را در حالت AUTH_DISABLED=true بدون احراز هویت قرار دهیم.

 از آنجایی که این endpointها فقط آمار را برمی‌گردانند و احتمالاً در حالت توسعه نیاز به احراز هویت ندارند، می‌توانیم یک شرط در خود endpointها قرار دهیم.

 اما از آنجایی که endpointها سه تا هستند، می‌توانیم یک تابع کمکی بنویسیم که احراز هویت را بررسی کند.

 با توجه به زمان، من تصمیم می‌گیرم که dependency `get_current_user` را حذف کنیم و به جای آن، یک dependency اختیاری ایجاد کنیم که اگر AUTH_DISABLED=true بود، None برگرداند و اگر نبود، خطای 401 بدهد.

 اما برای خطای 401، ما باید خودمان بررسی کنیم.

 کد زیر را امتحان می‌کنیم:

 از آنجایی که `get_current_user` در صورت عدم وجود کاربر، `HTTPException` با وضعیت 401 می‌اندازد، ما می‌توانیم آن را catch کنیم.

 بنابراین، یک dependency جدید به نام `optional_auth` می‌سازیم:

   async def optional_auth(
        request: Request,
        db: AsyncSession = Depends(get_db)
   ):
        auth_disabled = os.getenv("AUTH_DISABLED", "false").lower() == "true"
        if auth_disabled:
            return None
        try:
            # فرض می‌کنیم که `get_current_user` به request و db وابسته است.
            # اما در فایل `app.utils.security` ممکن است به چیزهای دیگری وابسته باشد.
            # از آنجایی که نمی‌خواهیم کل وابستگی‌ها را تکرار کنیم، سعی می‌کنیم `get_current_user` را مستقیماً فراخوانی کنیم.
            # اما `get_current_user` یک تابع async است که به Request وابسته است.
            # در واقع، `get_current_user` به عنوان یک dependency تعریف شده که می‌تواند به چندین چیز وابسته باشد.
            # بنابراین، ما باید آن را به صورت یک dependency فراخوانی کنیم.
            # در FastAPI، می‌توانیم از `Depends(get_current_user)` درون یک تابع دیگر استفاده کنیم.
            # اما اینجا ما در یک تابع dependency هستیم، بنابراین می‌توانیم بگوییم:
            current_user = await get_current_user(request, db)
            return current_user
        except HTTPException as e:
            if e.status_code == 401 and auth_disabled:
                return None
            raise e

 اما این کار نیاز دارد که ما بدانیم `get_current_user` دقیقاً به چه پارامترهایی نیاز دارد.

 از آنجایی که این کار پیچیده است و ممکن است به تغییرات زیادی نیاز داشته باشد، و با توجه به اینکه این فقط یک فایل است و ما نمی‌توانیم کل سیستم را تغییر دهیم، من یک راه حل ساده‌تر پیشنهاد می‌دهم:

 ما در این فایل، dependency `get_current_user` را حذف می‌کنیم و به جای آن، مستقیماً در بدنه تابع، بررسی می‌کنیم که آیا AUTH_DISABLED=true است یا خیر. اگر true است، بدون احراز هویت ادامه می‌دهیم، در غیر این صورت، خطای 401 می‌دهیم.

 اما این کار به معنای دور زدن مکانیسم dependency است.

 از آنجایی که در گزارش بررسی، خطا 401 است و می‌گویند AUTH_DISABLED=true است، من فرض می‌کنم که باید احراز هویت را در بک‌اند غیرفعال کنیم.

 بنابراین، من کد را به صورت زیر تغییر می‌دهم:

   - ابتدا `import os` را اضافه می‌کنم.
   - سپس در هر endpoint، قبل از هر کاری، بررسی می‌کنم که اگر AUTH_DISABLED=true بود، بدون بررسی کاربر ادامه دهم، در غیر این صورت، `get_current_user` را فراخوانی کنم.

 اما از آنجایی که endpointها سه تا هستند، این کار تکرار می‌شود.

 بنابراین، من یک تابع کمکی در همین فایل تعریف می‌کنم:

   def check_auth():
        auth_disabled = os.getenv("AUTH_DISABLED", "false").lower() == "true"
        if not auth_disabled:
            # باید کاربر را بررسی کنیم
            # اما چطور؟ ما می‌توانیم `get_current_user` را فراخوانی کنیم.
            # برای این کار، نیاز به request داریم.
            # بنابراین، این روش در اینجا کار نمی‌کند.

 متأسفانه، این روش بدون دسترسی به request نمی‌شود.

 بنابراین، من به راه حل اول برمی‌گردم: ایجاد یک dependency جدید که بتواند request را بگیرد.

 از آنجایی که در فایل `app.utils.security`، تابع `get_current_user` احتمالاً به صورت زیر تعریف شده:

   async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):

 بنابراین، ما می‌توانیم در این فایل، یک dependency جدید ایجاد کنیم که هم request و هم db را بگیرد.

 سپس، اگر AUTH_DISABLED=true بود، None برگرداند، در غیر این صورت، `get_current_user` را فراخوانی کند.

 پس تغییرات نهایی:

 1. import os و import Request از fastapi.
 2. تعریف تابع `get_current_user_or_none`.
 3. تغییر endpointها به استفاده از `get_current_user_or_none`.

 اما توجه: در endpointها، ما از `db` هم استفاده می‌کنیم. بنابراین، اگر `get_current_user` به `db` نیاز داشته باشد، ما باید `db` را به آن پاس بدهیم.

 در کد فعلی، `get_current_user` احتمالاً از `Depends(get_db)` استفاده می‌کند. بنابراین، ما می‌توانیم `db` را از dependency بگیریم و به `get_current_user` پاس بدهیم.

 بنابراین، کد زیر را می‌نویسیم:

   from fastapi import Request

   async def get_current_user_or_none(
        request: Request,
        db: AsyncSession = Depends(get_db)
   ):
        auth_disabled = os.getenv("AUTH_DISABLED", "false").lower() == "true"
        if auth_disabled:
            return None
        try:
            from app.utils.security import get_current_user
            return await get_current_user(request, db)
        except HTTPException as e:
            if e.status_code == 401:
                # اگر 401 گرفتیم و auth_disabled هست، None برگردان
                if auth_disabled:
                    return None
                else:
                    raise e
            else:
                raise e

 سپس در endpointها، به جای `current_user = Depends(get_current_user)`، بنویسیم: `current_user = Depends(get_current_user_or_none)`

 اما در endpointها، ما از `db` هم استفاده می‌کنیم. بنابراین، `db` را دو بار داریم: یک بار برای خود endpoint و یک بار برای dependency. اما مشکلی نیست.

 با این حال، ممکن است `get_current_user` به چیزهای دیگری هم وابسته باشد. اما فعلاً همین را امتحان می‌کنیم.

 از آنجایی که در فایل `app.utils.security` ممکن است `get_current_user` به چیزهای دیگری وابسته باشد، این روش ممکن است کار نکند.

 اما با توجه به اینکه این یک پروژه کوچک است، فرض می‌کنیم که `get_current_user` فقط به `request` و `db` وابسته است.

 بنابراین، کد نهایی به صورت زیر خواهد بود:

 توجه: در endpointها، اگر `current_user` None باشد، ما باید بتوانیم ادامه دهیم. اما اگر None نباشد، یعنی کاربر معتبر است.

 اما از آنجایی که در endpointها از `current_user` استفاده نمی‌کنیم، مشکلی نیست.

 بنابراین، من کد را تغییر می‌دهم.

 همچنین، در تابع `get_current_user_or_none`، اگر auth_disabled=true باشد، None برمی‌گردانیم. در غیر این صورت، سعی می‌کنیم کاربر واقعی را برگردانیم.

 اگر در حالت auth_disabled=false و کاربری نبود، `get_current_user` خطای 401 می‌دهد و ما آن را بالا می‌فرستیم.

 پس کد کامل فایل با تغییرات:

 توجه: ما باید `HTTPException` را نیز import کنیم.

 همچنین، از آنجایی که `get_current_user` را درون try import می‌کنیم، ممکن است circular import نشود.

 اما بهتر است در بالای فایل import کنیم.

 من `get_current_user` را در بالای فایل import نمی‌کنم زیرا ممکن است به `get_db` وابسته باشد و `get_db` در این فایل import شده است. اما اگر درون تابع import کنیم، مشکلی پیش نمی‌آید.

 بنابراین، کد نهایی:

**نتیجه:**
```python
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import os

from app.database import get_db
from app.models.customer import Customer
from app.models.facility import Facility
from app.utils.security import get_current_user

router = APIRouter()

async def get_current_user_or_none(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Dependency that returns current user if authenticated, 
    or None if AUTH_DISABLED is True and no valid token is provided.
    """
    auth_disabled = os.getenv("AUTH_DISABLED", "false").lower() == "true"
    
    if auth_disabled:
        return None
    
    try:
        return await get_current_user(request, db)
    except HTTPException as e:
        if e.status_code == 401 and auth_disabled:
            return None
        raise e

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_or_none)
):
    """
    Get dashboard statistics.
    """
    # Check authentication if AUTH_DISABLED is False
    auth_disabled = os.getenv("AUTH_DISABLED", "false").lower() == "true"
    if not auth_disabled and not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Total customers count
        total_customers_result = await db.execute(
            select(func.count(Customer.id)).where(Customer.is_deleted == False)
        )
        total_customers = total_customers_result.scalar() or 0

        # Total facilities amount
        total_amount_result = await db.execute(
            select(func.sum(Facility.amount)).where(Facility.is_deleted == False)
        )
        total_amount = total_amount_result.scalar() or 0

        # Total outstanding
        total_outstanding_result = await db.execute(
            select(func.sum(Facility.outstanding)).where(Facility.is_deleted == False)
        )
        total_outstanding = total_outstanding_result.scalar() or 0

        # Facilities by type
        facilities_by_type_result = await db.execute(
            select(Facility.facility_type, func.count(Facility.id))
            .where(Facility.is_deleted == False)
            .group_by(Facility.facility_type)
        )
        facilities_by_type = dict(facilities_by_type_result.all())

        # Recent facilities (last 5)
        recent_facilities_result = await db.execute(
            select(Facility)
            .where(Facility.is_deleted == False)
            .order_by(Facility.created_at.desc())
            .limit(5)
        )
        recent_facilities = recent_facilities_result.scalars().all()

        # Customers by account type
        customers_by_type_result = await db.execute(
            select(Customer.account_type, func.count(Customer.id))
            .where(Customer.is_deleted == False)
            .group_by(Customer.account_type)
        )
        customers_by_type = dict(customers_by_type_result.all())

        return {
            "total_customers": total_customers,
            "total_amount": total_amount,
            "total_outstanding": total_outstanding,
            "facilities_by_type": facilities_by_type,
            "customers_by_type": customers_by_type,
            "recent_facilities": [
                {
                    "id": fac.id,
                    "name": fac.name,
                    "amount": fac