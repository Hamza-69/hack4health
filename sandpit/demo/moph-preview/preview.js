// Puts Wasel on the real moph.gov.lb, in this browser only, the way the ministry would: one script tag,
// plus an "Ask Wasel about this service" button under each service title. Nothing on the ministry's
// servers changes, and the bar at the top of the page says so.

// Where Wasel's site runs: this laptop (`uv run h4h dev`), or the deployed https address.
const WASEL = "http://localhost:9000/";

const lang = location.pathname.startsWith("/en") ? "en" : "ar";
const TEXT = {
  ar: {
    note: "معاينة: واصل مضاف على هذا المتصفح فقط، بسطر واحد. موقع الوزارة نفسه ما تغيّر.",
    ask: "اسأل واصل عن هذه المعاملة",
    question: (title) => `كيف بقدّم على «${title}»؟`,
  },
  en: {
    note: "Preview: Wasel is added in this browser only, with one line. The ministry's website itself is unchanged.",
    ask: "Ask Wasel about this service",
    question: (title) => `How do I apply for "${title}"?`,
  },
}[lang];

// 1. The one line the ministry would add to its pages.
const script = document.createElement("script");
script.src = new URL("widget.js", WASEL).href;
script.dataset.lang = lang;
document.head.append(script);

// 2. On a service page, the button a webmaster would add under the title. It needs no script of its
// own: the widget opens on the question in data-wasel-ask.
const title = document.querySelector(".asFormTitle");
if (title && location.pathname.includes("/AdministrativeServices/details/")) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "wasel-preview-ask";
  button.textContent = TEXT.ask;
  button.setAttribute("data-wasel-ask", TEXT.question(title.textContent.trim()));
  title.after(button);
}

// 3. Say on screen that this is a preview.
const note = document.createElement("div");
note.className = "wasel-preview-note";
note.textContent = TEXT.note;
document.body.prepend(note);
