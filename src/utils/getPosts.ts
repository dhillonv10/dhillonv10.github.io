import { getCollection, type CollectionEntry } from "astro:content";
import postDates from "../data/post-dates.json";

const dates = postDates as Record<string, string>;

// Like getCollection("blog"), but each post's pubDatetime is the time of the git commit
// that first added the post (see scripts/post-dates.mjs). Posts missing from that file
// keep the pubDatetime from their frontmatter.
const getPosts = async (
  filter?: (entry: CollectionEntry<"blog">) => boolean
): Promise<CollectionEntry<"blog">[]> => {
  const posts = await getCollection("blog", filter);
  return posts.map(post => {
    const committed = dates[post.id];
    if (!committed) return post;
    return {
      ...post,
      data: {
        ...post.data,
        // frontmatter date, kept only to order posts that share a commit
        listedAt: post.data.pubDatetime,
        pubDatetime: new Date(committed),
      },
    };
  });
};

export default getPosts;
