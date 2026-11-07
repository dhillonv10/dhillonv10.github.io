import { SITE } from "@config";

const formatDate = (d: string | Date, opts?: Intl.DateTimeFormatOptions) =>
  new Date(d).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: SITE.timeZone,
    ...opts,
  });

export default formatDate;
