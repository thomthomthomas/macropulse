// Source: federalreserve.gov/monetarypolicy/fomccalendars.htm
// Update once a year. Dates are tentative until confirmed at the prior meeting.
export const fomcMeetings = [
  { start: "2026-10-27", end: "2026-10-28" },
  { start: "2026-12-08", end: "2026-12-09" },
  // TODO: add 2027 dates from the Fed calendar
];

export function nextFomc(today = new Date()) {
  const t = today.toISOString().slice(0, 10);
  return fomcMeetings.find((m) => m.end >= t) ?? null;
}
