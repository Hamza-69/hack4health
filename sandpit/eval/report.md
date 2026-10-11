# Eval report

2026-10-11 03:11 UTC · model `openai:gpt-5.6-luna` · modules: moph, requests · 29 questions, 0 failed · latency median 8.8s, p90 13.5s, max 21.9s


Grade each row against its `expect` note: fill the grade column (ok / partial / wrong).

| # | question | lang | topic | tools | found | s | answer | grade |
|---|---|---|---|---|---|---|---|---|
| 1 | [demo_hernia_lb](#demo_hernia_lb) | lebanese | demo | search_ministry_site, search_services | 2/2 | 9.0 | إذا بيّك لبناني وما عنده أي تغطية تانية (ضمان، تعاونية، جيش/قوى أمن، … | |
| 2 | [demo_hernia_en](#demo_hernia_en) | english | demo | none | - | 2.7 | Does your dad have any other coverage (NSSF, cooperative, Army/securi… | |
| 3 | [demo_voice_lb](#demo_voice_lb) | lebanese | demo | search_services, search_ministry_site, get_contacts | 2/2 | 13.5 | مرحبا. لطلب استشفاء على نفقة وزارة الصحة لعملية فتق، الأوراق المطلوبة… | |
| 4 | [operation_arabizi](#operation_arabizi) | arabizi | covered operation | search_services | 1/1 | 20.3 | Marhaba. Fik t2addem talab esteshfa2 3a nafa2et Wizarit el Se7a, iza … | |
| 5 | [controller_doctor_msa](#controller_doctor_msa) | msa | covered operation | search_ministry_site, search_services, search_ministry_site | 3/3 | 11.5 | بحسب منشورات وزارة الصحة، الطبيب المراقب هو الطبيب المعيّن من قبل الو… | |
| 6 | [cancer_aman_lb](#cancer_aman_lb) | lebanese | AMAN medicine | search_services, list_services, get_service, get_service | 3/3 | 12.1 | سلامتها أمّك. للحصول على دواء السرطان من وزارة الصحة: 1. إذا أول مرة:… | |
| 7 | [ms_aman_en](#ms_aman_en) | english | AMAN medicine | search_services, get_service | 2/2 | 9.1 | You can apply online through the Ministry of Public Health’s “Multipl… | |
| 8 | [haemophilia_arabizi](#haemophilia_arabizi) | arabizi | WhatsApp 81/348838 | search_services | 1/1 | 21.9 | Eh, fi talab msa3det adwiye lal hemophilia men wizaret el se7a. El sh… | |
| 9 | [transplant_msa](#transplant_msa) | msa | WhatsApp 81/348838 | search_services, get_service | 2/2 | 9.7 | يمكنك التقدّم عبر خدمة وزارة الصحة الخاصة بأدوية زراعة الكلى أو الأعض… | |
| 10 | [humira_lb](#humira_lb) | lebanese | Humira | search_services, lookup_drug | 2/2 | 8.7 | إيه، Humira 40mg/0.4ml موجود على لائحة الأدوية التي تؤمّنها وزارة الص… | |
| 11 | [ivig_en](#ivig_en) | english | IVIG | search_ministry_site, search_services | 2/2 | 8.9 | Yes. The Ministry has a service for IVIG assistance specifically for … | |
| 12 | [complaint_lb](#complaint_lb) | lebanese | complaints | search_ministry_site, get_contacts | 1/1 | 9.8 | إذا المستشفى عم يطلب منك فروقات مالية رغم إنو دخولك مغطّى 100% على حس… | |
| 13 | [hotlines_en](#hotlines_en) | english | hotlines | get_contacts | - | 4.0 | The Ministry of Public Health’s main hotline is 1214. Other numbers: … | |
| 14 | [panadol_lb](#panadol_lb) | lebanese | drug price | lookup_drug | 1/1 | 4.4 | حسب لائحة وزارة الصحة بتاريخ 10-10-2026: - Panadol Actifast 500mg: 15… | |
| 15 | [augmentin_arabizi](#augmentin_arabizi) | arabizi | drug price | lookup_drug | 1/1 | 10.8 | Eh, Augmentin 1g (875mg amoxicillin + 125mg clavulanic acid), tablet,… | |
| 16 | [lantus_en](#lantus_en) | english | drug price | lookup_drug | 1/1 | 4.2 | The Ministry’s database lists LANTUS (insulin glargine 100 IU/ml) at … | |
| 17 | [glucophage_ar](#glucophage_ar) | lebanese | drug price | lookup_drug | 1/1 | 4.3 | سعر غلوكوفاج 850 ملغ هو 572,634 ليرة لبنانية، حسب لائحة وزارة الصحة ب… | |
| 18 | [hospitals_tripoli_lb](#hospitals_tripoli_lb) | lebanese | facilities | find_facilities | 1/1 | 3.7 | في مستشفيين حكوميين بقضاء طرابلس: 1. مستشفى أورانج ناسو الحكومي الهات… | |
| 19 | [phc_saida_en](#phc_saida_en) | english | facilities | find_facilities | 1/1 | 5.1 | Here are primary health care centres in Saida: 1. Saida PHC Center — … | |
| 20 | [pharmacy_tripoli_arabizi](#pharmacy_tripoli_arabizi) | arabizi | facilities | find_facilities | 0/1 | 4.2 | Ma la2et la2e7et saydaliye b Trablos bi dalil el Wezara, w el la2e7a … | |
| 21 | [stroke_coverage_msa](#stroke_coverage_msa) | msa | recent announcement | search_ministry_site, search_services | 2/2 | 8.8 | نعم. أطلقت وزارة الصحة في 11 شباط 2026 تغطية استشفائية للجلطة أو السك… | |
| 22 | [uninsured_coverage_lb](#uninsured_coverage_lb) | lebanese | recent announcement | search_ministry_site, search_services | 2/2 | 10.2 | لا، مش صحيح إنو التغطية صارت بس للنازحين. بحسب آخر توضيح منشور من الو… | |
| 23 | [clarify_meds_lb](#clarify_meds_lb) | lebanese | clarifying question | search_services | 1/1 | 6.7 | أكيد. وزارة الصحة بتقدّم مساعدة أدوية لفئات وأمراض محدّدة، والطلب بيخ… | |
| 24 | [unknown_ivf_en](#unknown_ivf_en) | english | not in data | search_ministry_site, search_services, search_ministry_site… | 1/3 | 10.8 | I couldn’t confirm from the Ministry’s published information that IVF… | |
| 25 | [unknown_status_lb](#unknown_status_lb) | lebanese | not in data | search_ministry_site, get_contacts, report_unanswered | 1/1 | 10.0 | ما بقدر شوف حالة ملفك مباشرة على منصة أمان. لمتابعته، تواصل مع وزارة … | |
| 26 | [emergency_lb](#emergency_lb) | lebanese | emergency | none | - | 1.9 | اتصلي فورًا بالصليب الأحمر اللبناني على ١٤٠، أو خديه على أقرب قسم طوا… | |
| 27 | [diagnosis_en](#diagnosis_en) | english | diagnosis | none | - | 3.4 | I can’t diagnose this or recommend an antibiotic. Fever for 3 days wi… | |
| 28 | [capabilities_lb](#capabilities_lb) | lebanese | scope | none | - | 2.2 | مرحبا! فيّي ساعدك بخدمات وزارة الصحة، طلبات الاستشفاء، أسعار وتوفّر ا… | |
| 29 | [out_of_scope_en](#out_of_scope_en) | english | scope | none | - | 8.7 | I can help with Lebanon Ministry of Public Health services, medicines… | |

<a id="demo_hernia_lb"></a>

## 1. demo_hernia_lb

**Question** (lebanese, demo):

> بيي بدو يعمل عملية فتق، الوزارة بتغطيها؟

**Expect:** Asks whether the dad has NSSF, army, COOP or private insurance (ministry coverage is only for people with no other cover), or answers conditionally on that. Explains the hospitalization request (service 84, form MPH2-3): medical report stamped by the hospital with 'على نفقة وزارة الصحة', NSSF certificate of non-coverage (under 2 months old), individual ikhraj qaid, written pledge of no other cover; approval valid 15 days, renewed by the ministry's controller doctor (الطبيب المراقب). Links moph.gov.lb/ar/AdministrativeServices/details/84. Must not invent a hernia-specific rule (the crawl has none).

**Answer** (9.0s, first text at 9.0s, 2 model steps):

> إذا بيّك لبناني وما عنده أي تغطية تانية (ضمان، تعاونية، جيش/قوى أمن، أو تأمين)، فالوزارة بتغطي الاستشفاء للبنانيين غير المضمونين، بس ما فيني أكّد من المعلومات المتاحة إن عملية الفتق تحديدًا مشمولة.
>
> لازم تسألوا المستشفى أو تتصلوا على 1787 للتأكد من تغطية العملية. طلب الاستشفاء بيتقدّم بمركز إعطاء البطاقات بئر حسن، الجناح، قرب أوجيرو، من الاثنين للسبت.
>
> التفاصيل:
> https://www.moph.gov.lb/ar/AdministrativeServices/details/84
>
> إذا بتحب، فيّي حضّرلكن طلب الاستشفاء.

**Tools:**

1. `moph__search_ministry_site` `{"query": "تغطية وزارة الصحة عملية فتق شروط المستفيدين"}` → found, 5 results, 5 strong
2. `moph__search_services` `{"query": "طلب استشفاء على نفقة وزارة الصحة عملية فتق الشروط المستندات"}` → found, 5 results, 5 strong

<details><summary>Result 1: moph__search_ministry_site (first 2000 of 7957 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "kind": "document",
      "title": "letter26-1-3165",
      "date": "2026-01-30",
      "text": "الجمهورية اللبنانية\nوزارة الصحة العامة\nالوزير\nرقم الصادر: ٢٦٥/١/٢٦\nرقم المحفوظات: ١/١ - ١٤٠٢ - ٣/١٨\nبيروت في: ٢٠٢١/١/٢٠\nكتاب تعميمي\nموجه الى جميع المستشفيات الحكومية\nيطلب من جميع المستشفيات الحكومية على كافة الاراضي اللبنانية، تغطية حاملي بطاقة عناية (النازحين من القرى الحدودية الجنوبية)، ١٠٠٪ على نفقة وزارة الصحة العامة، عن الأعمال الطبية المغطاة بموجب القرارات الصادرة عن وزير الصحة العامة، أياً كانت جهتهم الضامنة.\nعلى ان تصدر بطاقات تغطية للمرضى غير المضمونين بنسبة ١٠٠٪ مباشرة عند الإصدار، وكتب وزير (فرق تعرفة الجهة الضامنة) للمرضى المضمونين.\nيبلغ:\n- المديرية العامة للصحة\n- مدير العناية الطبية\n- مصلحة المستشفيات والمستوصفات\n- دائرة المستشفيات والمستوصفات\n- المستشفيات الحكومية\n- مراكز اصدار البطاقات\n- الأطباء المراقبين\n- لجنة تدقيق الفواتير\n- المحفوظات\nوزير الصحة العامة\nد. ركان ناصر الدين\nبئر حسن - مبنى وزارة الصحة - بيروت، لبنان - هاتف: +٩٦١ ١ ٨٣٠٣٠٠ - فاكس: +٩٦١ ١ ٨٣٠٧٣٣ - الخط الساخن - ١٢١٤، البريد الإلكتروني: ministeroffice@public-health.gov.lb",
      "url": "https://www.moph.gov.lb/userfiles/files/laws/letter26-1-3165.pdf",
      "found_on": "https://www.moph.gov.lb/ar/Pages/127/82443/%D8%A8%D8%B7%D9%84%D8%A8-%D9%85%D9%86-%D9%88%D8%B2%D9%8A%D8%B1-%D8%A7%D9%84%D8%B5%D8%AD%D8%A9-%D8%AA%D8%BA%D8%B7%D9%8A%D8%A9-%D8%B5%D8%AD%D9%8A%D8%A9-100-%D9%84%D9%84%D9%86%D8%A7%D8%B2%D8%AD%D9%8A%D9%86-%D9%85%D9%86-%D8%A7%D9%84%D9%82%D8%B1%D9%89-%D8%A7%D9%84%D8%AD%D8%AF%D9%88%D8%AF%D9%8A%D8%A9-%D8%A7%D9%84%D8%AC%D9%86%D9%88%D8%A8%D9%8A%D8%A9",
      "found_on_title": "بطلب من وزير الصحة: تغطية صحية 100% للنازحين من القرى الحدودية الجنوبية"
    },
    {
      "match": "strong",
      "kind": "page",
      "title": "وزيرا الصحة والشؤون الاجتماعية أعلنا آلية التغطية الصحية لنازحي الحافة الأمامية",
      "date": "2026-01-30",
      "text": "وقال وزير الصحة العامة إنه سيتم الإستحصال على لوائح بال
```

</details>

<details><summary>Result 2: moph__search_services (first 2000 of 6857 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "service_id": 84,
      "title": "الإستفادة من التغطية الصحية - طلب إستشفاء",
      "who_is_eligible": [
        "يعتبر حضور المريض الزامي وفي حال عدم تمكنه على احد افراد عائلته المقربين احضار الاوراق المطلوبة مع المستندات التى تثبت صلة القرابة",
        "تعتبر المعاملة صالحة لمدة 15 يوما تجدد بواسطة الطبيب المراقب والمعين من قبل وزارة الصحة وفي حال عدم دخول المريض تعتبر المعاملة ملغاة بعد يومين من تاريخ اصدارها",
        "لا يحق للمستفيدين من تعاونية موظفين الدولة والجيش و الامن الداخلي وشركات التأمين الاستفادة من التغطية الصحية في وزارة الصحة العامة"
      ],
      "required_documents": [
        "تقرير طبي نموذجي مفصل مع تاريخ الدخول,ختم المستشفى, ختم وتوقيع الطبيب مع رقم انتسابه الى النقابة مع عبارة \"على نفقة وزارة الصحة\"",
        "افادة من الضمان الاجتماعي (المركز الرئيسي-منطقة الكولا) تفيد بعدم استفادة المريض من التغطية الصحية في الضمان الاجتماعي على الا تتجاوز الافادة مدة الشهرين",
        "صورة اصلية عن اخراج القيد الفردي + نسخة عنه ويجب ان يكون عليه صورة صاحب العلاقة اذا كان عمره اكثر من خمس سنوات ووثيقة ولادة للمولود الجديد غير المذكور على اخراج القيد وللاشخاص المجنسين يجب ابراز ملحق الجريدة الرسمية الخاص بالتجنيس",
        "تعهد خطي من المريض بعدم الإستفادة من تعاونية الموظفين أو الجيش أو الدرك أو أية جهة ضامنة أخرى"
      ],
      "processing_time": "في يوم تقديم الطلب",
      "form_number": "MPH2-3",
      "forms": [
        {
          "name": "MPH2-3",
          "url": "https://www.moph.gov.lb/AdministrativeServices/download/1296"
        }
      ],
      "apply_online": false,
      "office": {
        "directorate": "مركز اعطاء البطاقات",
        "unit": "مصلحة المستشفيات والمستوصفات والمهن الطبية - مديرية العناية الطبية",
        "address": "بئر حسن، الجناح، قرب أوجيرو",
        "hours": "من الاثنين الى السبت"
      },
      "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/84"
    },
    {
      "match": "strong",
      "service_id": 187,
      "tit
```

</details>

<a id="demo_hernia_en"></a>

## 2. demo_hernia_en

**Question** (english, demo):

> My dad needs a hernia operation, does the ministry cover it?

**Expect:** Same as demo_hernia_lb, in English: asks about NSSF or other cover, lists the hospitalization request documents (medical report 'at the ministry's expense', NSSF non-coverage certificate, ikhraj qaid, pledge), 15-day validity renewed by the controller doctor, office in Bir Hassan (Jnah, near Ogero), link to AdministrativeServices/details/84. No hernia-specific claims.

**Answer** (2.7s, first text at 2.7s, 1 model steps):

> Does your dad have any other coverage (NSSF, cooperative, Army/security forces, or private insurance), and what is his nationality?

**Tools:** none


<a id="demo_voice_lb"></a>

## 3. demo_voice_lb

**Question** (lebanese, demo):

> [voice note] مرحبا، بدي اعرف شو الأوراق يلي بحتاجها لعملية فتق على حساب وزارة الصحة

**Expect:** Treats the [voice note] marker as the user speaking. Lists the documents for the hospitalization request (service 84): medical report with 'على نفقة وزارة الصحة', NSSF non-coverage certificate, ikhraj qaid, pledge; mentions the controller doctor renews it every 15 days; links details/84. Replies in Lebanese Arabic.

**Answer** (13.5s, first text at 13.5s, 3 model steps):

> مرحبا. لطلب استشفاء على نفقة وزارة الصحة لعملية فتق، الأوراق المطلوبة هي:
>
> 1. تقرير طبي نموذجي مفصّل، فيه تاريخ الدخول، ختم المستشفى، ختم وتوقيع الطبيب ورقم انتسابه للنقابة، ومذكور عليه «على نفقة وزارة الصحة».
> 2. إفادة من الضمان الاجتماعي من المركز الرئيسي بمنطقة الكولا، تثبت إنّ المريض ما بيستفيد من تغطية الضمان، وما يكون عمرها أكتر من شهرين.
> 3. إخراج قيد فردي أصلي مع نسخة عنه، ويكون عليه صورة إذا عمر المريض فوق ٥ سنين.
> 4. تعهّد خطّي من المريض إنّه ما عنده تغطية من تعاونية موظفي الدولة أو الجيش أو قوى الأمن أو أي جهة ضامنة تانية.
>
> حضور المريض إلزامي. وإذا ما بيقدر، في قريب مقرّب يقدّم الأوراق مع مستند يثبت صلة القرابة.
>
> تُقدَّم المعاملة بمركز إعطاء البطاقات، مصلحة المستشفيات والمستوصفات والمهن الطبية، بئر حسن–الجناح قرب أوجيرو، من الاثنين للسبت. إنجازها مذكور إنّه بنفس يوم التقديم.
>
> ما قدرت أكد من المصدر إنّ عملية الفتق مغطّاة تحديداً، لذلك اتصل على 1787 للتأكد من التغطية وساعات العمل، أو 01/832700 لقبول المرضى بالمستشفيات.
>
> التفاصيل الرسمية:
> https://www.moph.gov.lb/ar/AdministrativeServices/details/84
>
> هل المريض ما عنده أي تغطية تانية مثل الضمان، تعاونية، جيش، قوى أمن أو تأمين؟

**Tools:**

1. `moph__search_services` `{"query": "طلب استشفاء على نفقة وزارة الصحة عملية فتق الأوراق المطلوبة"}` → found, 5 results, 5 strong
2. `moph__search_ministry_site` `{"query": "عملية فتق على نفقة وزارة الصحة الأوراق المطلوبة تغطية"}` → found, 5 results, 2 strong
3. `moph__get_contacts` `{}` → 4 contacts

<details><summary>Result 1: moph__search_services (first 2000 of 6158 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "service_id": 84,
      "title": "الإستفادة من التغطية الصحية - طلب إستشفاء",
      "who_is_eligible": [
        "يعتبر حضور المريض الزامي وفي حال عدم تمكنه على احد افراد عائلته المقربين احضار الاوراق المطلوبة مع المستندات التى تثبت صلة القرابة",
        "تعتبر المعاملة صالحة لمدة 15 يوما تجدد بواسطة الطبيب المراقب والمعين من قبل وزارة الصحة وفي حال عدم دخول المريض تعتبر المعاملة ملغاة بعد يومين من تاريخ اصدارها",
        "لا يحق للمستفيدين من تعاونية موظفين الدولة والجيش و الامن الداخلي وشركات التأمين الاستفادة من التغطية الصحية في وزارة الصحة العامة"
      ],
      "required_documents": [
        "تقرير طبي نموذجي مفصل مع تاريخ الدخول,ختم المستشفى, ختم وتوقيع الطبيب مع رقم انتسابه الى النقابة مع عبارة \"على نفقة وزارة الصحة\"",
        "افادة من الضمان الاجتماعي (المركز الرئيسي-منطقة الكولا) تفيد بعدم استفادة المريض من التغطية الصحية في الضمان الاجتماعي على الا تتجاوز الافادة مدة الشهرين",
        "صورة اصلية عن اخراج القيد الفردي + نسخة عنه ويجب ان يكون عليه صورة صاحب العلاقة اذا كان عمره اكثر من خمس سنوات ووثيقة ولادة للمولود الجديد غير المذكور على اخراج القيد وللاشخاص المجنسين يجب ابراز ملحق الجريدة الرسمية الخاص بالتجنيس",
        "تعهد خطي من المريض بعدم الإستفادة من تعاونية الموظفين أو الجيش أو الدرك أو أية جهة ضامنة أخرى"
      ],
      "processing_time": "في يوم تقديم الطلب",
      "form_number": "MPH2-3",
      "forms": [
        {
          "name": "MPH2-3",
          "url": "https://www.moph.gov.lb/AdministrativeServices/download/1296"
        }
      ],
      "apply_online": false,
      "office": {
        "directorate": "مركز اعطاء البطاقات",
        "unit": "مصلحة المستشفيات والمستوصفات والمهن الطبية - مديرية العناية الطبية",
        "address": "بئر حسن، الجناح، قرب أوجيرو",
        "hours": "من الاثنين الى السبت"
      },
      "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/84"
    },
    {
      "match": "strong",
      "service_id": 121,
      "tit
```

</details>

<details><summary>Result 2: moph__search_ministry_site (first 2000 of 8357 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "weak",
      "kind": "document",
      "title": "letter26-1-3165",
      "date": "2026-01-30",
      "text": "الجمهورية اللبنانية\nوزارة الصحة العامة\nالوزير\nرقم الصادر: ٢٦٥/١/٢٦\nرقم المحفوظات: ١/١ - ١٤٠٢ - ٣/١٨\nبيروت في: ٢٠٢١/١/٢٠\nكتاب تعميمي\nموجه الى جميع المستشفيات الحكومية\nيطلب من جميع المستشفيات الحكومية على كافة الاراضي اللبنانية، تغطية حاملي بطاقة عناية (النازحين من القرى الحدودية الجنوبية)، ١٠٠٪ على نفقة وزارة الصحة العامة، عن الأعمال الطبية المغطاة بموجب القرارات الصادرة عن وزير الصحة العامة، أياً كانت جهتهم الضامنة.\nعلى ان تصدر بطاقات تغطية للمرضى غير المضمونين بنسبة ١٠٠٪ مباشرة عند الإصدار، وكتب وزير (فرق تعرفة الجهة الضامنة) للمرضى المضمونين.\nيبلغ:\n- المديرية العامة للصحة\n- مدير العناية الطبية\n- مصلحة المستشفيات والمستوصفات\n- دائرة المستشفيات والمستوصفات\n- المستشفيات الحكومية\n- مراكز اصدار البطاقات\n- الأطباء المراقبين\n- لجنة تدقيق الفواتير\n- المحفوظات\nوزير الصحة العامة\nد. ركان ناصر الدين\nبئر حسن - مبنى وزارة الصحة - بيروت، لبنان - هاتف: +٩٦١ ١ ٨٣٠٣٠٠ - فاكس: +٩٦١ ١ ٨٣٠٧٣٣ - الخط الساخن - ١٢١٤، البريد الإلكتروني: ministeroffice@public-health.gov.lb",
      "url": "https://www.moph.gov.lb/userfiles/files/laws/letter26-1-3165.pdf",
      "found_on": "https://www.moph.gov.lb/ar/Pages/127/82443/%D8%A8%D8%B7%D9%84%D8%A8-%D9%85%D9%86-%D9%88%D8%B2%D9%8A%D8%B1-%D8%A7%D9%84%D8%B5%D8%AD%D8%A9-%D8%AA%D8%BA%D8%B7%D9%8A%D8%A9-%D8%B5%D8%AD%D9%8A%D8%A9-100-%D9%84%D9%84%D9%86%D8%A7%D8%B2%D8%AD%D9%8A%D9%86-%D9%85%D9%86-%D8%A7%D9%84%D9%82%D8%B1%D9%89-%D8%A7%D9%84%D8%AD%D8%AF%D9%88%D8%AF%D9%8A%D8%A9-%D8%A7%D9%84%D8%AC%D9%86%D9%88%D8%A8%D9%8A%D8%A9",
      "found_on_title": "بطلب من وزير الصحة: تغطية صحية 100% للنازحين من القرى الحدودية الجنوبية"
    },
    {
      "match": "weak",
      "kind": "page",
      "title": "الصحة تؤكد التغطية المستمرة لعلاج لارا حايك وتعلن عن التغطية الكاملة بنسبة 100 % للعمليات الجراحية لجرحى المرفأ",
      "date": "2026-08-05",
      "text": "Date: 05/08/2026\nAuthor: م
```

</details>

<details><summary>Result 3: moph__get_contacts</summary>

```
{
  "contacts": [
    {
      "contact": "1214: Ministry of Public Health hotline and complaints office (info@moph.gov.lb), also for cancer and intractable-disease medicines",
      "source_url": "https://www.moph.gov.lb/ar/contact"
    },
    {
      "contact": "1787: questions about the ministry's emergency and hospitalisation cover (working hours); hospitalisation for displaced people",
      "source_url": "https://www.moph.gov.lb/ar/Media/view/85973"
    },
    {
      "contact": "01/832700: hotline for patient admission to hospitals",
      "source_url": "https://www.moph.gov.lb/ar/complaints"
    },
    {
      "contact": "1564: mental health support line",
      "source_url": "https://www.moph.gov.lb/ar/Media/view/82829"
    }
  ]
}
```

</details>

<a id="operation_arabizi"></a>

## 4. operation_arabizi

**Question** (arabizi, covered operation):

> marhaba, baddi a3mel 3amaliye bel mestashfa 3a 7sab el wizara, shu lazem a3mel?

**Expect:** Replies in Arabizi (or Latin script). Asks or conditions on NSSF/other insurance. Gives the hospitalization request steps and documents (service 84) and the controller doctor's role; links details/84.

**Answer** (20.3s, first text at 20.3s, 2 model steps):

> Marhaba. Fik t2addem talab esteshfa2 3a nafa2et Wizarit el Se7a, iza ma 3andak ta2min tene. Ma byestafid yalle 3andon daman ejteme3e, Ta3aweniyet el mwazzafin, el jesh, el derak, aw cherket ta2min.
>
> Lazem:
>
> 1. Taqrir tebbe mfassal 3a wara2it el mestashfa, fiya tari5 el do5oul, 5atmet el mestashfa, taw2i3 el tabib w ra2em entisabo, w maktoub “3a nafa2et Wizarit el Se7a”.
> 2. Ifede men el daman el ejteme3e bt2akked enno ma 3andak ta8tiye, ma tkoun 2adem men shahrein.
> 3. E5raj 2eid farde asle + nes5a 3anno، w lazem ykoun 3leya soura iza 3omrak faw2 5 snin.
> 4. Ta3ahhod 5atte enno ma 3andak ta8tiye men ay jeha damne tene.
>
> Bt2addem el talab bi Markaz e3ta2 el bita2at، Bir Hassan, el Jnah, 7add Ogero، men el tnen lal sebt. El mo3amale btenjaz bi nafs nhar el ta2dim.
>
> El formulaire MPH2-3:
> https://www.moph.gov.lb/AdministrativeServices/download/1296
>
> Saf7et el khidme:
> https://www.moph.gov.lb/ar/AdministrativeServices/details/84
>
> Fik teb3atle el tafasil w el souwar، w bsa3dak 7addir el talab w 2addmo.

**Tools:**

1. `moph__search_services` `{"query": "طلب استشفاء على نفقة وزارة الصحة لإجراء عملية في المستشفى الشروط المستندات ومكان التقديم"}` → found, 5 results, 5 strong

<details><summary>Result 1: moph__search_services (first 2000 of 6356 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "service_id": 84,
      "title": "الإستفادة من التغطية الصحية - طلب إستشفاء",
      "who_is_eligible": [
        "يعتبر حضور المريض الزامي وفي حال عدم تمكنه على احد افراد عائلته المقربين احضار الاوراق المطلوبة مع المستندات التى تثبت صلة القرابة",
        "تعتبر المعاملة صالحة لمدة 15 يوما تجدد بواسطة الطبيب المراقب والمعين من قبل وزارة الصحة وفي حال عدم دخول المريض تعتبر المعاملة ملغاة بعد يومين من تاريخ اصدارها",
        "لا يحق للمستفيدين من تعاونية موظفين الدولة والجيش و الامن الداخلي وشركات التأمين الاستفادة من التغطية الصحية في وزارة الصحة العامة"
      ],
      "required_documents": [
        "تقرير طبي نموذجي مفصل مع تاريخ الدخول,ختم المستشفى, ختم وتوقيع الطبيب مع رقم انتسابه الى النقابة مع عبارة \"على نفقة وزارة الصحة\"",
        "افادة من الضمان الاجتماعي (المركز الرئيسي-منطقة الكولا) تفيد بعدم استفادة المريض من التغطية الصحية في الضمان الاجتماعي على الا تتجاوز الافادة مدة الشهرين",
        "صورة اصلية عن اخراج القيد الفردي + نسخة عنه ويجب ان يكون عليه صورة صاحب العلاقة اذا كان عمره اكثر من خمس سنوات ووثيقة ولادة للمولود الجديد غير المذكور على اخراج القيد وللاشخاص المجنسين يجب ابراز ملحق الجريدة الرسمية الخاص بالتجنيس",
        "تعهد خطي من المريض بعدم الإستفادة من تعاونية الموظفين أو الجيش أو الدرك أو أية جهة ضامنة أخرى"
      ],
      "processing_time": "في يوم تقديم الطلب",
      "form_number": "MPH2-3",
      "forms": [
        {
          "name": "MPH2-3",
          "url": "https://www.moph.gov.lb/AdministrativeServices/download/1296"
        }
      ],
      "apply_online": false,
      "office": {
        "directorate": "مركز اعطاء البطاقات",
        "unit": "مصلحة المستشفيات والمستوصفات والمهن الطبية - مديرية العناية الطبية",
        "address": "بئر حسن، الجناح، قرب أوجيرو",
        "hours": "من الاثنين الى السبت"
      },
      "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/84"
    },
    {
      "match": "strong",
      "service_id": 145,
      "tit
```

</details>

<a id="controller_doctor_msa"></a>

## 5. controller_doctor_msa

**Question** (msa, covered operation):

> ما هو دور الطبيب المراقب في المستشفى، وكيف أمدد إقامة مريض على نفقة الوزارة؟

**Expect:** Says the ministry-appointed controller doctor renews the hospitalization approval (valid 15 days) and must co-sign extensions. Extension of stay is service 81 (form MPH2-6): a medical report for the extension signed by the treating doctor and the controller doctor, processed on the spot. Links details/81 and/or details/84.

**Answer** (11.5s, first text at 11.5s, 3 model steps):

> بحسب منشورات وزارة الصحة، الطبيب المراقب هو الطبيب المعيّن من قبل الوزارة، ويقوم بتجديد معاملة الاستشفاء عند الحاجة. ولتمديد إقامة المريض، يجب أن يوقّع الطبيب المعالج والطبيب المراقب على طلب التمديد.
>
> الخطوات والمطلوب:
>
> 1. إعداد تقرير طبي خاص بتمديد الاستشفاء.
> 2. توقيعه وختمه من الطبيب المعالج والطبيب المراقب.
> 3. تقديم المعاملة إلى:
> مديرية العناية الطبية – مصلحة المستشفيات والمستوصفات والمهن الطبية
> بئر حسن، الجناح، قرب أوجيرو
> خلال أيام العمل الرسمي.
> 4. تعبئة النموذج MPH2-6:
> https://www.moph.gov.lb/AdministrativeServices/download/1432
>
> تُنجز المعاملة في حينه. للاستفسار: hospitals@moph.gov.lb
>
> الصفحة الرسمية:
> https://www.moph.gov.lb/ar/AdministrativeServices/details/81
>
> المصدر لا يوضح تفاصيل إضافية عن صلاحيات الطبيب المراقب داخل المستشفى beyond توقيعه وتجديده للمعاملة.

**Tools:**

1. `moph__search_ministry_site` `{"query": "دور الطبيب المراقب في المستشفى وزارة الصحة العامة"}` → found, 5 results, 5 strong
2. `moph__search_services` `{"query": "تمديد إقامة مريض على نفقة وزارة الصحة طلب استشفاء الطبيب المراقب"}` → found, 5 results, 5 strong
3. `moph__search_ministry_site` `{"query": "الطبيب المراقب المعين من قبل وزارة الصحة مهامه الاستشفاء تمديد الإقامة"}` → found, 5 results, 2 strong

<details><summary>Result 1: moph__search_ministry_site (first 2000 of 5985 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "kind": "page",
      "title": "وزارة الصحّة العامة",
      "text": "المساعدة على اعداد مشروع الموازنة المختصة بتنفيذ الخطة العامة والمتوافقة مع البرنامج السنوي للعمل لجهة انطباق الاعتمادات على المدى المحدد للخطة.\nتعيين الأبحاث اللازمة في المجالات الصحية واعدادها او اقتراح تكليف الجهات المحلية او الدولية المؤهلة للقيام بذلك، وتقييم النتائج المترتبة على هذه الابحاث.\nالتقدم باقتراحات المشاريع والبرامج والخطط اللازمة لتطوير القطاع الصحي للجهات المحلية والدولية وادارتها وتقييمها ومراقبة تنفيذها.\nالقيام بكافة المهام والمسؤوليات التي يمكن ان يكلفها بها المدير العام.\nدائرة الرقابة على المستشفيات الحكومية\nوتقوم بالمهام التالية:\nاقتراح تنسيق العمل بين جميع المؤسسات العامة التي تتولى ادارة المستشفيات الحكومية في سبيل التكامل في الخدمات الاستشفائية العامة.\nاقتراح تحديد الفروع الطبية والاختصاصات والمعدات الطبية المتطورة في كل من المستشفيات\nمراقبة نوعية وكلفة الخدمات الطبية المقدمة للمريض في المستشفى العام.\nاقتراح اعتماد المستشفيات العامة كمراكز للرصد الوبائي والاحصاءات الحيوية والدراسات الاستشفائية كالادارة الصحية وتحليل الخدمات المختلفة.\nاقتراح تحديد الاسس والمقاييس الفنية لبدائل الاستشفاء كالاستشفاء النهاري والخدمات الجراحية السريعة والاستشفاء المنزلي وسواه.",
      "url": "https://www.moph.gov.lb/ar/about"
    },
    {
      "match": "strong",
      "kind": "news",
      "title": "Announcements",
      "date": "2016-04-26",
      "text": "تأجيل الامتحانات للحصول على إذن مزاولة المهنة لمراقب صحي\n٢٠١٥/٢/٢٠\nأعلنت وزارة الصحة العامة عن تأجيل الامتحانات للحصول على إذن مزاولة المهنة لمراقب صحي من نهار غد الى السبت المقبل الموافق في 28/2/2015.\nاجراء مباراة لوظيفة مراقب صحي لدى وزارة الصحة\n٢٠١٥/١/٢٩\nقرّر وزير الصحة العامة وائل أبو فاعور إجراء امتحانات الكفاءة لطلاب إجازة ممارسة مهنة مراقب صحي من الحائزين على شهادات البكالوريا الفنية في حقل المراقبة الصحية والصادرة عن معهد متخصص معترف به رسمياً من الحكومة اللبنانية. وذلك في تمام الساعة التاسعة من صباح يوم السبت الواقع فيه 21 / 2 / 2015 في مبنى وزارة
```

</details>

<details><summary>Result 2: moph__search_services (first 2000 of 5718 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "service_id": 81,
      "title": "تمديد إقامة في المستشفى",
      "who_is_eligible": [
        "توقيع الطبيب المعالج والطبيب المراقب في المستشفى"
      ],
      "required_documents": [
        "التقرير الطبي الخاص بتمديد الإستشفاء"
      ],
      "processing_time": "في حينه",
      "form_number": "MPH2-6",
      "forms": [
        {
          "name": "MPH2-6",
          "url": "https://www.moph.gov.lb/AdministrativeServices/download/1432"
        }
      ],
      "apply_online": false,
      "office": {
        "directorate": "مديرية العناية الطبية",
        "unit": "مصلحة المستشفيات والمستوصفات والمهن الطبية",
        "address": "بئر حسن، الجناح، قرب أوجيرو",
        "email": "hospitals@moph.gov.lb",
        "hours": "طوال أيام العمل الرسمي"
      },
      "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/81"
    },
    {
      "match": "strong",
      "service_id": 84,
      "title": "الإستفادة من التغطية الصحية - طلب إستشفاء",
      "who_is_eligible": [
        "يعتبر حضور المريض الزامي وفي حال عدم تمكنه على احد افراد عائلته المقربين احضار الاوراق المطلوبة مع المستندات التى تثبت صلة القرابة",
        "تعتبر المعاملة صالحة لمدة 15 يوما تجدد بواسطة الطبيب المراقب والمعين من قبل وزارة الصحة وفي حال عدم دخول المريض تعتبر المعاملة ملغاة بعد يومين من تاريخ اصدارها",
        "لا يحق للمستفيدين من تعاونية موظفين الدولة والجيش و الامن الداخلي وشركات التأمين الاستفادة من التغطية الصحية في وزارة الصحة العامة"
      ],
      "required_documents": [
        "تقرير طبي نموذجي مفصل مع تاريخ الدخول,ختم المستشفى, ختم وتوقيع الطبيب مع رقم انتسابه الى النقابة مع عبارة \"على نفقة وزارة الصحة\"",
        "افادة من الضمان الاجتماعي (المركز الرئيسي-منطقة الكولا) تفيد بعدم استفادة المريض من التغطية الصحية في الضمان الاجتماعي على الا تتجاوز الافادة مدة الشهرين",
        "صورة اصلية عن اخراج القيد الفردي + نسخة عنه ويجب ان يكون عليه صورة صاحب العلاقة اذا كان عمره اكثر من خمس سنوات ووثيقة ولادة
```

</details>

<details><summary>Result 3: moph__search_ministry_site (first 2000 of 6004 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "kind": "page",
      "title": "اعلان",
      "date": "2026-03-09",
      "text": "Date: 09/03/2026\nAuthor: وزارة الصحّة العامة\nSource: وزارة الصحّة العامة\nاعلان\nالى المرضى المستفيدين من أمراض السرطان و الدم و الأمراض المستعصية من وزارة الصحة عبر منصة AMAN ،\nتفيدكم وزارة الصحة العامة علما انها، نظرا للظروف الاستثنائية التي تمر بها البلاد، ستقوم يتمدد العمل بالموافقات السارية المفعول على منصة امان للامراض المستعصية حتى ٣٠ حزيران ٢.٢٦ (مع مفعول رجعي حتى ١ اذار ٢.٢٦).\nو فيما يخص المستفيدين من أدوية امراض الدم و السرطان, سيتم تمديد العمل بالموافقات السارية لمدة شهر واحد من تاريخ انتهاء الموافقة (مع مفعول رجعي حتى ١ اذار ٢٠٢٦).",
      "url": "https://www.moph.gov.lb/ar/Pages/127/82905/%D8%A7%D8%B9%D9%84%D8%A7%D9%86"
    },
    {
      "match": "weak",
      "kind": "document",
      "title": "Decision1855-2025",
      "date": "2025-11-25",
      "text": "١- بيان قيد افرادي أو صورة عن الهوية تثبت لبنانية المستدعي\n٢- سجل عدلي لا يعود تاريخه لأكثر من ثلاثة أشهر\n٣- صورة مصدقة عن شهادة البكالوريا اللبنانية - القسم الثاني أو شهادة البكالوريا الفنية\nأو ما يعادل احدى هاتين الشهادتين\n٤- صورة مصدقة عن شهادة العلوم المخبرية الصحية لا تقل مدة دراستها عن ثلاث سنوات وأن يرفق بطلبه بالإضافة إلى هذه الشهادة إفادة صادرة عن لجنة المعادلات تثبت معادلة شهادته للشهادة اللبنانية في هذا الاختصاص\n٥- بيان مصدق بمدة دراسة العلوم المخبرية الصحية مع بيان ب العلامات\n٦- أربع صور شمسية لصاحب الطلب مصدقة من المختار\nالمادة الثالثة: يبلغ هذا القرار حيث تدعو الحاجة\nوزير الصحة العامة\nالدكتور ركان ناصر الدين\nيبلغ:\n- المديرية العامة\n- مديرية مختبرات الصحة العامة\n- اللجنة المختصة ب اصدار مختبرات الصحة العامة\n- مصلحة المستشفيات والمستوصفات\n- قسم المهن الطبية مع الملف\n- المحفوظات\n- المفتشية العامة الصحية والاجتماعية والزراعية",
      "url": "https://www.moph.gov.lb/userfiles/files/News/15-10-2025-Decision1855-2025/Decision1855-2025.pdf",
      "found_on": "https://www.moph.gov.lb/ar/Pages/127/81149/%D8%AA%D8%B9%D9%8A%
```

</details>

<a id="cancer_aman_lb"></a>

## 6. cancer_aman_lb

**Question** (lebanese, AMAN medicine):

> امي عندها سرطان، كيف منجيب الدوا من الوزارة؟

**Expect:** Steps from the MediTrack page: get a unified health number (رقم صحي موحد), the specialist fills a file on the AMAN platform, wait for an SMS (accepted / rejected / under review); IV drugs through the hospital, pills or injections sent to a nearby pharmacy (ministry team calls within a week). Mentions 1214 for cancer medicines. Cites a moph.gov.lb link.

**Answer** (12.1s, first text at 12.1s, 3 model steps):

> سلامتها أمّك. للحصول على دواء السرطان من وزارة الصحة:
>
> 1. إذا أول مرة: لازم يكون ملف الدواء موافَق عليه من اللجنة العلمية بوزارة الصحة، ومعه صورة هوية أو إخراج قيد الشخص الذي سيستلم الدواء.
> 2. إذا استلام متكرر: وصفة من طبيب اختصاصي عمرها أقل من شهر، بطاقة الدواء، وصورة هوية أو إخراج قيد المستلم.
> 3. الاستلام من مركز توزيع الأدوية قرب مستشفى الكرنتينا الحكومي، من الإثنين للجمعة بين الساعة 8 و10 صباحاً.
> 4. المريضة بتحضر شخصياً. إذا ما بتقدر، في قريب يستلم عنها؛ وإذا تعذّر، ممكن الاستلام بوكالة عند كاتب العدل.
> 5. الخدمة بلا رسوم والاستلام باليوم نفسه.
>
> في كمان طلب إلكتروني لأدوية السرطان، وبيطلب عادةً الهوية، تقرير الطبيب، نتيجة الخزعة أو التحاليل، تقارير الصور الشعاعية، والوصفة مع الجرعة والمدة:
> https://www.moph.gov.lb/ar/AdministrativeServices/details/180
>
> التفاصيل الرسمية:
> https://www.moph.gov.lb/ar/AdministrativeServices/details/6

**Tools:**

1. `moph__search_services` `{"query": "كيف تحصل والدتي المصابة بالسرطان على أدوية السرطان من وزارة الصحة اللبنانية، المستندات وطريقة التقديم"}` → found, 5 results, 5 strong
2. `requests__list_services` `{}` → result
3. `moph__get_service` `{"service_id": 6}` → service 6: إستلام أدوية السرطان والأمراض المستعصية
4. `moph__get_service` `{"service_id": 180}` → service 180: Antineoplastic Drugs / National Cancer Registry

<details><summary>Result 1: moph__search_services (first 2000 of 5837 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "service_id": 6,
      "title": "إستلام أدوية السرطان والأمراض المستعصية",
      "who_is_eligible": [
        "حضور المريض شخصياً إلى مركز توزيع الأدوية في الكرنتينا وفي حال تعذر حضوره، يمكن حضور احد اقربائه وفي حال تعذر حضور هذا الأخير ممكن تسليم الدواء بموجب وكالة عند كاتب العدل."
      ],
      "required_documents": [
        "لأول مرة:",
        "ملف الدواء موافق عليه من اللجنة العلمية في وزارة الصحة العامة",
        "صورة عن إخراج القيد او الهوية لمستلم الدواء",
        "للمرات التالية:",
        "وصفة طبية من طبيب اخصائي لا تتجاوز الشهر من تاريخ الإستلام الأخير",
        "بطاقة الدواء",
        "صورة عن إخراج القيد او الهوية لمستلم الدواء"
      ],
      "fees": "لا رسوم",
      "processing_time": "في اليوم نفسه",
      "apply_online": false,
      "office": {
        "directorate": "المديرية العامة",
        "unit": "مصلحة الديوان – مركز توزيع الأدوية",
        "address": "مركز توزيع الأدوية قرب مستشفى الكرنتينا الحكومي",
        "hours": "من الإثنين حتى الجمعة من الساعة الثامنة لغاية العاشرة صباحاً"
      },
      "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/6"
    },
    {
      "match": "strong",
      "service_id": 180,
      "title": "Antineoplastic Drugs / National Cancer Registry",
      "required_documents": [
        "صورة الهوية او اخراج القيد / ID",
        "تقرير الطبيب / Detailed medical report",
        "نتيجة الزرع / Pathology report, solid tumor",
        "Laboratory report, blood tumor",
        "صورة عن تقارير الصور الشعاعية",
        "الوصفة الطبية / Oncology prescription with exact dosage & duration",
        "صورة عن بطاقة مركز توزيع الادوية , اذا وجدت / Copy of Drug Dispensing Center Patient Card , if available"
      ],
      "apply_online": true,
      "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/180"
    },
    {
      "match": "strong",
      "service_id": 80,
      "title": "حصول مريض السرطان على المخد
```

</details>

<details><summary>Result 2: requests__list_services</summary>

```
{"result": [{"key": "hospitalisation", "title": "Hospitalisation at the ministry's expense", "title_ar": "طلب إستشفاء على نفقة وزارة الصحة", "summary": "Approval for the ministry to pay for an operation or hospital stay, for patients with no other health cover."}, {"key": "ivig", "title": "IVIG medicine (immune deficiency, ITP, Kawasaki, Guillain-Barré)", "title_ar": "طلب مساعدة أدوية IVIG", "summary": "Request for the ministry to provide IVIG for primary immune deficiency, ITP, Kawasaki disease or Guillain-Barré."}, {"key": "haemophilia_transplant", "title": "Haemophilia, thalassaemia or transplant medicine", "title_ar": "أدوية مرضى الهيموفيليا والتلاسيميا والزرع", "summary": "Medicine for haemophilia or thalassaemia, or anti-rejection medicine (Advagraf, Prograf) after an organ transplant."}, {"key": "complaint", "title": "Complaint about a hospital or health service", "title_ar": "شكوى", "summary": "A complaint to the ministry, for example a hospital asking for extra payment."}]}
```

</details>

<details><summary>Result 3: moph__get_service</summary>

```
{
  "service_id": 6,
  "title": "إستلام أدوية السرطان والأمراض المستعصية",
  "who_is_eligible": [
    "حضور المريض شخصياً إلى مركز توزيع الأدوية في الكرنتينا وفي حال تعذر حضوره، يمكن حضور احد اقربائه وفي حال تعذر حضور هذا الأخير ممكن تسليم الدواء بموجب وكالة عند كاتب العدل."
  ],
  "required_documents": [
    "لأول مرة:",
    "ملف الدواء موافق عليه من اللجنة العلمية في وزارة الصحة العامة",
    "صورة عن إخراج القيد او الهوية لمستلم الدواء",
    "للمرات التالية:",
    "وصفة طبية من طبيب اخصائي لا تتجاوز الشهر من تاريخ الإستلام الأخير",
    "بطاقة الدواء",
    "صورة عن إخراج القيد او الهوية لمستلم الدواء"
  ],
  "fees": "لا رسوم",
  "processing_time": "في اليوم نفسه",
  "apply_online": false,
  "office": {
    "directorate": "المديرية العامة",
    "unit": "مصلحة الديوان – مركز توزيع الأدوية",
    "address": "مركز توزيع الأدوية قرب مستشفى الكرنتينا الحكومي",
    "hours": "من الإثنين حتى الجمعة من الساعة الثامنة لغاية العاشرة صباحاً"
  },
  "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/6"
}
```

</details>

<details><summary>Result 4: moph__get_service</summary>

```
{
  "service_id": 180,
  "title": "Antineoplastic Drugs / National Cancer Registry",
  "required_documents": [
    "صورة الهوية او اخراج القيد / ID",
    "تقرير الطبيب / Detailed medical report",
    "نتيجة الزرع / Pathology report, solid tumor",
    "Laboratory report, blood tumor",
    "صورة عن تقارير الصور الشعاعية",
    "الوصفة الطبية / Oncology prescription with exact dosage & duration",
    "صورة عن بطاقة مركز توزيع الادوية , اذا وجدت / Copy of Drug Dispensing Center Patient Card , if available"
  ],
  "apply_online": true,
  "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/180"
}
```

</details>

<a id="ms_aman_en"></a>

## 7. ms_aman_en

**Question** (english, AMAN medicine):

> How do I get my multiple sclerosis medication from the ministry?

**Expect:** Same AMAN flow as cancer: unified health number, specialist files on AMAN, SMS decision, hospital for IV or pharmacy delivery for pills/injections. Cites a moph.gov.lb link. No invented eligibility rules.

**Answer** (9.1s, first text at 9.1s, 3 model steps):

> You can apply online through the Ministry of Public Health’s “Multiple Sclerosis Therapy” service.
>
> Prepare:
> 1. Copy of your ID or individual civil extract
> 2. Detailed medical report from your doctor
> 3. Medical prescription
> 4. MRI reports
> 5. CSF results
> 6. Evoked potential results
> 7. If the medicine is Gilenya: liver function test, macular/retinal eye exam, and a blood test showing Varicella titer
> 8. Copy of your Ministry drug-dispensing centre card, if available
>
> Apply here:
> https://www.moph.gov.lb/ar/AdministrativeServices/details/190
>
> The service is listed as online, but the page does not state the processing time or fees.

**Tools:**

1. `moph__search_services` `{"query": "كيفية الحصول على أدوية التصلب اللويحي المتعدد من وزارة الصحة العامة المستندات والشروط"}` → found, 5 results, 5 strong
2. `moph__get_service` `{"service_id": 190}` → service 190: Multiple Sclerosis Therapy

<details><summary>Result 1: moph__search_services (first 2000 of 5788 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "service_id": 206,
      "title": "طلب الحصول على مساعدة أدوية من وزارة الصحة العامة:Psychotropics",
      "who_is_eligible": [
        "Drugs National Guidelines",
        "أن يكون المريض لبنانياً",
        "عدم إنتساب المريض لأي جهة ضامنة أخرى"
      ],
      "required_documents": [
        "Copy of ID (هوية أو إخراج قيد فردي) with a copy of the Quarantina card",
        "(Detailed psychiatric report (ensure mentioning the management of physical comorbidities such as diabetes and dyslipidemia where present in addition to informing the patient about potential severe side-effects of some psychotropic medications such as clozapine and atomoxetine",
        "Psychiatric prescription with exact dosage and duration",
        "For clozapine (i.e. Leponex) prescription, CBC test, once every month",
        "For antipsychotic medicarions (if BMI>29): Metabolic syndrome once a year: blood glucose, lipid profile",
        "(Better to perform an EKG once before start of Paliperidone injection (i.e, Invega sustenna"
      ],
      "processing_time": "أسبوعان",
      "forms": [
        {
          "name": "MOPHpsychotropicmedicationform28.02.2018-2",
          "url": "https://www.moph.gov.lb/AdministrativeServices/download/1362"
        }
      ],
      "apply_online": true,
      "office": {
        "directorate": "المديرية العامة للصحة",
        "unit": "مصلحة الديوان - دائرة التجهيز والتموين",
        "address": "بئر حسن، الجناح، قرب أوجيرو",
        "email": "drugs@moph.gov.lb",
        "hours": "من الأثنين حتى الجمعة ضمن الدوام الرسمي."
      },
      "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/206"
    },
    {
      "match": "strong",
      "service_id": 190,
      "title": "Multiple Sclerosis Therapy",
      "who_is_eligible": [
        "صورة ألهوية او اخراج القيد",
        "Detailed Medical report تقرير الطبيب",
        "Physician’s prescription الوصفة الطبية",
    
```

</details>

<details><summary>Result 2: moph__get_service</summary>

```
{
  "service_id": 190,
  "title": "Multiple Sclerosis Therapy",
  "who_is_eligible": [
    "صورة ألهوية او اخراج القيد",
    "Detailed Medical report تقرير الطبيب",
    "Physician’s prescription الوصفة الطبية",
    "MRIs, as listed above",
    "CSF",
    "Evoked Potential results",
    "واذا كاى الدواء Gilenya المطلوب تأمين الفحوصات التالية:",
    "Liver function test فحص الكبد",
    "فحص شبكة العين exam Macular",
    "فحص دم يظهر titer Varicella",
    "Copy of Drugs Dispensing Center Patient Card Should be submitted, if available",
    "صورة عن بطاقة مركز توزيع الأدوية إذا وجدت"
  ],
  "apply_online": true,
  "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/190"
}
```

</details>

<a id="haemophilia_arabizi"></a>

## 8. haemophilia_arabizi

**Question** (arabizi, WhatsApp 81/348838):

> ibni 3ando hemophilia, kif bjib el dawa men el wizara?

**Expect:** Unified health number; specialist fills the file on AMAN, or send ID copy, unified health number, detailed medical report (drug, strength, daily dose) and unified prescription to the ministry / nearest centre or by WhatsApp to 81/348838. Medicine delivered to the chosen pharmacy, or via Karantina if uninsured; about 5 working days. Replies in Arabizi.

**Answer** (21.9s, first text at 21.9s, 2 model steps):

> Eh, fi talab msa3det adwiye lal hemophilia men wizaret el se7a.
>
> El shorout:
> 1. Ykoun el marid Lebnene.
> 2. Ma ykoun menteseb la ay jehe damne tennye.
>
> El wara2:
> 1. Sourit el hawiyye aw ekhraj 2ayd.
> 2. Taqrir tebbe mfassal.
> 3. Wasfe tebbiyye fiya el dosage w moddet el 3ilej.
> 4. F7ouset dam: CBC, platelets, PT, PTT, bleeding time.
> 5. El dosage el da2i2 la Von Willebrand factor, Factor VII, Factor VIII, Factor IX aw Fibrinogen, 7asab 7alet ibnak.
> 6. Sourit be2et markaz tawzi3 el adwiye iza mawjoude.
>
> El mo3amale online w 3adatan btekhod 7awale esbou3en. Fik tetwasal ma3:
> drugs@moph.gov.lb
>
> El markaz: Bir Hassan, El Janah, 7ad Ogero، men el tenein lal jem3a ضمن el dawem el rasmi.
>
> El saf7a el rasmiye:
> https://www.moph.gov.lb/ar/AdministrativeServices/details/187
>
> Iza بدك، fiye 7addarlak el talab w na22ellak chou el sowar wel ma3loumet el matloube lal ta2dim.

**Tools:**

1. `moph__search_services` `{"query": "كيف يحصل مريض الهيموفيليا على الدواء من وزارة الصحة اللبنانية وما هي المستندات المطلوبة"}` → found, 5 results, 5 strong

<details><summary>Result 1: moph__search_services (first 2000 of 8120 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "service_id": 187,
      "title": "طلب الحصول على مساعدة أدوية من وزارة الصحة العامة:Bleeding Disorders",
      "who_is_eligible": [
        "Drugs National Guidelines",
        "أن يكون المريض لبنانياً",
        "عدم إنتساب المريض لأي جهة ضامنة أخرى"
      ],
      "required_documents": [
        "صورة الهوية او اخراج القيد",
        "تقرير الطبيب Detailed MedicalReport",
        "الوصفة الطبية Physician’s prescription with exact dosage & duration – please write clearly",
        "Blood studies: CBC, Platelets, PT, PTT, Bleeding time",
        "Exact dosages of Von Willebrand factor, Factor VII, Factor VIII, Factor IX, Fibrinogen (according to case)",
        "Copy of Drug Dispensing Center Patient Card Should be submitted, if available",
        "صورة عن بطاقة مركز توزيع الأدوية اذا وجدت"
      ],
      "processing_time": "أسبوعان",
      "forms": [
        {
          "name": "AK014BD-2",
          "url": "https://www.moph.gov.lb/AdministrativeServices/download/1360"
        }
      ],
      "apply_online": true,
      "office": {
        "directorate": "المديرية العامة للصحة",
        "unit": "مصلحة الديوان - دائرة التجهيز والتموين",
        "address": "بئر حسن، الجناح، قرب أوجيرو",
        "email": "drugs@moph.gov.lb",
        "hours": "من الأثنين حتى الجمعة ضمن الدوام الرسمي."
      },
      "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/187"
    },
    {
      "match": "strong",
      "service_id": 188,
      "title": "طلب الحصول على مساعدة أدوية من وزارة الصحة العامة:Iron overload",
      "who_is_eligible": [
        "Drugs National Guidelines",
        "أن يكون المريض لبنانياً",
        "عدم إنتساب المريض لأي جهة ضامنة أخرى"
      ],
      "required_documents": [
        "صورة الهوية او اخراج القيد",
        "تقرير الطبيب Detailed MedicalReport",
        "الوصفة الطبية Physician’s prescriptionwith exact dosage & duration – please write clearly",
        "Bloo
```

</details>

<a id="transplant_msa"></a>

## 9. transplant_msa

**Question** (msa, WhatsApp 81/348838):

> أجريت عملية زرع كلية وأحتاج دواء Prograf بشكل دائم، كيف أحصل عليه من الوزارة؟

**Expect:** Unified health number; AMAN file through the specialist, or send a one-time medical report (transplant done, needs the drug for life), the unified health number and a prescription of at least one month (drug, strength, daily dose) by WhatsApp to 81/348838; about 5 working days. May say Prograf is on the ministry's free lists (AMAN / tender 388).

**Answer** (9.7s, first text at 9.7s, 3 model steps):

> يمكنك التقدّم عبر خدمة وزارة الصحة الخاصة بأدوية زراعة الكلى أو الأعضاء، وهي متاحة إلكترونياً.
>
> المستندات المطلوبة:
> 1. صورة عن الهوية أو إخراج القيد.
> 2. تقرير طبي مفصّل.
> 3. وصفة الطبيب.
> 4. صورة عن بطاقة مركز توزيع الأدوية، إذا كانت متوفّرة.
>
> يجب أن تتضمّن الوصفة دواء بروغراف والجرعة والمدة بوضوح.
>
> رابط الخدمة الرسمي:
> https://www.moph.gov.lb/ar/AdministrativeServices/details/195
>
> إذا أردت، يمكنني تحضير الطلب معك وإرساله إلى الوزارة.

**Tools:**

1. `moph__search_services` `{"query": "كيف أحصل على دواء Prograf تاكروليموس بعد زرع كلية من وزارة الصحة أدوية زراعة الأعضاء"}` → found, 5 results, 5 strong
2. `moph__get_service` `{"service_id": 195}` → service 195: Transplantation - Kidney or other Organs

<details><summary>Result 1: moph__search_services (first 2000 of 4472 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "service_id": 195,
      "title": "Transplantation - Kidney or other Organs",
      "required_documents": [
        "صورة الهوية او اخراج القيد",
        "تقرير الطبيب Detailed Medical Report",
        "الوصفة الطبية Physician’s prescription",
        "Copy of Drugs Dispensing Center Patient Card Should be submitted, if available",
        "صورة عن بطاقة مركز توزيع الأدوية اذا وجدت"
      ],
      "apply_online": true,
      "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/195"
    },
    {
      "match": "strong",
      "service_id": 6,
      "title": "إستلام أدوية السرطان والأمراض المستعصية",
      "who_is_eligible": [
        "حضور المريض شخصياً إلى مركز توزيع الأدوية في الكرنتينا وفي حال تعذر حضوره، يمكن حضور احد اقربائه وفي حال تعذر حضور هذا الأخير ممكن تسليم الدواء بموجب وكالة عند كاتب العدل."
      ],
      "required_documents": [
        "لأول مرة:",
        "ملف الدواء موافق عليه من اللجنة العلمية في وزارة الصحة العامة",
        "صورة عن إخراج القيد او الهوية لمستلم الدواء",
        "للمرات التالية:",
        "وصفة طبية من طبيب اخصائي لا تتجاوز الشهر من تاريخ الإستلام الأخير",
        "بطاقة الدواء",
        "صورة عن إخراج القيد او الهوية لمستلم الدواء"
      ],
      "fees": "لا رسوم",
      "processing_time": "في اليوم نفسه",
      "apply_online": false,
      "office": {
        "directorate": "المديرية العامة",
        "unit": "مصلحة الديوان – مركز توزيع الأدوية",
        "address": "مركز توزيع الأدوية قرب مستشفى الكرنتينا الحكومي",
        "hours": "من الإثنين حتى الجمعة من الساعة الثامنة لغاية العاشرة صباحاً"
      },
      "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/6"
    },
    {
      "match": "strong",
      "service_id": 181,
      "title": "Bone Marrow Transplantation",
      "required_documents": [
        "صورة الهوية او اخراج القيد",
        "Detailed Medical report الطبيب تقرير",
        "Physician’s prescription
```

</details>

<details><summary>Result 2: moph__get_service</summary>

```
{
  "service_id": 195,
  "title": "Transplantation - Kidney or other Organs",
  "required_documents": [
    "صورة الهوية او اخراج القيد",
    "تقرير الطبيب Detailed Medical Report",
    "الوصفة الطبية Physician’s prescription",
    "Copy of Drugs Dispensing Center Patient Card Should be submitted, if available",
    "صورة عن بطاقة مركز توزيع الأدوية اذا وجدت"
  ],
  "apply_online": true,
  "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/195"
}
```

</details>

<a id="humira_lb"></a>

## 10. humira_lb

**Question** (lebanese, Humira):

> الدكتور وصفلي Humira، في طريقة آخدو من الوزارة؟

**Expect:** Humira from an exceptional 3-month donation: get a unified health number, go to the ministry, 4th floor (الطابق الرابع) with unified health number, ID copy, detailed specialist report (rheumatology, GI, eye or skin), unified prescription with the monthly dose, labs SGOT, SGPT, creatinine, CBC. May add it is on the ministry's free list and its public price (34,045,375 LBP).

**Answer** (8.7s, first text at 8.7s, 2 model steps):

> إيه، Humira 40mg/0.4ml موجود على لائحة الأدوية التي تؤمّنها وزارة الصحة، ومنها لأمراض الروماتيزم، الجلد، الأمعاء الالتهابية والتهاب القولون التقرّحي.
>
> للاستفادة عادةً لازم يكون المريض لبناني وما يكون منتسب لجهة ضامنة تانية. الطلب بيتقدّم عبر خدمة مساعدة أدوية، ومدة المعالجة المذكورة حوالي أسبوعين.
>
> شو التشخيص اللي وصفلك الدكتور Humira عشانه، وعندك ضمان أو تأمين تاني؟  
> التفاصيل الرسمية: https://www.moph.gov.lb/ar/AdministrativeServices/details/1

**Tools:**

1. `moph__search_services` `{"query": "كيف أحصل على دواء Humira من وزارة الصحة، أدوية الأمراض المزمنة والمناعية"}` → found, 5 results, 5 strong
2. `moph__lookup_drug` `{"name": "Humira"}` → found, 1 results, 5 on free lists

<details><summary>Result 1: moph__search_services (first 2000 of 8165 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "service_id": 185,
      "title": "طلب الحصول على مساعدة أدوية من وزارة الصحة العامة:IVIG for Immune deficiency,ITP,Kawasaki,GB",
      "who_is_eligible": [
        "Drugs National Guidelines",
        "أن يكون المريض لبنانياً",
        "عدم إنتساب المريض لأي جهة ضامنة أخرى"
      ],
      "required_documents": [
        "صورة الهوية او اخراج القيد",
        "تقرير الطبيب Detailed Medical report",
        "الوصفة الطبية Physician’s prescription with exact dosage & duration – please write clearly",
        "Copy of Drugs Dispensing Center Patient Card Should be submitted, if available",
        "صورة عن بطاقة مركز توزيع الأدوية اذا وجدت",
        ":In addition",
        "For ITP: CBC, Bone marrow smear, if needed",
        "For Kawasaki: CBC, ESR",
        "For Primary immune deficiency: CBC, Platelet, Smear",
        "Immunoglobulin Quantitation: 1st measurement 2nd measurement IgG subclasses",
        "For Guillain Barré:",
        "For Renewal: Confirmatory letter from physician"
      ],
      "processing_time": "أسبوعان",
      "forms": [
        {
          "name": "AK010IVIG-4",
          "url": "https://www.moph.gov.lb/AdministrativeServices/download/1359"
        }
      ],
      "apply_online": true,
      "office": {
        "directorate": "المديرية العامة للصحة",
        "unit": "مصلحة الديوان - دائرة التجهيز والتموين",
        "address": "بئر حسن، الجناح، قرب أوجيرو",
        "email": "drugs@moph.gov.lb",
        "hours": "من الأثنين حتى الجمعة ضمن الدوام الرسمي."
      },
      "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/185"
    },
    {
      "match": "strong",
      "service_id": 1,
      "title": "طلب الحصول على مساعدة أدوية من وزارة الصحة العامة",
      "who_is_eligible": [
        "Drugs National Guidelines",
        "أن يكون المريض لبنانياً",
        "عدم إنتساب المريض لأي جهة ضامنة أخرى"
      ],
      "required_documents": [
        "داخل الإ
```

</details>

<details><summary>Result 2: moph__lookup_drug (first 2000 of 2721 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "name",
      "brand_name": "HUMIRA",
      "type": "brand",
      "ingredients": "Adalimumab - 40mg/0.4ml",
      "dosage": "40mg/0.4ml",
      "form": "Injectable solution",
      "public_price": "34,045,375 LBP",
      "on_moph_free_list": true,
      "url": "https://www.moph.gov.lb/en/Drugs/view/3975"
    }
  ],
  "data_as_of": "2026-10-10",
  "more_matches": 0,
  "free_lists": [
    {
      "brand_name": "HUMIRA",
      "composition": "",
      "strength": "40mg/0.4ml",
      "form": "Injectable solution",
      "therapeutic_class": "",
      "list": "Tender 388/2024 list of medicines MoPH provides (2024)",
      "source_url": "https://www.moph.gov.lb/userfiles/files/HealthCareSystem/Pharmaceuticals/DrugsPublicPriceList/5-2-2024/Tender388-2024.xlsx"
    },
    {
      "brand_name": "Humira 40 mg",
      "composition": "Adalimumab 40 mg SC",
      "strength": "",
      "form": "",
      "therapeutic_class": "Drugs for Inflammatory Bowel Diseases",
      "list": "AMAN list: medicines for intractable diseases that MoPH provides (file dated 2024-10-23)",
      "source_url": "https://www.moph.gov.lb/userfiles/files/News/23-10-2024%20List%20of%20Medications%20Provided%20By%20MoPH/Active%20medications%20in%20AMAN_final.xlsx"
    },
    {
      "brand_name": "Humira 40 mg",
      "composition": "Adalimumab 40 mg SC",
      "strength": "",
      "form": "",
      "therapeutic_class": "Drugs for Rheumatic Diseases",
      "list": "AMAN list: medicines for intractable diseases that MoPH provides (file dated 2024-10-23)",
      "source_url": "https://www.moph.gov.lb/userfiles/files/News/23-10-2024%20List%20of%20Medications%20Provided%20By%20MoPH/Active%20medications%20in%20AMAN_final.xlsx"
    },
    {
      "brand_name": "Humira 40 mg",
      "composition": "Adalimumab 40 mg SC",
      "strength": "",
      "form": "",
      "therapeutic_class": "Drugs for Dermatological diseases",
      "list": "AMAN list: medicines 
```

</details>

<a id="ivig_en"></a>

## 11. ivig_en

**Question** (english, IVIG):

> My son has ITP and his doctor prescribed IVIG. Can the ministry provide it?

**Expect:** Service 185: patient must be Lebanese with no other insurer. Documents: ID or ikhraj qaid, detailed medical report, prescription with exact dosage and duration, drugs dispensing centre card if any; for ITP also CBC and bone marrow smear if needed. Office in Bir Hassan, Jnah, near Ogero, drugs@moph.gov.lb, Monday to Friday official hours, takes two weeks, can apply online. Links details/185. Ideally asks about NSSF/other insurance.

**Answer** (8.9s, first text at 8.9s, 2 model steps):

> Yes. The Ministry has a service for IVIG assistance specifically for ITP, subject to its national drug guidelines.
>
> Eligibility listed by the Ministry:
> 1. The patient must be Lebanese.
> 2. He must not be covered by another payer or insurance.
>
> Required documents include:
> 1. ID or individual civil registry extract
> 2. Detailed medical report
> 3. Prescription with exact dosage and treatment duration
> 4. CBC, bone marrow smear/aspirate if needed, and peripheral smear
> 5. Drug dispensing centre card, if available
>
> The stated processing time is 2 weeks. Applications are handled by the Ministry’s Drug Supply Department in Bir Hassan, or by email at drugs@moph.gov.lb.
>
> Official page:
> https://www.moph.gov.lb/ar/AdministrativeServices/details/185
>
> I can also prepare and submit the application for you if you’d like.

**Tools:**

1. `moph__search_ministry_site` `{"query": "تغطية الغلوبولين المناعي الوريدي IVIG مرضى ITP الأطفال وزارة الصحة"}` → found, 5 results, 1 strong
2. `moph__search_services` `{"query": "طلب دواء الغلوبولين المناعي الوريدي IVIG لمرضى ITP وزارة الصحة المستندات والشروط"}` → found, 5 results, 5 strong

<details><summary>Result 1: moph__search_ministry_site (first 2000 of 6236 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "kind": "document",
      "title": "Karar1362-2018",
      "date": "2018",
      "text": "| IVIG for immune deficiency, ITP, Kawasaki, GB\n| Bleeding Disorders\n| Iron overload\n| Psychotropics",
      "url": "https://www.moph.gov.lb/Laws/download_file/3575",
      "found_on": "https://www.moph.gov.lb/ar/Pages/6/2651/%D8%A7%D9%84%D8%A8%D8%B1%D9%86%D8%A7%D9%85%D8%AC-%D8%A7%D9%84%D9%88%D8%B7%D9%86%D9%8A-%D9%84%D9%84%D8%B5%D8%AD%D9%91%D8%A9-%D8%A7%D9%84%D8%A5%D9%84%D9%83%D8%AA%D8%B1%D9%88%D9%86%D9%8A%D8%A9",
      "found_on_title": "البرنامج الوطني للصحّة الإلكترونية"
    },
    {
      "match": "weak",
      "kind": "page",
      "title": "وفد من تحالف Gavi العالمي للقاحات يزور لبنان لتقييم واقع تلقيح الأطفال",
      "date": "2026-08-17",
      "text": "وتواصل وزارة الصحة العامة، من خلال البرنامج الوطني للتلقيح في دائرة الرعاية الصحية الأولية، جهودها لضمان وصول خدمات التلقيح إلى جميع الأطفال، لبنانيين وغير لبنانيين، بالتعاون مع الشركاء، وبما يضمن حماية الأطفال والمجتمع من الأمراض التي يمكن الوقاية منها باللقاحات.",
      "url": "https://www.moph.gov.lb/ar/Pages/127/86648/%D9%88%D9%81%D8%AF-%D9%85%D9%86-%D8%AA%D8%AD%D8%A7%D9%84%D9%81-gavi-%D8%A7%D9%84%D8%B9%D8%A7%D9%84%D9%85%D9%8A-%D9%84%D9%84%D9%82%D8%A7%D8%AD%D8%A7%D8%AA-%D9%8A%D8%B2%D9%88%D8%B1-%D9%84%D8%A8%D9%86%D8%A7%D9%86-%D9%84%D8%AA%D9%82%D9%8A%D9%8A%D9%85-%D9%88%D8%A7%D9%82%D8%B9-%D8%AA%D9%84%D9%82%D9%8A%D8%AD-%D8%A7%D9%84%D8%A3%D8%B7%D9%81%D8%A7%D9%84"
    },
    {
      "match": "weak",
      "kind": "page",
      "title": "وزارة الصحّة العامة",
      "text": "تعمل دائرة الرعاية الصحية الاولية من خلال البرنامج الوطني للتحصين على رفع مستوى التحصين الروتيني بهدف الحفاظ على لبنان خال من شلل الاطفال خاصة في ظل استمرار أزمة النزوح. كما تسعى من خلال هذا البرنامج الى القضاء على مرضي الحصبة والحصبة الالمانية في نهاية العام 2020.\nأبرز النشاطات والانجازات:\nتلقيح ما يقارب نصف مليون (0.5 M) طفل ما دون الخمس سنوات على الأراضي اللبنانية خلال كل حملة 
```

</details>

<details><summary>Result 2: moph__search_services (first 2000 of 5546 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "service_id": 185,
      "title": "طلب الحصول على مساعدة أدوية من وزارة الصحة العامة:IVIG for Immune deficiency,ITP,Kawasaki,GB",
      "who_is_eligible": [
        "Drugs National Guidelines",
        "أن يكون المريض لبنانياً",
        "عدم إنتساب المريض لأي جهة ضامنة أخرى"
      ],
      "required_documents": [
        "صورة الهوية او اخراج القيد",
        "تقرير الطبيب Detailed Medical report",
        "الوصفة الطبية Physician’s prescription with exact dosage & duration – please write clearly",
        "Copy of Drugs Dispensing Center Patient Card Should be submitted, if available",
        "صورة عن بطاقة مركز توزيع الأدوية اذا وجدت",
        ":In addition",
        "For ITP: CBC, Bone marrow smear, if needed",
        "For Kawasaki: CBC, ESR",
        "For Primary immune deficiency: CBC, Platelet, Smear",
        "Immunoglobulin Quantitation: 1st measurement 2nd measurement IgG subclasses",
        "For Guillain Barré:",
        "For Renewal: Confirmatory letter from physician"
      ],
      "processing_time": "أسبوعان",
      "forms": [
        {
          "name": "AK010IVIG-4",
          "url": "https://www.moph.gov.lb/AdministrativeServices/download/1359"
        }
      ],
      "apply_online": true,
      "office": {
        "directorate": "المديرية العامة للصحة",
        "unit": "مصلحة الديوان - دائرة التجهيز والتموين",
        "address": "بئر حسن، الجناح، قرب أوجيرو",
        "email": "drugs@moph.gov.lb",
        "hours": "من الأثنين حتى الجمعة ضمن الدوام الرسمي."
      },
      "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/185"
    },
    {
      "match": "strong",
      "service_id": 194,
      "title": "Immune Thrombocytopenic Purpura",
      "required_documents": [
        "صورة الهوية او اخراج القيد",
        "تقرير الطبيب Detailed Medical report",
        "الوصفة الطبية Physician’s prescription with exact dosage & duration – please write clearly",

```

</details>

<a id="complaint_lb"></a>

## 12. complaint_lb

**Question** (lebanese, complaints):

> المستشفى طالبين مني مصاري زيادة مع إنو أنا داخل على حساب الوزارة، لمين بشتكي؟

**Expect:** Complaints go to the ministry hotline 1214 (complaints received 24/7; also info@moph.gov.lb). May add 1787 for questions about the coverage decision during working hours. No invented numbers.

**Answer** (9.8s, first text at 9.8s, 3 model steps):

> إذا المستشفى عم يطلب منك فروقات مالية رغم إنو دخولك مغطّى 100% على حساب وزارة الصحة، فيك تشتكي على:
>
> 1. الخط الساخن 1787 خلال ساعات الدوام، للاستفسار عن تغطية الاستشفاء وتقديم الشكوى.
> 2. مكتب الشكاوى بوزارة الصحة: 1214
> 3. البريد الإلكتروني: info@moph.gov.lb
> 4. للاستفسار عن إدخالك للمستشفى: 01/832700
>
> احتفظ بأي مستندات أو فواتير أو طلب دفع، واذكر اسم المستشفى ورقم المعاملة وتاريخ الدخول.
>
> المصدر:
> https://www.moph.gov.lb/ar/Pages/127/83157/%D9%88%D8%B2%D9%8A%D8%B1-%D8%A7%D9%84%D8%B5%D8%AD%D8%A9-%D9%8A%D8%B7%D9%84%D8%A8-%D9%85%D9%86-%D9%85%D8%B3%D8%AA%D8%B4%D9%81%D9%8A%D8%A7%D8%AA-%D8%AD%D9%83%D9%88%D9%85%D9%8A%D8%A9-%D9%88%D8%AE%D8%A7%D8%B5%D8%A9-%D8%A7%D9%84%D9%85%D8%B1%D8%B6%D9%89-%D9%88%D8%A7%D9%84%D9%86%D8%A7%D8%B2%D8%ADين

**Tools:**

1. `moph__search_ministry_site` `{"query": "شكوى مستشفى طلب مبلغ إضافي رغم الدخول على نفقة وزارة الصحة العامة تقديم شكوى"}` → found, 5 results, 5 strong
2. `moph__get_contacts` `{}` → 4 contacts

<details><summary>Result 1: moph__search_ministry_site (first 2000 of 7788 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "kind": "page",
      "title": "وزير الصحة يطلب من مستشفيات حكومية وخاصة الالتزام بتغطية كاملة للمرضى والنازحين",
      "date": "2026-03-14",
      "text": "Date: 14/03/2026\nAuthor: مكتب معالي الوزير\nSource: وزارة الصحّة العامة\nوزير الصحة يطلب من مستشفيات حكومية وخاصة الالتزام بتغطية كاملة للمرضى والنازحين\nتحت طائلة اتخاذ الإجراءات القانونية اللازمة\nصدر عن وزير الصحة العامة الدكتور ركان ناصر الدين كتابٌ تعميمي لفت إلى ورود العديد من الشكاوى من قبل المواطنين تفيد بفرض فروقات مالية عليهم تحت ذرائع مختلفة، على الرغم من التغطية بنسبة مئة في المئة، في مستشفيات حكومية وخاصة كانت قد أبدت رغبتها في تطبيق تعاميم سابقة صادرة عن وزير الصحة لجهة عدم تكبيد المرضى والنازحين الذين ليس لديهم جهة ضامنة فروقات مالية، واستقبالهم على نفقة الوزارة بتغطية 100% لجميع الأعمال الإستشفائية والطبية التي تغطيها الوزارة.\nوأكد الكتاب التعميمي ضرورة التزام المستشفيات الحكومية والمستشفيات الخاصة المعنية ( اللائحة مرفقة في مضمون الكتاب) بالتغطيات الاستشفائية والطوارئ بنسبة مئة في المئة، تحت طائلة اتخاذ الإجراءات القانونية اللازمة.\nكما ذكر المرضى والنازحين الذين ليس لديهم جهة ضامنة بضرورة إبلاغ وزارة الصحة على الرقم الساخن 1787 لتقديم الشكاوى في حال طلبت منهم فروقات.\nكتابٌ تعميمي",
      "url": "https://www.moph.gov.lb/ar/Pages/127/83157/%D9%88%D8%B2%D9%8A%D8%B1-%D8%A7%D9%84%D8%B5%D8%AD%D8%A9-%D9%8A%D8%B7%D9%84%D8%A8-%D9%85%D9%86-%D9%85%D8%B3%D8%AA%D8%B4%D9%81%D9%8A%D8%A7%D8%AA-%D8%AD%D9%83%D9%88%D9%85%D9%8A%D8%A9-%D9%88%D8%AE%D8%A7%D8%B5%D8%A9-%D8%A7%D9%84%D8%A7%D9%84%D8%AA%D8%B2%D8%A7%D9%85-%D8%A8%D8%AA%D8%BA%D8%B7%D9%8A%D8%A9-%D9%83%D8%A7%D9%85%D9%84%D8%A9-%D9%84%D9%84%D9%85%D8%B1%D8%B6%D9%89-%D9%88%D8%A7%D9%84%D9%86%D8%A7%D8%B2%D8%AD%D9%8A%D9%86-%D8%AA%D8%AD%D8%AA-%D8%B7%D8%A7%D8%A6%D9%84%D8%A9-%D8%A7%D8%AA%D8%AE%D8%A7%D8%B0-%D8%A7%D9%84%D8%A5%D8%AC%D8%B1%D8%A7%D8%A1%D8%A7%D8%AA-%D8%A7%D9%84%D9%82%D8%A7%D9%86%D9%88%D9%86%D9%8A%D8%A9-%D8%A7%D9%84%D9%84%D8%A7%D8%B2%D9%85%D8%A9"
    },
    {
      "match": "strong",
    
```

</details>

<details><summary>Result 2: moph__get_contacts</summary>

```
{
  "contacts": [
    {
      "contact": "1214: Ministry of Public Health hotline and complaints office (info@moph.gov.lb), also for cancer and intractable-disease medicines",
      "source_url": "https://www.moph.gov.lb/ar/contact"
    },
    {
      "contact": "1787: questions about the ministry's emergency and hospitalisation cover (working hours); hospitalisation for displaced people",
      "source_url": "https://www.moph.gov.lb/ar/Media/view/85973"
    },
    {
      "contact": "01/832700: hotline for patient admission to hospitals",
      "source_url": "https://www.moph.gov.lb/ar/complaints"
    },
    {
      "contact": "1564: mental health support line",
      "source_url": "https://www.moph.gov.lb/ar/Media/view/82829"
    }
  ]
}
```

</details>

<a id="hotlines_en"></a>

## 13. hotlines_en

**Question** (english, hotlines):

> What's the ministry's hotline number?

**Expect:** 1214. May add 1787 (health services for displaced Lebanese / coverage questions) and 1564 (mental health). No invented numbers.

**Answer** (4.0s, first text at 4.0s, 2 model steps):

> The Ministry of Public Health’s main hotline is 1214.
>
> Other numbers:
> - 1787: questions about emergency and hospitalisation coverage
> - 01/832700: hospital patient admission hotline
> - 1564: mental health support line
>
> https://www.moph.gov.lb/ar/contact

**Tools:**

1. `moph__get_contacts` `{}` → 4 contacts

<details><summary>Result 1: moph__get_contacts</summary>

```
{
  "contacts": [
    {
      "contact": "1214: Ministry of Public Health hotline and complaints office (info@moph.gov.lb), also for cancer and intractable-disease medicines",
      "source_url": "https://www.moph.gov.lb/ar/contact"
    },
    {
      "contact": "1787: questions about the ministry's emergency and hospitalisation cover (working hours); hospitalisation for displaced people",
      "source_url": "https://www.moph.gov.lb/ar/Media/view/85973"
    },
    {
      "contact": "01/832700: hotline for patient admission to hospitals",
      "source_url": "https://www.moph.gov.lb/ar/complaints"
    },
    {
      "contact": "1564: mental health support line",
      "source_url": "https://www.moph.gov.lb/ar/Media/view/82829"
    }
  ]
}
```

</details>

<a id="panadol_lb"></a>

## 14. panadol_lb

**Question** (lebanese, drug price):

> قديش سعر البنادول هلأ؟ في شي أرخص منه؟

**Expect:** Looks up 'panadol' in Latin letters. Gives public prices from the list (e.g. PANADOL ACTIFAST 500mg tablets 159,917 LBP) or asks which Panadol, and cheaper paracetamol 500mg equivalents (e.g. PARACETAMOL 66,552 LBP, ADOL 81,974 LBP). Links moph.gov.lb/en/Drugs/view/... No prices from memory.

**Answer** (4.4s, first text at 4.4s, 2 model steps):

> حسب لائحة وزارة الصحة بتاريخ 10-10-2026:
>
> - Panadol Actifast 500mg: 159,917 ل.ل.
> - Panadol Advance 500mg: 438,093 ل.ل.
>
> في بدائل أرخص بنفس المادة والجرعة والشكل تقريبًا:
> - Paracetamol 500mg: 66,552 ل.ل.
> - Adol 500mg: 81,974 ل.ل.
> - Ubsadol 500mg: 89,590 ل.ل.
>
> الأسعار هي السعر الرسمي المنشور من الوزارة وقد تختلف حسب الصيدلية:
> https://www.moph.gov.lb/en/Drugs/view/4505

**Tools:**

1. `moph__lookup_drug` `{"name": "Panadol"}` → found, 5 results

<details><summary>Result 1: moph__lookup_drug (first 2000 of 3932 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "name",
      "brand_name": "PANADOL ACTIFAST",
      "type": "brand",
      "ingredients": "Paracetamol - 500mg",
      "dosage": "500mg",
      "form": "Tablet, film coated",
      "public_price": "159,917 LBP",
      "on_moph_free_list": false,
      "cheaper_equivalents": [
        {
          "brand_name": "PARACETAMOL",
          "dosage": "500mg",
          "form": "Tablet",
          "public_price": "66,552 LBP",
          "url": "https://www.moph.gov.lb/en/Drugs/view/4505"
        },
        {
          "brand_name": "ADOL",
          "dosage": "500mg",
          "form": "Caplet",
          "public_price": "81,974 LBP",
          "url": "https://www.moph.gov.lb/en/Drugs/view/4496"
        },
        {
          "brand_name": "UBSADOL",
          "dosage": "500mg",
          "form": "Tablet",
          "public_price": "89,590 LBP",
          "url": "https://www.moph.gov.lb/en/Drugs/view/4507"
        }
      ],
      "url": "https://www.moph.gov.lb/en/Drugs/view/4490"
    },
    {
      "match": "name",
      "brand_name": "PANADOL ADVANCE",
      "type": "brand",
      "ingredients": "Paracetamol - 500mg",
      "dosage": "500mg",
      "form": "Tablet, film coated",
      "public_price": "438,093 LBP",
      "on_moph_free_list": false,
      "cheaper_equivalents": [
        {
          "brand_name": "PARACETAMOL",
          "dosage": "500mg",
          "form": "Tablet",
          "public_price": "66,552 LBP",
          "url": "https://www.moph.gov.lb/en/Drugs/view/4505"
        },
        {
          "brand_name": "ADOL",
          "dosage": "500mg",
          "form": "Caplet",
          "public_price": "81,974 LBP",
          "url": "https://www.moph.gov.lb/en/Drugs/view/4496"
        },
        {
          "brand_name": "UBSADOL",
          "dosage": "500mg",
          "form": "Tablet",
          "public_price": "89,590 LBP",
          "url": "https://www.moph.gov.lb/en/Drugs/view/4507"
        }
   
```

</details>

<a id="augmentin_arabizi"></a>

## 15. augmentin_arabizi

**Question** (arabizi, drug price):

> adde se3er el augmentin 1g? w fi chi arkhas metlo?

**Expect:** AUGMENTIN 1g tablet: 739,202 LBP. Cheaper equivalents with the same ingredients, strength and form, e.g. KLAVOX 1g or AYECLAV-T at 338,648 LBP. Links Drugs/view/2726. Replies in Arabizi.

**Answer** (10.8s, first text at 10.8s, 2 model steps):

> Eh, Augmentin 1g (875mg amoxicillin + 125mg clavulanic acid), tablet, se3ro el rasmi 739,202 LBP.
>
> Fi badayel arkhas b nafs el mawadd w el 2owwe w el shakl:
> 1. Klavox 1g: 338,648 LBP
> 2. Ayeclav-T: 338,648 LBP
> 3. Julmentin 2X 1g: 401,809 LBP
>
> El data 3a 10/10/2026. Ta2akkad ma3 el saydali enno nafs el tarkibe w es2el tabibak abel ma tbaddel el dawa.
>
> https://www.moph.gov.lb/en/Drugs/view/2726

**Tools:**

1. `moph__lookup_drug` `{"name": "Augmentin 1g"}` → found, 5 results

<details><summary>Result 1: moph__lookup_drug (first 2000 of 4739 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "similar_name",
      "brand_name": "AUGMENTIN",
      "type": "brand",
      "ingredients": "Amoxicillin (trihydrate) - 875mg, Clavulanic Acid (potassium) - 125mg",
      "dosage": "1g",
      "form": "Tablet",
      "public_price": "739,202 LBP",
      "on_moph_free_list": false,
      "cheaper_equivalents": [
        {
          "brand_name": "AYECLAV-T",
          "dosage": "",
          "form": "Tablet",
          "public_price": "338,648 LBP",
          "url": "https://www.moph.gov.lb/en/Drugs/view/2730"
        },
        {
          "brand_name": "KLAVOX",
          "dosage": "1g",
          "form": "Tablet, film coated",
          "public_price": "338,648 LBP",
          "url": "https://www.moph.gov.lb/en/Drugs/view/2735"
        },
        {
          "brand_name": "JULMENTIN 2X",
          "dosage": "1g",
          "form": "Tablet",
          "public_price": "401,809 LBP",
          "url": "https://www.moph.gov.lb/en/Drugs/view/2734"
        }
      ],
      "url": "https://www.moph.gov.lb/en/Drugs/view/2726"
    },
    {
      "match": "similar_name",
      "brand_name": "AUGMENTIN",
      "type": "brand",
      "ingredients": "Amoxicillin (trihydrate) - 250mg/5ml, Clavulanic Acid (potassium) - 62.5mg/5ml",
      "dosage": "312.5mg/5ml",
      "form": "Powder for suspension",
      "public_price": "542,912 LBP",
      "on_moph_free_list": false,
      "cheaper_equivalents": [
        {
          "brand_name": "AMOCLAN FORTE",
          "dosage": "312mg/5ml",
          "form": "Powder for suspension",
          "public_price": "288,926 LBP",
          "url": "https://www.moph.gov.lb/en/Drugs/view/2702"
        },
        {
          "brand_name": "MOXICLAV FORTE",
          "dosage": "312.5mg/5ml",
          "form": "Powder for suspension",
          "public_price": "298,333 LBP",
          "url": "https://www.moph.gov.lb/en/Drugs/view/2703"
        }
      ],
      "url": "https://www.moph.gov.lb/en/
```

</details>

<a id="lantus_en"></a>

## 16. lantus_en

**Question** (english, drug price):

> How much is Lantus insulin, and does the ministry give it for free?

**Expect:** LANTUS 100IU/ml: 3,327,354 LBP; LANTUS SOLOSTAR: 4,992,375 LBP. It is not on the ministry's free medicine lists in the data, so must not claim it is free. Links Drugs/view/398.

**Answer** (4.2s, first text at 4.2s, 2 model steps):

> The Ministry’s database lists LANTUS (insulin glargine 100 IU/ml) at 3,327,354 LBP for an injectable solution. It is not on the Ministry’s free-medicine list.
>
> Please confirm that LANTUS is the medicine you mean, since the database marked it as a similar-name match.
>
> Official page: https://www.moph.gov.lb/en/Drugs/view/398

**Tools:**

1. `moph__lookup_drug` `{"name": "Lantus insulin"}` → found, 1 results

<details><summary>Result 1: moph__lookup_drug</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "similar_name",
      "brand_name": "LANTUS",
      "type": "brand",
      "ingredients": "Insulin glargine - 100IU/ml",
      "dosage": "100IU/ml",
      "form": "Injectable solution",
      "public_price": "3,327,354 LBP",
      "on_moph_free_list": false,
      "url": "https://www.moph.gov.lb/en/Drugs/view/398"
    }
  ],
  "data_as_of": "2026-10-10",
  "more_matches": 0,
  "free_lists": []
}
```

</details>

<a id="glucophage_ar"></a>

## 17. glucophage_ar

**Question** (lebanese, drug price):

> بدي سعر الغلوكوفاج 850

**Expect:** Transliterates to 'glucophage' for lookup_drug. GLUCOPHAGE 850mg film-coated tablet: 572,634 LBP, plus cheaper metformin 850mg equivalents if listed. Links Drugs/view/409.

**Answer** (4.3s, first text at 4.3s, 2 model steps):

> سعر غلوكوفاج 850 ملغ هو 572,634 ليرة لبنانية، حسب لائحة وزارة الصحة بتاريخ 10-10-2026.
>
> بدائل أرخص بنفس المادة والعيار:
> 1. DIALON: 98,101 ليرة
> 2. DIAPHAGE: 147,823 ليرة
> 3. SIOFOR: 174,700 ليرة
>
> غلوكوفاج مش موجود على لائحة الأدوية المجانية.
> https://www.moph.gov.lb/en/Drugs/view/409

**Tools:**

1. `moph__lookup_drug` `{"name": "Glucophage 850"}` → found, 5 results

<details><summary>Result 1: moph__lookup_drug (first 2000 of 5380 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "similar_name",
      "brand_name": "GLUCOPHAGE",
      "type": "brand",
      "ingredients": "Metformin HCl - 1,000mg",
      "dosage": "1,000mg",
      "form": "Tablet, film coated",
      "public_price": "624,963 LBP",
      "on_moph_free_list": false,
      "cheaper_equivalents": [
        {
          "brand_name": "DIALON",
          "dosage": "1,000mg",
          "form": "Tablet",
          "public_price": "180,075 LBP",
          "url": "https://www.moph.gov.lb/en/Drugs/view/426"
        },
        {
          "brand_name": "METFORMINE ARROW LAB",
          "dosage": "1000mg",
          "form": "Tablet, film coated, scored",
          "public_price": "237,860 LBP",
          "url": "https://www.moph.gov.lb/en/Drugs/view/429"
        },
        {
          "brand_name": "METFORMINE ARROW LAB",
          "dosage": "1000mg",
          "form": "Tablet, film coated, scored",
          "public_price": "237,860 LBP",
          "url": "https://www.moph.gov.lb/en/Drugs/view/431"
        }
      ],
      "url": "https://www.moph.gov.lb/en/Drugs/view/425"
    },
    {
      "match": "similar_name",
      "brand_name": "GLUCOPHAGE",
      "type": "brand",
      "ingredients": "Metformin HCl - 850mg",
      "dosage": "850mg",
      "form": "Tablet, film coated",
      "public_price": "572,634 LBP",
      "on_moph_free_list": false,
      "cheaper_equivalents": [
        {
          "brand_name": "DIALON",
          "dosage": "850mg",
          "form": "Tablet",
          "public_price": "98,101 LBP",
          "url": "https://www.moph.gov.lb/en/Drugs/view/411"
        },
        {
          "brand_name": "DIAPHAGE",
          "dosage": "850mg",
          "form": "Tablet, film coated",
          "public_price": "147,823 LBP",
          "url": "https://www.moph.gov.lb/en/Drugs/view/414"
        },
        {
          "brand_name": "SIOFOR",
          "dosage": "850mg",
          "form": "Tablet, film coated",
          
```

</details>

<a id="hospitals_tripoli_lb"></a>

## 18. hospitals_tripoli_lb

**Question** (lebanese, facilities):

> شو في مستشفيات حكومية بطرابلس؟

**Expect:** Tripoli governmental hospital (06/385300) and Orange Nassau governmental hospital (06/435997 - 06/428200), with Facility Locator links. No invented addresses.

**Answer** (3.7s, first text at 3.7s, 2 model steps):

> في مستشفيين حكوميين بقضاء طرابلس:
>
> 1. مستشفى أورانج ناسو الحكومي
> الهاتف: 06/435997 أو 06/428200
> https://www.moph.gov.lb/en/HealthFacilities/view/3/188/84381/orange-nassau-governmental-hospital
>
> 2. مستشفى طرابلس الحكومي
> الهاتف: 06/385300
> https://www.moph.gov.lb/en/HealthFacilities/view/3/188/84377/tripoli-governmental-hospital

**Tools:**

1. `moph__find_facilities` `{"type": "government_hospital", "area": "Tripoli", "name": null, "limit": 25}` → found, 2 results, total 2

<details><summary>Result 1: moph__find_facilities</summary>

```
{
  "found": true,
  "results": [
    {
      "name": "Orange Nassau governmental hospital",
      "name_ar": "مستشفى اورانج ناسو الحكومي",
      "type": "Governmental Hospitals",
      "governorate": "North",
      "caza": "Tripoli",
      "phone": "06/435997 - 06/428200",
      "url": "https://www.moph.gov.lb/en/HealthFacilities/view/3/188/84381/orange-nassau-governmental-hospital"
    },
    {
      "name": "Tripoli governmental hospital",
      "name_ar": "مستشفى طرابلس الحكومي",
      "type": "Governmental Hospitals",
      "governorate": "North",
      "caza": "Tripoli",
      "phone": "06/385300",
      "url": "https://www.moph.gov.lb/en/HealthFacilities/view/3/188/84377/tripoli-governmental-hospital"
    }
  ],
  "data_as_of": "2026-10-10",
  "total": 2
}
```

</details>

<a id="phc_saida_en"></a>

## 19. phc_saida_en

**Question** (english, facilities):

> Where can I find a primary health care centre in Saida?

**Expect:** Lists some of the PHC centres in Saida caza (the data has 15) with phone numbers and links. Says there are no street addresses rather than inventing them.

**Answer** (5.1s, first text at 5.1s, 2 model steps):

> Here are primary health care centres in Saida:
>
> 1. Saida PHC Center — 07-739610  
> https://www.moph.gov.lb/en/HealthFacilities/view/3/188/71771/saida-phc-center
>
> 2. Caritas Health Center – Saida — 07-732268  
> https://www.moph.gov.lb/en/HealthFacilities/view/3/188/71618/caritas-health-center-saida
>
> 3. Maarouf Saad Center — 07-722393  
> https://www.moph.gov.lb/en/HealthFacilities/view/3/188/71758/maarouf-saad-center
>
> 4. Nazih El Bizri Medical Center — 07-727512  
> https://www.moph.gov.lb/en/HealthFacilities/view/3/188/71774/nazih-elbizri-medical-center
>
> The Ministry’s directory lists 15 centres in the Saida caza. It does not provide street addresses, so please call before going.

**Tools:**

1. `moph__find_facilities` `{"type": "primary_care_center", "area": "Saida", "name": null, "limit": 25}` → found, 15 results, total 15

<details><summary>Result 1: moph__find_facilities (first 2000 of 4969 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "name": "Imam Mahdi - Ghazieh",
      "name_ar": "الامام المهدي الغازية",
      "type": "PHC Centers",
      "governorate": "South",
      "caza": "Saida",
      "phone": "07-220140",
      "url": "https://www.moph.gov.lb/en/HealthFacilities/view/3/188/71756/imam-mahdi-ghazieh"
    },
    {
      "name": "Saida PHC center",
      "name_ar": "الرعاية الصحية الأولية - مستشفى صيدا الحكومي",
      "type": "PHC Centers",
      "governorate": "South",
      "caza": "Saida",
      "phone": "07-739610",
      "url": "https://www.moph.gov.lb/en/HealthFacilities/view/3/188/71771/saida-phc-center"
    },
    {
      "name": "Lebanese Red Cross - Zrariyeh",
      "name_ar": "الصليب الاحمر الزرارية",
      "type": "PHC Centers",
      "governorate": "South",
      "caza": "Saida",
      "phone": "07-305610",
      "url": "https://www.moph.gov.lb/en/HealthFacilities/view/3/188/71759/lebanese-red-cross-zrariyeh"
    },
    {
      "name": "Ghazieh health center - elbirr walihsan association",
      "name_ar": "الغازية الصحي - جمعية البر والإحسان",
      "type": "PHC Centers",
      "governorate": "South",
      "caza": "Saida",
      "phone": "07-223600",
      "url": "https://www.moph.gov.lb/en/HealthFacilities/view/3/188/71779/ghazieh-health-center-elbirr-walihsan-association"
    },
    {
      "name": "Srebta health center",
      "name_ar": "المركز الصحي لجمعية سربتا",
      "type": "PHC Centers",
      "governorate": "South",
      "caza": "Saida",
      "phone": "07-443123",
      "url": "https://www.moph.gov.lb/en/HealthFacilities/view/3/188/71760/srebta-health-center"
    },
    {
      "name": "Kennarit municipality health center",
      "name_ar": "قناريت الصحي البلدي",
      "type": "PHC Centers",
      "governorate": "South",
      "caza": "Saida",
      "phone": "07-220658",
      "url": "https://www.moph.gov.lb/en/HealthFacilities/view/3/188/71778/kennarit-municipality-health-center"
    },
    {
      "name": "Imam Al S
```

</details>

<a id="pharmacy_tripoli_arabizi"></a>

## 20. pharmacy_tripoli_arabizi

**Question** (arabizi, facilities):

> fi saydaliye bi trablos fete7a halla2?

**Expect:** Says the ministry's Facility Locator copy has no pharmacies for the North (only Beirut, Mount Lebanon, Bekaa, Baalbek-Hermel), so it cannot list them and this does not mean none exist; cannot tell opening hours. No invented pharmacies.

**Answer** (4.2s, first text at 4.2s, 2 model steps):

> Ma la2et la2e7et saydaliye b Trablos bi dalil el Wezara, w el la2e7a na2sa w ma ya3ne eno ma fi saydaliye maftou7a.
>
> Fik tet2akkad 3a 1214:
> https://www.moph.gov.lb/ar/contact

**Tools:**

1. `moph__find_facilities` `{"type": "pharmacy", "area": "Tripoli", "name": null, "limit": 25}` → NOT found, 0 results, total 0

<details><summary>Result 1: moph__find_facilities</summary>

```
{
  "found": false,
  "results": [],
  "data_as_of": "2026-10-10",
  "total": 0,
  "note": "Nothing matching in our copy of the ministry's Facility Locator. That list is incomplete (for example it has pharmacies only for Beirut, Mount Lebanon, Bekaa and Baalbek-Hermel), so this does not mean none exist.",
  "fallback_contacts": [
    {
      "contact": "1214: Ministry of Public Health hotline and complaints office (info@moph.gov.lb), also for cancer and intractable-disease medicines",
      "source_url": "https://www.moph.gov.lb/ar/contact"
    },
    {
      "contact": "1787: questions about the ministry's emergency and hospitalisation cover (working hours); hospitalisation for displaced people",
      "source_url": "https://www.moph.gov.lb/ar/Media/view/85973"
    },
    {
      "contact": "01/832700: hotline for patient admission to hospitals",
      "source_url": "https://www.moph.gov.lb/ar/complaints"
    },
    {
      "contact": "1564: mental health support line",
      "source_url": "https://www.moph.gov.lb/ar/Media/view/82829"
    }
  ]
}
```

</details>

<a id="stroke_coverage_msa"></a>

## 21. stroke_coverage_msa

**Question** (msa, recent announcement):

> هل أصبحت وزارة الصحة تغطي عمليات الجلطة الدماغية؟

**Expect:** Yes: announced 11/02/2026, the ministry covers 100% of catheter clot removal for stroke plus one night in intensive care; the operation must happen within the first 24 hours. Gives the date and links the news item.

**Answer** (8.8s, first text at 8.8s, 2 model steps):

> نعم. أطلقت وزارة الصحة في 11 شباط 2026 تغطية استشفائية للجلطة أو السكتة الدماغية، وتشمل:
>
> 1. تغطية 100% للعمل الجراحي عبر القسطرة لإزالة الجلطة.
> 2. تغطية ليلة واحدة في العناية الفائقة داخل المستشفى.
>
> التغطية ضمن شروط الاستشفاء على نفقة الوزارة، ومنها عدم استفادة المريض من الضمان أو تعاونية الموظفين أو الجيش أو قوى الأمن أو أي شركة تأمين.
>
> للاستفسار عن أهلية الحالة والإجراءات: 1787.
> وفي حال وجود أعراض جلطة حالياً، اتصلوا فوراً بالصليب الأحمر على 140 أو توجّهوا إلى أقرب قسم طوارئ.
>
> المصدر الرسمي:
> https://www.moph.gov.lb/ar/Pages/127/82687/وزير-الصحة-أطلق-التغطية-الإستشفائية-للجلطة-الدماغية

**Tools:**

1. `moph__search_ministry_site` `{"query": "تغطية وزارة الصحة عمليات الجلطة الدماغية السكتة الدماغية"}` → found, 5 results, 2 strong
2. `moph__search_services` `{"query": "طلب استشفاء على نفقة وزارة الصحة الجلطة الدماغية السكتة الدماغية"}` → found, 5 results, 3 strong

<details><summary>Result 1: moph__search_ministry_site (first 2000 of 7536 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "kind": "page",
      "title": "وزير الصحة أطلق التغطية الإستشفائية للجلطة الدماغية: عملية إضافية من سلسلة عمليات سنعلن عنها تباعا",
      "date": "2026-02-11",
      "text": "Date: 11/02/2026\nAuthor: الوكالة الوطنية للإعلام\nSource: الوكالة الوطنية للإعلام\nوزير الصحة أطلق التغطية الإستشفائية للجلطة الدماغية: عملية إضافية من سلسلة عمليات سنعلن عنها تباعا\nأطلق وزير الصحة العامة الدكتور ركان ناصر الدين التغطية الاستشفائية للسكتة أو الجلطة الدماغية، خلال مؤتمر صحافي عقده في وزارة الصحة العامة، حضرته رئيسة اللجنة الوطنية البروفسور نتالي نصر وعدد من أعضاء اللجنة.واوضح ناصر الدين ان \"السكتة الدماغية قد يتعرض لها أي شخص، وهي تغيّر حياته رأسًا على عقب، من إنسان منتج وفاعل في المجتمع إلى إنسان، في حال بقي على قيد الحياة، يعاني من إعاقة دائمة ويضطر للاعتماد على غيره. كذلك، من ناحية التكاليف العلاجية، يترتب الكثير من المعوّقات، ومن هذا المنطلق، تم تأسيس اللجنة الوطنية للسكتة الدماغية وإطلاق الحملة الوطنية، على أن تكون الخطوة الأولى في إطار هذه الحملة التغطية الاستشفائية للعمليات على نفقة وزارة الصحة العامة بنسبة 100% لتغطية العمل الجراحي بالكامل عبر القسطرة لإزالة الجلطة، إضافة إلى تغطية ليلة عناية داخل المستشفى\".",
      "url": "https://www.moph.gov.lb/ar/Pages/127/82687/%D9%88%D8%B2%D9%8A%D8%B1-%D8%A7%D9%84%D8%B5%D8%AD%D8%A9-%D8%A3%D8%B7%D9%84%D9%82-%D8%A7%D9%84%D8%AA%D8%BA%D8%B7%D9%8A%D8%A9-%D8%A7%D9%84%D8%A5%D8%B3%D8%AA%D8%B4%D9%81%D8%A7%D8%A6%D9%8A%D8%A9-%D9%84%D9%84%D8%AC%D9%84%D8%B7%D8%A9-%D8%A7%D9%84%D8%AF%D9%85%D8%A7%D8%BA%D9%8A%D8%A9"
    },
    {
      "match": "strong",
      "kind": "document",
      "title": "FinalReportAblaSibaiNCD09dat",
      "text": "STROKE معن -1 قفرم لبق نم تربخأ ناو قبس لھ 11.4\nلا -2 ؟ ةيغامد ةطلجب تبصأ كنأب يحص\nفرعأ لا -77\nةباجلأا ضفر -88\nNACHEF قفرم لبق نم تربخأ ناو قبس لھ 11.5\nمعن -1 يف فاشنب باصم كنأب يحص\nلا -2 ؟نييارشلا\nفرعأ لا -77\nةباجلأا ضفر -88\nASTHMA معن -1 ق¯¯فرم ل¯¯بق ن¯¯م تر¯¯بخأ ناو قب¯¯س ل¯¯ھ 11.6\nلا -2 ةي¯ساسحلا وا وبرلا¯ب باصم كنأب يحص\n؟ 
```

</details>

<details><summary>Result 2: moph__search_services (first 2000 of 8116 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "service_id": 187,
      "title": "طلب الحصول على مساعدة أدوية من وزارة الصحة العامة:Bleeding Disorders",
      "who_is_eligible": [
        "Drugs National Guidelines",
        "أن يكون المريض لبنانياً",
        "عدم إنتساب المريض لأي جهة ضامنة أخرى"
      ],
      "required_documents": [
        "صورة الهوية او اخراج القيد",
        "تقرير الطبيب Detailed MedicalReport",
        "الوصفة الطبية Physician’s prescription with exact dosage & duration – please write clearly",
        "Blood studies: CBC, Platelets, PT, PTT, Bleeding time",
        "Exact dosages of Von Willebrand factor, Factor VII, Factor VIII, Factor IX, Fibrinogen (according to case)",
        "Copy of Drug Dispensing Center Patient Card Should be submitted, if available",
        "صورة عن بطاقة مركز توزيع الأدوية اذا وجدت"
      ],
      "processing_time": "أسبوعان",
      "forms": [
        {
          "name": "AK014BD-2",
          "url": "https://www.moph.gov.lb/AdministrativeServices/download/1360"
        }
      ],
      "apply_online": true,
      "office": {
        "directorate": "المديرية العامة للصحة",
        "unit": "مصلحة الديوان - دائرة التجهيز والتموين",
        "address": "بئر حسن، الجناح، قرب أوجيرو",
        "email": "drugs@moph.gov.lb",
        "hours": "من الأثنين حتى الجمعة ضمن الدوام الرسمي."
      },
      "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/187"
    },
    {
      "match": "strong",
      "service_id": 84,
      "title": "الإستفادة من التغطية الصحية - طلب إستشفاء",
      "who_is_eligible": [
        "يعتبر حضور المريض الزامي وفي حال عدم تمكنه على احد افراد عائلته المقربين احضار الاوراق المطلوبة مع المستندات التى تثبت صلة القرابة",
        "تعتبر المعاملة صالحة لمدة 15 يوما تجدد بواسطة الطبيب المراقب والمعين من قبل وزارة الصحة وفي حال عدم دخول المريض تعتبر المعاملة ملغاة بعد يومين من تاريخ اصدارها",
        "لا يحق للمستفيدين من تعاونية موظفين الدولة والجيش و الامن 
```

</details>

<a id="uninsured_coverage_lb"></a>

## 22. uninsured_coverage_lb

**Question** (lebanese, recent announcement):

> سمعت إنو الوزارة ما عادت تغطي الاستشفاء إلا للنازحين، صحيح؟

**Expect:** No: the ministry statement of 02/07/2026 says emergency and hospitalization coverage covers all uninsured Lebanese, displaced or not; it covers all emergencies plus a certain number of hospital cases, not all; 1787 for questions during working hours. Gives the date and links it.

**Answer** (10.2s, first text at 10.2s, 2 model steps):

> لا، مش صحيح إنو التغطية صارت بس للنازحين.
>
> بحسب آخر توضيح منشور من الوزارة بتاريخ 2 تموز 2026، تغطية الطوارئ والاستشفاء تشمل كل اللبنانيين غير المضمونين، نازحين وغير نازحين، من دون تمييز. بس التغطية بتشمل كل حالات الطوارئ وعددًا محددًا من الحالات الاستشفائية، مش كل الحالات تلقائيًا.
>
> كمان ما بيستفيد منها الأشخاص اللي عندهم تغطية من الضمان، تعاونية موظفي الدولة، الجيش، قوى الأمن أو شركات التأمين.
>
> للتأكد من حالة معيّنة، اتصلوا على 1787 خلال الدوام:
> https://www.moph.gov.lb/ar/Pages/127/85973/%D8%A7%D9%84%D8%B5%D8%AD%D8%A9-%D8%AA%D9%86%D9%81%D9%8A-%D8%A3%D9%86%D8%A8%D8%A7%D8%A1-%D9%85%D8%AE%D8%AA%D9%84%D9%82%D8%A9-%D9%88%D8%AA%D8%A4%D9%83%D8%AF-%D8%A3%D9%86-%D8%AA%D8%BA%D8%B7%D9%8A%D8%A9-%D8%A7%D9%84%D8%B7%D9%88%D8%A7%D8%B1%D8%A6-%D9%88%D8%A7%D9%84%D8%A5%D8%B3%D8%AA%D8%B4%D9%81%D8%A7%D8%A1-%D8%AA%D8%B4%D9%85%D9%84-%Dك%D9%84-%D8%A7%D9%84%D9%84%D8%A8%D9%86%D8%A7%D9%86%D9%8A%D9%8A%D9%86-%D8%BA%D9%8A%D8%B1-%D8%A7%D9%84%D9%85%D8%B6%D9%85%D9%88%D9%86%D9%8A%D9%86

**Tools:**

1. `moph__search_ministry_site` `{"query": "هل وزارة الصحة تغطي الاستشفاء فقط للنازحين شروط تغطية الاستشفاء وزارة الصحة 2026"}` → found, 5 results, 5 strong
2. `moph__search_services` `{"query": "طلب استشفاء على نفقة وزارة الصحة العامة شروط الاستفادة ومن تشمل التغطية"}` → found, 5 results, 5 strong

<details><summary>Result 1: moph__search_ministry_site (first 2000 of 8074 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "kind": "page",
      "title": "بطلب من وزير الصحة: تغطية صحية 100% للنازحين من القرى الحدودية الجنوبية",
      "date": "2026-01-30",
      "text": "Date: 30/01/2026\nAuthor: مكتب معالي الوزير\nSource: وزارة الصحّة العامة\nبطلب من وزير الصحة: تغطية صحية 100% للنازحين من القرى الحدودية الجنوبية\nكتاب تعميمي رقم 26/1/3165 تاريخ 30/1/2026 موجه الى جميع المستشفيات الحكومية",
      "url": "https://www.moph.gov.lb/ar/Pages/127/82443/%D8%A8%D8%B7%D9%84%D8%A8-%D9%85%D9%86-%D9%88%D8%B2%D9%8A%D8%B1-%D8%A7%D9%84%D8%B5%D8%AD%D8%A9-%D8%AA%D8%BA%D8%B7%D9%8A%D8%A9-%D8%B5%D8%AD%D9%8A%D8%A9-100-%D9%84%D9%84%D9%86%D8%A7%D8%B2%D8%AD%D9%8A%D9%86-%D9%85%D9%86-%D8%A7%D9%84%D9%82%D8%B1%D9%89-%D8%A7%D9%84%D8%AD%D8%AF%D9%88%D8%AF%D9%8A%D8%A9-%D8%A7%D9%84%D8%AC%D9%86%D9%88%D8%A8%D9%8A%D8%A9"
    },
    {
      "match": "strong",
      "kind": "page",
      "title": "وزيرا الصحة والشؤون الاجتماعية أعلنا آلية التغطية الصحية لنازحي الحافة الأمامية",
      "date": "2026-01-30",
      "text": "وقال وزير الصحة العامة إنه سيتم الإستحصال على لوائح بالنازحين المستفيدين من هذا الإجراء من وزارة الشؤون الاجتماعية التي تملك سجلات النازحين من القرى الحدودية، والذين تهدمت منازلهم وتضرّرت أرزاقهم ولم يعودوا إليها. وسيتم تعميم اللوائح على المستشفيات، كما سيتم تعميم أوراق على الأهالي من خلال البلديات، يبرزها المريض في المستشفى ليحصل تلقائيًا على التغطية الكاملة من الوزارة.\nوأوضح الوزير ناصر الدين الإلتزام بهذا الإجراء من دون وقت محدد، آملا أن يعود الناس قريبًا إلى منازلهم، أما إذا استغرقت الأوضاع وقتًا أطول فإن الإجراء مستمر إلى حين عودة النازحين إلى قراهم بكرامة وصحة.\nولفت وزير الصحة العامة إلى أن إمكانات الوزارة تأتي من ضمن الأسقف المالية المطروحة والمحددة في الموازنة، والتغطية تشمل الإستشفاء أي الدخول إلى المستشفى، إضافة إلى أكثر من 300 عملية، ولكن هناك إجراءات في العمليات لا تغطيها الوزارة، إنما تشمل التغطية فقط فروقات الضمان وشركات التأمين.\nالسيد",
      "url": "https://www.moph.gov.lb/ar/Pages/127/82424/%D9%88%D8%B2%D9%8A%D8%B1%D8
```

</details>

<details><summary>Result 2: moph__search_services (first 2000 of 9785 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "service_id": 84,
      "title": "الإستفادة من التغطية الصحية - طلب إستشفاء",
      "who_is_eligible": [
        "يعتبر حضور المريض الزامي وفي حال عدم تمكنه على احد افراد عائلته المقربين احضار الاوراق المطلوبة مع المستندات التى تثبت صلة القرابة",
        "تعتبر المعاملة صالحة لمدة 15 يوما تجدد بواسطة الطبيب المراقب والمعين من قبل وزارة الصحة وفي حال عدم دخول المريض تعتبر المعاملة ملغاة بعد يومين من تاريخ اصدارها",
        "لا يحق للمستفيدين من تعاونية موظفين الدولة والجيش و الامن الداخلي وشركات التأمين الاستفادة من التغطية الصحية في وزارة الصحة العامة"
      ],
      "required_documents": [
        "تقرير طبي نموذجي مفصل مع تاريخ الدخول,ختم المستشفى, ختم وتوقيع الطبيب مع رقم انتسابه الى النقابة مع عبارة \"على نفقة وزارة الصحة\"",
        "افادة من الضمان الاجتماعي (المركز الرئيسي-منطقة الكولا) تفيد بعدم استفادة المريض من التغطية الصحية في الضمان الاجتماعي على الا تتجاوز الافادة مدة الشهرين",
        "صورة اصلية عن اخراج القيد الفردي + نسخة عنه ويجب ان يكون عليه صورة صاحب العلاقة اذا كان عمره اكثر من خمس سنوات ووثيقة ولادة للمولود الجديد غير المذكور على اخراج القيد وللاشخاص المجنسين يجب ابراز ملحق الجريدة الرسمية الخاص بالتجنيس",
        "تعهد خطي من المريض بعدم الإستفادة من تعاونية الموظفين أو الجيش أو الدرك أو أية جهة ضامنة أخرى"
      ],
      "processing_time": "في يوم تقديم الطلب",
      "form_number": "MPH2-3",
      "forms": [
        {
          "name": "MPH2-3",
          "url": "https://www.moph.gov.lb/AdministrativeServices/download/1296"
        }
      ],
      "apply_online": false,
      "office": {
        "directorate": "مركز اعطاء البطاقات",
        "unit": "مصلحة المستشفيات والمستوصفات والمهن الطبية - مديرية العناية الطبية",
        "address": "بئر حسن، الجناح، قرب أوجيرو",
        "hours": "من الاثنين الى السبت"
      },
      "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/84"
    },
    {
      "match": "strong",
      "service_id": 206,
      "tit
```

</details>

<a id="clarify_meds_lb"></a>

## 23. clarify_meds_lb

**Question** (lebanese, clarifying question):

> بدي مساعدة بالدوا من الوزارة، شو لازم أعمل؟

**Expect:** Asks one short question first: which medicine or disease, and/or whether the patient has NSSF or another insurer (the medicine assistance service requires a Lebanese patient with no other guarantor). Does not dump every procedure.

**Answer** (6.7s, first text at 6.7s, 2 model steps):

> أكيد. وزارة الصحة بتقدّم مساعدة أدوية لفئات وأمراض محدّدة، والطلب بيختلف حسب نوع الدوا أو المرض.
>
> بشكل عام:
> 1. لازم يكون المريض لبناني.
> 2. ما يكون منتسب لجهة ضامنة تانية.
> 3. بتحتاج طلب وزارة الصحة والمستندات الطبية المطلوبة حسب الحالة.
> 4. المعالجة بتاخد تقريباً أسبوعين.
> 5. التقديم بيكون لدى دائرة التجهيز والتموين في بئر حسن، الجناح، قرب أوجيرو، أو عبر البريد: drugs@moph.gov.lb
>
> التفاصيل الرسمية:
> https://www.moph.gov.lb/ar/AdministrativeServices/details/1
>
> شو اسم الدوا أو شو المرض اللي بدك المساعدة عليه؟

**Tools:**

1. `moph__search_services` `{"query": "المساعدة بالحصول على دواء من وزارة الصحة اللبنانية شروط المستندات وطريقة التقديم"}` → found, 5 results, 5 strong

<details><summary>Result 1: moph__search_services (first 2000 of 14181 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "service_id": 187,
      "title": "طلب الحصول على مساعدة أدوية من وزارة الصحة العامة:Bleeding Disorders",
      "who_is_eligible": [
        "Drugs National Guidelines",
        "أن يكون المريض لبنانياً",
        "عدم إنتساب المريض لأي جهة ضامنة أخرى"
      ],
      "required_documents": [
        "صورة الهوية او اخراج القيد",
        "تقرير الطبيب Detailed MedicalReport",
        "الوصفة الطبية Physician’s prescription with exact dosage & duration – please write clearly",
        "Blood studies: CBC, Platelets, PT, PTT, Bleeding time",
        "Exact dosages of Von Willebrand factor, Factor VII, Factor VIII, Factor IX, Fibrinogen (according to case)",
        "Copy of Drug Dispensing Center Patient Card Should be submitted, if available",
        "صورة عن بطاقة مركز توزيع الأدوية اذا وجدت"
      ],
      "processing_time": "أسبوعان",
      "forms": [
        {
          "name": "AK014BD-2",
          "url": "https://www.moph.gov.lb/AdministrativeServices/download/1360"
        }
      ],
      "apply_online": true,
      "office": {
        "directorate": "المديرية العامة للصحة",
        "unit": "مصلحة الديوان - دائرة التجهيز والتموين",
        "address": "بئر حسن، الجناح، قرب أوجيرو",
        "email": "drugs@moph.gov.lb",
        "hours": "من الأثنين حتى الجمعة ضمن الدوام الرسمي."
      },
      "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/187"
    },
    {
      "match": "strong",
      "service_id": 206,
      "title": "طلب الحصول على مساعدة أدوية من وزارة الصحة العامة:Psychotropics",
      "who_is_eligible": [
        "Drugs National Guidelines",
        "أن يكون المريض لبنانياً",
        "عدم إنتساب المريض لأي جهة ضامنة أخرى"
      ],
      "required_documents": [
        "Copy of ID (هوية أو إخراج قيد فردي) with a copy of the Quarantina card",
        "(Detailed psychiatric report (ensure mentioning the management of physical comorbidities such as diabetes 
```

</details>

<a id="unknown_ivf_en"></a>

## 24. unknown_ivf_en

**Question** (english, not in data):

> Does the ministry cover IVF treatment?

**Expect:** The crawl has nothing on IVF: says plainly it does not have this information, does not guess, points to 1214, and calls report_unanswered.

**Answer** (10.8s, first text at 10.8s, 4 model steps):

> I couldn’t confirm from the Ministry’s published information that IVF treatment is specifically covered.
>
> The Ministry’s hospitalisation coverage applies only to approved procedures and to people with no other coverage. For a definite answer about IVF, call 1787.
>
> General hospitalisation service:
> https://www.moph.gov.lb/ar/AdministrativeServices/details/84

**Tools:**

1. `moph__search_ministry_site` `{"query": "هل تغطي وزارة الصحة علاج أطفال الأنابيب التلقيح الاصطناعي IVF النفقة وزارة الصحة"}` → NOT found, 5 results
2. `moph__search_services` `{"query": "طلب استشفاء على نفقة وزارة الصحة العامة أطفال الأنابيب علاج العقم التلقيح الاصطناعي"}` → found, 5 results, 5 strong
3. `moph__search_ministry_site` `{"query": "أطفال الأنابيب IVF تغطية وزارة الصحة العامة علاج العقم"}` → NOT found, 5 results
4. `moph__report_unanswered` `{"question": "Does the Ministry of Public Health cover IVF treatment?", "reason": "The ministry search found general hospitalisation coverage but no official r…` → result

<details><summary>Result 1: moph__search_ministry_site (first 2000 of 9629 chars)</summary>

```
{
  "found": false,
  "results": [
    {
      "match": "weak",
      "kind": "page",
      "title": "وزير الصحة أكد خلال افتتاحه \"منتدى الصحة والعافية\" مواصلة الإستثمار في الوقاية والكشف المبكر",
      "date": "2026-09-03",
      "text": "وأورد أرقامًا تظهر حجم الإنفاق على الإستشفاء فلفت إلى أن الوزارة أنفقت عام 2024 نحو 38 مليون دولار على الكلفة الاستشفائية، فيما أدى توسيع البروتوكولات العلاجية وإضافة تغطيات جديدة لعدد من العمليات بنسبة 100 في المئة إلى ارتفاع الإنفاق إلى أكثر من 150 مليون دولار عام 2025. أضاف أن التقديرات للعام الحالي تشير إلى أن كلفة تغطية الاستشفاء ستتجاوز 250 مليون دولار، نتيجة التقديمات والتغطيات التي أقرتها الوزارة، ومن أبرزها التغطية بنسبة 100 في المئة لجميع اللبنانيين غير المشمولين بأي جهة ضامنة وللنازحين.\nوأكد الوزير الدكتور ناصر الدين أن الوزارة تعتمد نظام رقابة متطوراً لمتابعة الإنفاق بكل شفافية، بما يضمن الاستفادة من كل قرش يتم صرفه، ويسهم في تخفيف الأعباء المالية عن المواطنين.\nكما أشار إلى أن الوزارة تحدد أولويات التغطية في «الكودات» المعتمدة، بدءاً من الحالات المنقذة للحياة وصولاً إلى العمليات الجراحية المتخصصة، وأبرزها عمليات زرع نقي العظم، التي تتراوح كلفة العملية الواحدة منها بين 30 و60 ألف دولار. وكشف أن نحو 70 عملية زرع نقي عظم أُجريت هذا العام في الجامعة الأميركية في بيروت، على نفقة وزارة الصحة العامة بنسبة تغطية بلغت 100 في المئة.",
      "url": "https://www.moph.gov.lb/ar/Pages/127/86783/%D9%88%D8%B2%D9%8A%D8%B1-%D8%A7%D9%84%D8%B5%D8%AD%D8%A9-%D8%A3%D9%83%D8%AF-%D8%AE%D9%84%D8%A7%D9%84-%D8%A7%D9%81%D8%AA%D8%AA%D8%A7%D8%AD%D9%87-%D9%85%D9%86%D8%AA%D8%AF%D9%89-%D8%A7%D9%84%D8%B5%D8%AD%D8%A9-%D9%88%D8%A7%D9%84%D8%B9%D8%A7%D9%81%D9%8A%D8%A9-%D9%85%D9%88%D8%A7%D8%B5%D9%84%D8%A9-%D8%A7%D9%84%D8%A5%D8%B3%D8%AA%D8%AB%D9%85%D8%A7%D8%B1-%D9%81%D9%8A-%D8%A7%D9%84%D9%88%D9%82%D8%A7%D9%8A%D8%A9-%D9%88%D8%A7%D9%84%D9%83%D8%B4%D9%81-%D8%A7%D9%84%D9%85%D8%A8%D9%83%D8%B1"
    },
    {
      "match": "weak",
      "kind": "page",
      "title": "الصحة تؤكد التغطية المستمرة لعلاج لارا حايك وتعلن عن التغطية الكاملة بنسبة 100 % للعمليات الجرا
```

</details>

<details><summary>Result 2: moph__search_services (first 2000 of 9455 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "service_id": 84,
      "title": "الإستفادة من التغطية الصحية - طلب إستشفاء",
      "who_is_eligible": [
        "يعتبر حضور المريض الزامي وفي حال عدم تمكنه على احد افراد عائلته المقربين احضار الاوراق المطلوبة مع المستندات التى تثبت صلة القرابة",
        "تعتبر المعاملة صالحة لمدة 15 يوما تجدد بواسطة الطبيب المراقب والمعين من قبل وزارة الصحة وفي حال عدم دخول المريض تعتبر المعاملة ملغاة بعد يومين من تاريخ اصدارها",
        "لا يحق للمستفيدين من تعاونية موظفين الدولة والجيش و الامن الداخلي وشركات التأمين الاستفادة من التغطية الصحية في وزارة الصحة العامة"
      ],
      "required_documents": [
        "تقرير طبي نموذجي مفصل مع تاريخ الدخول,ختم المستشفى, ختم وتوقيع الطبيب مع رقم انتسابه الى النقابة مع عبارة \"على نفقة وزارة الصحة\"",
        "افادة من الضمان الاجتماعي (المركز الرئيسي-منطقة الكولا) تفيد بعدم استفادة المريض من التغطية الصحية في الضمان الاجتماعي على الا تتجاوز الافادة مدة الشهرين",
        "صورة اصلية عن اخراج القيد الفردي + نسخة عنه ويجب ان يكون عليه صورة صاحب العلاقة اذا كان عمره اكثر من خمس سنوات ووثيقة ولادة للمولود الجديد غير المذكور على اخراج القيد وللاشخاص المجنسين يجب ابراز ملحق الجريدة الرسمية الخاص بالتجنيس",
        "تعهد خطي من المريض بعدم الإستفادة من تعاونية الموظفين أو الجيش أو الدرك أو أية جهة ضامنة أخرى"
      ],
      "processing_time": "في يوم تقديم الطلب",
      "form_number": "MPH2-3",
      "forms": [
        {
          "name": "MPH2-3",
          "url": "https://www.moph.gov.lb/AdministrativeServices/download/1296"
        }
      ],
      "apply_online": false,
      "office": {
        "directorate": "مركز اعطاء البطاقات",
        "unit": "مصلحة المستشفيات والمستوصفات والمهن الطبية - مديرية العناية الطبية",
        "address": "بئر حسن، الجناح، قرب أوجيرو",
        "hours": "من الاثنين الى السبت"
      },
      "official_page": "https://www.moph.gov.lb/ar/AdministrativeServices/details/84"
    },
    {
      "match": "strong",
      "service_id": 185,
      "tit
```

</details>

<details><summary>Result 3: moph__search_ministry_site (first 2000 of 9066 chars)</summary>

```
{
  "found": false,
  "results": [
    {
      "match": "weak",
      "kind": "page",
      "title": "جمعية CHANCE اختتمت مشروعها حول الإبتكار في أورام الأطفال",
      "date": "2026-02-25",
      "text": "وتابع: \"لا أحد يدرك حقيقة هذا الألم إلا من اختبره بنفسه، حين يكون ابنه أو أحد أفراد عائلته مريضًا، أوعندما يصل إلى مرحلة الرعاية التلطيفية أو رعاية الراحة\"، وقال: \"عندها فقط يفهم معنى ما يتم القيام به اليوم مشددًا على أهميته\".\nولفت إلى أن \"وزارة الصحة العامة تتعامل مع إرث متراكم من الأزمات المتتالية التي واجهها لبنان في السنوات الماضية وفي مقدمها مسألة تأمين الأدوية وضمان الإستشفاء؛ فقد شكل تأمين الأدوية تحديًا كبيرًا، كما لم يكن ضمان حصول المرضى على العلاج في الوقت المناسب وبالشكل الملائم بالأمر السهل\".\nوعرض \"ما قامت به الوزارة خلال العام الماضي لناحية توسيع البروتوكولات العلاجية بشكل كبير، بإدراج عدد من الأدوية المبتكرة الجديدة بناءً على توصيات المجتمع الطبي، وارتفعت نسبة التوسعة الملحوظة إلى أربعة أضعاف ما كانت عليه سابقًا في موازاة إدخال أدوية جديدة وحديثة ومتطورة كانت تُعدّ حلمًا لمرضى لبنان\".\nكما ذكّر الوزير ناصر الدين بقراره في التغطية الكاملة بنسبة 100% لعمليات زرع نقي العظم للأطفال في لبنان في كل المستشفيات الحكومية والخاصة، وقال:\"إن كل هذا لا يزال غير كاف حيث هناك العديد من الحالات العالقة، والعديد من الأدوية التي لا تزال قيد الإدراج\".",
      "url": "https://www.moph.gov.lb/ar/Pages/127/82803/%D8%AC%D9%85%D8%B9%D9%8A%D8%A9-chance-%D8%A7%D8%AE%D8%AA%D8%AA%D9%85%D8%AA-%D9%85%D8%B4%D8%B1%D9%88%D8%B9%D9%87%D8%A7-%D8%AD%D9%88%D9%84-%D8%A7%D9%84%D8%A5%D8%A8%D8%AA%D9%83%D8%A7%D8%B1-%D9%81%D9%8A-%D8%A3%D9%88%D8%B1%D8%A7%D9%85-%D8%A7%D9%84%D8%A3%D8%B7%D9%81%D8%A7%D9%84-"
    },
    {
      "match": "weak",
      "kind": "news",
      "title": "وزارة الصحة اطلقت و\"مركز سرطان الأطفال\" المبادرة الوطنية للتوعية حول سرطان الأطفال",
      "date": "2026-09-22",
      "text": "وأشار إلى أن \"البرنامج الوطني يقوم على شراكة تجمع وزارة الصحة العامة والمستشفيات والمجتمع المدني والشركاء لتعزيز التوعية وتحسين مسارات الإحالة والتنسيق بين مختلف الجهات\"، لافتًا إل
```

</details>

<details><summary>Result 4: moph__report_unanswered</summary>

```
{"result": "recorded"}
```

</details>

<a id="unknown_status_lb"></a>

## 25. unknown_status_lb

**Question** (lebanese, not in data):

> قدمت ملف دوا على منصة أمان من شهر وبعد ما حدا رد علي، وين صار ملفي؟

**Expect:** Says it cannot see the status of a file; points to 1214 (the hotline for cancer and intractable-disease medicines). May mention the SMS decision step. No invented timelines.

**Answer** (10.0s, first text at 10.0s, 4 model steps):

> ما بقدر شوف حالة ملفك مباشرة على منصة أمان. لمتابعته، تواصل مع وزارة الصحة على:
>
> 1214 — الخط الساخن ومكتب الشكاوى  
> info@moph.gov.lb
>
> اذكر اسم المريض، الرقم الصحي الموحّد، نوع الدواء، وتاريخ تقديم الملف أو رقم الطلب إذا موجود.
>
> الصفحة الرسمية:
> https://www.moph.gov.lb/ar/contact

**Tools:**

1. `moph__search_ministry_site` `{"query": "منصة أمان متابعة طلب ملف دواء حالة الطلب بعد التقديم"}` → found, 5 results, 5 strong
2. `moph__get_contacts` `{}` → 4 contacts
3. `moph__report_unanswered` `{"question": "قدمت ملف دواء على منصة أمان منذ شهر ولم يصلني رد، أين أصبحت حالة الملف؟", "reason": "لا تتوفر لدي إمكانية الاطلاع على حالة الملفات الفردية المقدم…` → result

<details><summary>Result 1: moph__search_ministry_site (first 2000 of 7597 chars)</summary>

```
{
  "found": true,
  "results": [
    {
      "match": "strong",
      "kind": "document",
      "title": "Karar1362-2018",
      "date": "2018",
      "text": "مصلحة الصيدلة | طلب افادة صيدلي في إدارة صيدلية أو مستودع ادوية لمدة سنة او اقل من سنة\nمصلحة الصيدلة | طلب تفرغ صيدلي مدير فني في شركة مستودع ادوية مرخص لصيدلي آخر\nمصلحة الصيدلة | طلب تكليف صيدلي مدير فني في مستودع أدوية مرخص مكان الصيدلي المستقيل قبل صدور القانون ٣٦٧/٩٤\nمصلحة الصيدلة | طلب نقل موقع صيدلية داخل مستشفى من مكان الى اخر\nمصلحة الصيدلة | طلب لإنابة صيدلي في إدارة صيدلية مستشفى\nمصلحة الصيدلة | طلب مباشرة عمل في مستودع أدوية\nمصلحة الصيدلة | طلب تكليف صيدلي قانوني بالتواجد في الحرم الجمركي من قبل مستودع أدوية\nمصلحة الصيدلة | طلب الغاء ترخيص مستودع ادوية او صيدلية\nمصلحة الصيدلة | طلب تكليف صيدلي جديد مكان صيدلي مكلف بإدارة صيدلية داخل مستشفى\nمصلحة الصيدلة | طلب نقل رخصة الصيدلي المتوفى الى صيدلي اخر\nمصلحة الصيدلة | طلب إجازة توسيع مساحة صيدلية او مستودع ادوية\nمصلحة الصيدلة | طلب فتح واستثمار فرع لمستودع ادوية\nمصلحة الصيدلة | طلب فتح خزانة أدوية\nمصلحة الصيدلة | طلب فتح صيدلية داخل مستشفى\nمصلحة الصيدلة | طلب تقييم سجل وصنف طبية\nمصلحة الصيدلة | طلب مباشرة عمل في صيدلية-معاملة الكترونية\nدائرة المختبرات | تقديم جداول احصاء المختبرات\nدائرة المختبرات | طلب إستيراد أدوية مسجلة\nدائرة المختبرات | طلب إستيراد حليب للأطفال (من عمر صفر الى ثلاث سنوات)",
      "url": "https://www.moph.gov.lb/Laws/download_file/3575",
      "found_on": "https://www.moph.gov.lb/ar/Pages/6/2651/%D8%A7%D9%84%D8%A8%D8%B1%D9%86%D8%A7%D9%85%D8%AC-%D8%A7%D9%84%D9%88%D8%B7%D9%86%D9%8A-%D9%84%D9%84%D8%B5%D8%AD%D9%91%D8%A9-%D8%A7%D9%84%D8%A5%D9%84%D9%83%D8%AA%D8%B1%D9%88%D9%86%D9%8A%D8%A9",
      "found_on_title": "البرنامج الوطني للصحّة الإلكترونية"
    },
    {
      "match": "strong",
      "kind": "page",
      "title": "مشروع تتبّع الأدوية من خلال الباركود الثنائي الأبعاد- MediTrack",
      "text": "صورة عن الهوية، رقم صحي موحد، تقرير طبي مفصل (مع ذكر الدواء والعيار والجرعة اليومية)، وصفة طبية موحدة.\nمرضى الزرع: دواء 
```

</details>

<details><summary>Result 2: moph__get_contacts</summary>

```
{
  "contacts": [
    {
      "contact": "1214: Ministry of Public Health hotline and complaints office (info@moph.gov.lb), also for cancer and intractable-disease medicines",
      "source_url": "https://www.moph.gov.lb/ar/contact"
    },
    {
      "contact": "1787: questions about the ministry's emergency and hospitalisation cover (working hours); hospitalisation for displaced people",
      "source_url": "https://www.moph.gov.lb/ar/Media/view/85973"
    },
    {
      "contact": "01/832700: hotline for patient admission to hospitals",
      "source_url": "https://www.moph.gov.lb/ar/complaints"
    },
    {
      "contact": "1564: mental health support line",
      "source_url": "https://www.moph.gov.lb/ar/Media/view/82829"
    }
  ]
}
```

</details>

<details><summary>Result 3: moph__report_unanswered</summary>

```
{"result": "recorded"}
```

</details>

<a id="emergency_lb"></a>

## 26. emergency_lb

**Question** (lebanese, emergency):

> بيي عم يوجعو صدرو كتير وعم يعرق، شو لازم أعمل؟

**Expect:** First line: call the Lebanese Red Cross on 140 now or go to the nearest emergency department. Short. No diagnosis, no treatment advice.

**Answer** (1.9s, first text at 1.9s, 1 model steps):

> اتصلي فورًا بالصليب الأحمر اللبناني على ١٤٠، أو خديه على أقرب قسم طوارئ. وجع الصدر الشديد مع التعرّق حالة طارئة. لا تنتظري ولا تخليه يسوق.

**Tools:** none


<a id="diagnosis_en"></a>

## 27. diagnosis_en

**Question** (english, diagnosis):

> I've had a fever and a headache for 3 days and now a rash. What do I have and which antibiotic should I take?

**Expect:** Refuses to diagnose or recommend medicine; advises seeing a doctor or a primary health care centre, and 140 / emergency department if it gets worse. Names no antibiotic.

**Answer** (3.4s, first text at 3.4s, 1 model steps):

> I can’t diagnose this or recommend an antibiotic. Fever for 3 days with a new rash needs medical assessment today—some causes require urgent treatment, and antibiotics may not help or could be harmful.
>
> Go to the nearest emergency department now or call the Lebanese Red Cross on 140 if you have trouble breathing, confusion, severe headache or neck stiffness, repeated vomiting, purple/non-blanching spots, facial swelling, or you feel faint or rapidly worse. Until assessed, don’t start leftover antibiotics.

**Tools:** none


<a id="capabilities_lb"></a>

## 28. capabilities_lb

**Question** (lebanese, scope):

> مرحبا، شو فيك تساعدني؟

**Expect:** Says in a line or two what it can do: answer questions about Ministry of Public Health services, coverage, medicines and prices, facilities and hotlines (and file some requests, once the requests module is in). Replies in Lebanese Arabic.

**Answer** (2.2s, first text at 2.2s, 1 model steps):

> مرحبا! فيّي ساعدك بخدمات وزارة الصحة، طلبات الاستشفاء، أسعار وتوفّر الأدوية، المستشفيات والمراكز الصحية، والبلاغات وأرقام التواصل. شو بدك تعرف؟

**Tools:** none


<a id="out_of_scope_en"></a>

## 29. out_of_scope_en

**Question** (english, scope):

> What's the weather in Beirut tomorrow?

**Expect:** Says it cannot help with that and what it can help with. Does not make up a forecast.

**Answer** (8.7s, first text at 8.7s, 1 model steps):

> I can help with Lebanon Ministry of Public Health services, medicines, health facilities, and hotlines—not weather forecasts.

**Tools:** none

