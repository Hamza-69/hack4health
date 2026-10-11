# Demo runbook

The jury demo lasts 3 minutes, and the stage version 10. Everything runs on the demo laptop.

## Before the demo

1. `uv run h4h dev` from the repo root. It starts the core (:8000), the admin panel (:5173), the modules and the web chat (:9000).
2. `uv run python -m sandpit.demo.reset`. This clears chats, tickets and requests, so the next request is W-1042.
3. Optional, after the reset: `uv run python -m sandpit.eval.run`. In about 2 minutes it fills "What people ask" with 29 realistic questions. It files no requests, so W-1042 stays next.
4. Open the admin panel at http://localhost:5173 and log in as the desk account. Its login is in the root `.env`, as `DEMO_DESK_LOGIN`. Go to **Ministry Inbox**. Keep a second tab logged in as `DEMO_OPS_LOGIN` on **Ministry Info → What people ask**.
5. Print `sandpit/demo/specimens.html`, or show it on a second screen: the medical report, the NSSF statement and the إخراج قيد.
6. Phone: the Wasel WhatsApp number linked, and the family's phone ready. Fallback: the web chat at http://localhost:9000, where you press **New chat**.

## The story

1. **Voice note** from the family's phone: «بيي بدو يعمل عملية فتق، الوزارة بتغطيها؟»
   - Wasel asks whether he has other cover. Reply «هو لبناني وما معو ولا ضمان ولا تأمين».
   - Wasel answers with the official page and offers to file the request. Reply «إيه بليز قدملنا ياها».
2. **Photos.** Send the medical report and the NSSF statement, then «اسمو علي حداد، العملية بمستشفى رفيق الحريري الجامعي، وأنا ابنو. ما عندو أي جهة ضامنة تانية.»
   - Wasel says the **إخراج قيد** is missing. Send it.
   - Wasel shows a summary and asks to confirm. Reply «إيه قدّمو». You get **W-1042**.
3. **On the laptop**, W-1042 has appeared in the inbox: the filled form, the documents and "Checked by Wasel". Press **Approve**, and the family's phone buzzes within seconds.
4. **Hand the phone to a judge**, who can ask anything: a medicine price, hospitals in their area, a coverage rule.

Rehearse the whole story without a phone: `uv run python -m sandpit.eval.demo_flow --lang lb`.

## Second story: "send a photo of your bill"

For the 10-minute stage demo, or if a judge asks about hospitals charging extra. The prop is the fourth page of `specimens.html` (open `specimens.html#bill` to show it alone, or send `sandpit/demo/bill.png` in the web chat). Al Sindyan Governmental Hospital is fictional, so no real hospital is shown overcharging: the bills module knows it only as a demo hospital (`BILLS_DEMO=0` removes it).

1. Send the bill photo with «بدهن ياني إدفع هيدا قبل ما يطلّعو خيي، طبيعي؟»
   - The bill says Lebanese and uninsured, so Wasel usually answers straight away. If it asks about other cover, reply «لبناني، ما عندو ضمان ولا تأمين».
   - Wasel answers: 100% at a government hospital, not the 80% on the bill, with the 2 July 2026 statement; it mentions 1787 and offers to report it. Reply «إيه بلّغ».
2. Wasel confirms the name, date and amount from the bill, asks whether it was paid, and shows a summary. Confirm and you get **R-501**.
3. **On the laptop**, admin panel → Hospital Bills: R-501 with the bill and the rule Wasel applied. Press **Take it up with the hospital**; the phone buzzes. Show **By hospital** (the evidence for the 1 Oct joint follow-up) and **Rules Wasel applies**.

## Third story: forward a rumour

For the 10-minute stage demo, or if a judge asks about fake news. On 2 July 2026 the ministry had to deny a rumour that its hospital cover had been limited to displaced people.

1. On the family's phone, put this in any chat (Message yourself works), then **forward** it to Wasel, so WhatsApp marks it Forwarded:
   «عاجل: وزارة الصحة وقّفت تغطية الطوارئ والاستشفاء للبنانيين يلي مش نازحين، التغطية صارت بس للنازحين. انشروها»
   - Wasel answers in 2–3 lines: not true, with the ministry's 2 July 2026 statement and its link (all uninsured Lebanese, displaced or not).
2. Forward two more: «وزارة الصحة صارت تغطي عمليات زرع الأعضاء على نفقتها» is confirmed by the 30 Sep 2026 announcement. «وزارة الصحة عم توزّع ١٠٠ دولار لكل عيلة عندها ولاد» isn't published anywhere, so Wasel says the ministry hasn't published it and points to 1214.
3. **On the laptop**, open **Ministry Info → Rumours**: each claim with its count, verdict, source and when it was first and last seen, newest first. Forward the first message again, or reword it, and its count goes up.

In the web chat, paste the message with «وصلني هيدا، صحيح؟». Wasel treats it like a forwarded message; only WhatsApp adds the `[forwarded]` tag. Rehearse with `uv run python -m sandpit.eval.run --only rumour_july_lb,rumour_transplant_en,rumour_invented_lb`.

Don't claim that NSSF ended any hospital contracts: Wasel sends that to the NSSF and names no hospital.

## If something breaks

- **WhatsApp is down:** use the web chat. Photos there are typed as `[photo <url>] <what the document is>`.
- **A reply is slow:** search replies take 5–10 seconds, so keep talking over it.
- **Starting over:** run the reset (step 2), and press New chat in the web chat.
- **Facts not to claim:** that hernia specifically is covered (the data never names it), or that 1787 is the general complaints line (that's 1214; 1787 is only for patients charged differences, per the 14 Mar 2026 circular).
