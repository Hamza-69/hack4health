# Hospital Bills (`bills`)

"Send a photo of your bill." A patient or a relative sends the hospital bill on WhatsApp. Wasel says what the ministry's rule is at that hospital for that patient, with the source and its date. If the patient is covered in full and was charged anyway, it files a report with the hospital, date, amount and bill photo. The ministry's Hospitals Service decides on each report, and the reports add up per hospital: evidence for the joint follow-up the ministry agreed with the Hospitals Syndicate on 1 Oct 2026.

It never judges items or prices on a bill (hospital prices aren't public) and never accuses anyone: a person at the ministry decides.

## Why

The ministry kept repeating the same warning (14 Mar, 20 Mar, 6 Sep, 1 Oct 2026) because a violation is only caught if a patient phones 1787 from the billing desk, knowing what they are owed. The rule kept changing: 80% at government hospitals normally, 100% for people displaced from border villages (Jan), 100% for all uninsured Lebanese during the war (Mar), then 100% at government hospitals and listed private ones (Jul). And a phone call leaves no record the ministry can act on.

## Where it sits

| The patient… | Module | Tools |
|---|---|---|
| asks what the ministry covers in general | `moph` | `search_ministry_site`, `search_services` |
| applies for a service (hospitalisation, IVIG…) | `requests` | `submit_request`, `request_status` (W-numbers) |
| was charged at a hospital while covered | `bills` | `check_bill`, `report_charge`, `add_to_report` (R-numbers) |

Report status needs no tool of its own: the agent's prompt already lists the user's open tickets, and the desk's decisions arrive as `[supplier · bills · ticket …]` messages.

## The rules

`app/cover.json` is the ministry's own statements, each with its date and link, and the list of 33 government and 44 private hospitals that must give 100% cover (circular 26/1/8685 of 14 Mar 2026, the newest list published; the 2 Jul statement mentions an updated list that is not on the site). `app/cover.py` picks the rule:

| Patient | Hospital | Verdict |
|---|---|---|
| wounded in the port explosion | government, or the private one already treating them | `no_extra_charge` (13 Aug 2026) |
| wounded in the war | any | `no_extra_charge` (3 Mar 2026) |
| NSSF, cooperative, army/security, insurance | any | `not_ministry`: their payer's rules apply |
| not Lebanese | any | `cannot_confirm`: point to 1787 |
| uninsured Lebanese | government, or private on the list | `no_extra_charge`, for all emergencies and the cases the ministry covers (2 Jul 2026) |
| uninsured Lebanese | private, not on the list | `usual_share`: ministry pays 65%, patient the rest |

`report_charge` re-runs the check and refuses anything but `no_extra_charge`, so the agent can't file a report the rule doesn't support.

Hospital names from bills are matched to the list and the ministry's Facility Locator (`sandpit/data/structured/facilities_clean.csv`, or `MOPH_DATA_DIR`). When a name could mean two hospitals ("اهدن" is a government and a private hospital), the tool returns both and the agent asks.

When the ministry publishes a new circular: add it to `sources` and `timeline` in `cover.json`, update the hospital list if it has one, and change `rule()` if the rule itself changed.

## Admin page

- **Reports**: the queue; each report shows the rule Wasel applied with its sources, the bill, and Take it up with the hospital / Ask for more / Close. The patient hears back in seconds.
- **By hospital**: reports, open and taken-up counts and amounts per hospital.
- **Rules Wasel applies**: the timeline and the hospital list, so the desk can see exactly what patients are told.

## Tests

```bash
cd modules/bills && uv run pytest
```
