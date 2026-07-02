import json

with open("reddit_data.json") as f:
    posts = json.load(f)

# Group by subreddit
by_sub = {}
for post in posts:
    sub = post.get("communityName", "unknown")
    if sub not in by_sub:
        by_sub[sub] = []
    by_sub[sub].append(post)

# Print top 5 for each subreddit sorted by ups (or num_comments if ups is missing)
for sub, sub_posts in by_sub.items():
    print(f"\n================ r/{sub} ================")
    sorted_posts = sorted(sub_posts, key=lambda x: x.get("ups", 0) or x.get("num_comments", 0) or 0, reverse=True)
    for i, post in enumerate(sorted_posts[:5]):
        print(f"{i+1}. {post['title']} (Upvotes: {post.get('ups')}, Comments: {post.get('num_comments')})")
        print(f"   URL: {post['url']}")
        text = post.get("selftext", "")
        if text:
            print(f"   Snippet: {text[:200]}...")
        if post.get("image_url"):
            print(f"   Image: {post['image_url']}")
        print()
