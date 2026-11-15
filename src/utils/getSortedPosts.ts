import type { CollectionEntry } from "astro:content";
import postFilter from "./postFilter";

const getSortedPosts = (posts: CollectionEntry<"blog">[]) => {
  return posts.filter(postFilter).sort((a, b) => {
    const time = (p: CollectionEntry<"blog">) =>
      Math.floor(
        new Date(p.data.modDatetime ?? p.data.pubDatetime).getTime() / 1000
      );
    // posts added in the same commit: fall back to the frontmatter date
    const listed = (p: CollectionEntry<"blog">) =>
      new Date(
        (p.data as { listedAt?: Date }).listedAt ?? p.data.pubDatetime
      ).getTime();
    return time(b) - time(a) || listed(b) - listed(a);
  });
};

export default getSortedPosts;
