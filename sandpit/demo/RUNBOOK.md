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

## If something breaks

- **WhatsApp is down:** use the web chat. Photos there are typed as `[photo <url>] <what the document is>`.
- **A reply is slow:** search replies take 5–10 seconds, so keep talking over it.
- **Starting over:** run the reset (step 2), and press New chat in the web chat.
- **Facts not to claim:** that hernia specifically is covered (the data never names it), or that 1787 is the complaints line (it's 1214).
