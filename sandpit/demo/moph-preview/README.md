# Wasel on the real moph.gov.lb

A Chrome extension for the demo. On https://www.moph.gov.lb it adds, in this browser only:

- the line the ministry would add to its pages: `<script src=".../widget.js">`, so Wasel's button sits in the corner of every page, in Arabic or English;
- on each service page, an **اسأل واصل عن هذه المعاملة / Ask Wasel about this service** button under the title, which opens Wasel on that service (a `data-wasel-ask` attribute, no script);
- a bar at the top saying it is a preview added in this browser, and that the ministry's site itself is unchanged.

Nothing is sent to or changed on the ministry's servers. Their site sends no Content-Security-Policy or X-Frame-Options, so the widget runs there exactly as it would once installed.

## Set up (before the demo, once)

1. Chrome › `chrome://extensions` › turn on **Developer mode** › **Load unpacked** › pick this folder.
2. Run Wasel: `uv run h4h dev` from the repo root.
3. Open https://www.moph.gov.lb/ar/AdministrativeServices/details/84. Chrome asks whether **www.moph.gov.lb** may access devices on your local network: press **Allow**. The real site is reaching Wasel on this laptop (`localhost`), which Chrome guards since 2025. It remembers the answer, so do this before the demo, not in front of the judges.
4. Press **اسأل واصل عن هذه المعاملة** and check that Wasel answers.

No prompt at all: run Wasel on a public https address (the Fly deploy, or a tunnel to `localhost:9000`), put that address in `WASEL` at the top of `preview.js`, and press the reload icon on the extension's card.

## Present

1. Open the hospitalisation page above (Arabic), or `/en/AdministrativeServices/details/84` (English).
2. Say: "This is the ministry's real website. We added Wasel in this browser only, with the one line your webmaster would add. Nothing on your servers changed."
3. Press **Ask Wasel about this service**: Wasel opens on that service, answers with the official page and offers to prepare the request.
4. Click to any other page of the site: the Wasel button is on every one.

If the venue's network or the permission gets in the way, use the preview on Wasel's landing page (http://localhost:9000, section **One line on the ministry's website**).

## Notes

- Chrome only. Safari blocks an https page from loading `http://localhost`.
- Turn the extension off on its card to see the site as it is.
