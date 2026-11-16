// Writes src/data/post-dates.json: for every post, the time of the commit that first added it.
// Falls back to the previous values when git history isn't available (for example a shallow clone),
// and the site falls back to the frontmatter `pubDatetime` for any post missing from the file.
import { execFileSync } from "node:child_process";
import { readdirSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const blogDir = join("src", "content", "blog");
const out = join(root, "src", "data", "post-dates.json");

const git = args =>
  execFileSync("git", args, { cwd: root, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();

export function updatePostDates() {
  let previous = {};
  try {
    previous = JSON.parse(readFileSync(out, "utf8"));
  } catch {}

  let shallow = true;
  try {
    shallow = git(["rev-parse", "--is-shallow-repository"]) === "true";
  } catch {
    shallow = null; // no git at all
  }

  const dates = { ...previous };
  if (shallow !== null) {
    const files = readdirSync(join(root, blogDir)).filter(f => /\.mdx?$/.test(f));
    for (const f of files) {
      // A shallow clone (what most hosts use) can't show when a file was first added, so only
      // posts that are not recorded yet are looked up, using the oldest commit it can see.
      if (shallow && dates[f]) continue;
      try {
        const lines = git([
          "log", "--diff-filter=A", "--follow", "--format=%aI", "--", join(blogDir, f),
        ]).split("\n").filter(Boolean);
        if (lines.length) dates[f] = new Date(lines[lines.length - 1]).toISOString();
      } catch {}
    }
    for (const f of Object.keys(dates)) {
      try { readFileSync(join(root, blogDir, f)); } catch { delete dates[f]; }
    }
  }

  const sorted = Object.fromEntries(Object.entries(dates).sort(([a], [b]) => a.localeCompare(b)));
  const text = JSON.stringify(sorted, null, 2) + "\n";
  mkdirSync(dirname(out), { recursive: true });
  let old = "";
  try { old = readFileSync(out, "utf8"); } catch {}
  if (old !== text) writeFileSync(out, text);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) updatePostDates();
