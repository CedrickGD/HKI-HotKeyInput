/**
 * Tiny strftime-style formatter that matches the subset the Rust backend
 * resolves via chrono. Used for live previews in the Settings dialog so
 * the user can see what a pattern will produce without round-tripping
 * through the backend.
 *
 * Supported tokens: %d %m %Y %y %H %I %M %S %p %A %a %B %b %e %j %%
 */

const DAY_NAMES = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
];

const DAY_NAMES_SHORT = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

const MONTH_NAMES = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

const MONTH_NAMES_SHORT = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

function pad2(n: number): string {
  return n < 10 ? `0${n}` : `${n}`;
}

function pad3(n: number): string {
  if (n < 10) return `00${n}`;
  if (n < 100) return `0${n}`;
  return `${n}`;
}

function dayOfYear(date: Date): number {
  const start = new Date(date.getFullYear(), 0, 0);
  const diff = date.getTime() - start.getTime();
  return Math.floor(diff / 86_400_000);
}

export function formatStrftime(pattern: string, date: Date = new Date()): string {
  let out = "";
  for (let i = 0; i < pattern.length; i += 1) {
    const ch = pattern[i];
    if (ch !== "%" || i === pattern.length - 1) {
      out += ch;
      continue;
    }
    const next = pattern[i + 1];
    i += 1;
    switch (next) {
      case "d":
        out += pad2(date.getDate());
        break;
      case "e":
        out += `${date.getDate()}`.padStart(2, " ");
        break;
      case "m":
        out += pad2(date.getMonth() + 1);
        break;
      case "Y":
        out += `${date.getFullYear()}`;
        break;
      case "y":
        out += pad2(date.getFullYear() % 100);
        break;
      case "H":
        out += pad2(date.getHours());
        break;
      case "I": {
        const h = date.getHours() % 12;
        out += pad2(h === 0 ? 12 : h);
        break;
      }
      case "M":
        out += pad2(date.getMinutes());
        break;
      case "S":
        out += pad2(date.getSeconds());
        break;
      case "p":
        out += date.getHours() < 12 ? "AM" : "PM";
        break;
      case "A":
        out += DAY_NAMES[date.getDay()];
        break;
      case "a":
        out += DAY_NAMES_SHORT[date.getDay()];
        break;
      case "B":
        out += MONTH_NAMES[date.getMonth()];
        break;
      case "b":
        out += MONTH_NAMES_SHORT[date.getMonth()];
        break;
      case "j":
        out += pad3(dayOfYear(date));
        break;
      case "%":
        out += "%";
        break;
      default:
        out += `%${next}`;
        break;
    }
  }
  return out;
}

/**
 * Formats an ISO-8601 timestamp into a coarse "2h ago" style string.
 * Falls back to a date/time render once the delta crosses a week.
 */
export function formatRelativeTime(iso: string, now: Date = new Date()): string {
  const then = new Date(iso);
  const ms = now.getTime() - then.getTime();
  if (Number.isNaN(ms)) return iso;
  const seconds = Math.floor(ms / 1000);
  if (seconds < 30) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return then.toLocaleDateString();
}
