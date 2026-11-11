import type { Site, SocialObjects } from "./types";

export const SITE: Site = {
  website: "https://opsbug.com/", // replace this with your deployed domain
  author: "Vik Dhillon",
  desc: "Personal Blog",
  title: "Vik Dhillon",
  ogImage: "astropaper-og.jpg",
  lightAndDarkMode: true,
  postPerPage: 3,
  scheduledPostMargin: 15 * 60 * 1000, // 15 minutes
};

export const GISCUS = {
  repo: "dhillonv10/dhillonv10.github.io",
  repoId: "R_kgDOMAmurA",
  category: "Blog Comments",
  categoryId: "DIC_kwDOMAmurM4DKyOA",
};

// Names of the two post lists on the home page. Tag a post in its frontmatter:
//   type: feature   -> listed under the first heading (your longer, featured pieces)
//   type: note      -> listed under the second (the default when `type` is omitted)
export const SECTIONS = {
  feature: "Machina ex Machina",
  note: "Brief Notes",
} as const;

export const LOCALE = {
  lang: "en", // html lang code. Set this empty and default will be "en"
  langTag: ["en-EN"], // BCP 47 Language Tags. Set this empty [] to use the environment default
} as const;

export const LOGO_IMAGE = {
  enable: false,
  svg: true,
  width: 216,
  height: 46,
};

export const SOCIALS: SocialObjects = [
  {
    name: "Github",
    href: "https://github.com/dhillonv10",
    linkTitle: ` ${SITE.title} on Github`,
    active: true,
  },
  {
    name: "Twitter",
    href: "https://twitter.com/opsbug",
    linkTitle: `${SITE.title} on Twitter`,
    active: true,
  },
];
