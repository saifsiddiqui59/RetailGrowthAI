// Offline Part 2 publishing examples, tailored to a user-supplied reference showing three shirts.
// This repository does NOT store that image, claim ownership of trademarks or create media.
// Text is an illustrative example; real AI campaigns run in Part 1 with authenticated media.
export const SOCIAL_PUBLISHING_SAMPLES = Object.freeze([
  {
    "id": "linkedin-text",
    "provider": "linkedin",
    "name": "LinkedIn",
    "mediaKind": "text",
    "channel": "Member text post",
    "title": "A small collection, three distinct ways to dress",
    "copy": "A well-chosen shirt can refresh an everyday wardrobe.\n\nOur demo shirt collection highlights three moods: a crisp black shirt with a contrasting light collar, a soft yellow shirt with a deep green collar, and a rich forest-green shirt with dark detailing.\n\nFor retailers, clear product photography and honest color descriptions help customers compare styles confidently. Which color would you start with?\n\n#Menswear #RetailStyle #SmallBusiness",
    "schedule": "Draft only · sample Asia/Kolkata schedule",
    "required": [
      "LinkedIn member OAuth + verified w_member_social permission",
      "Business-owner review of exact text, schedule, and publish quota",
      "Versioned Posts API response and confirmed remote post ID"
    ],
    "adapter": "LinkedIn versioned REST Posts API",
    "warning": "This is an educational text sample, not an affiliated endorsement or a verified inventory listing."
  },
  {
    "id": "facebook-text",
    "provider": "facebook",
    "name": "Facebook",
    "mediaKind": "text",
    "channel": "Page feed text post",
    "title": "Three shirt colors, three different moods",
    "copy": "What is your go-to shirt color?\n\n🖤 Black with a light contrast collar\n💛 Soft yellow with a dark-green collar\n💚 Forest green with dark accents\n\nThese are visual ideas for our sample menswear campaign—not a live product offer. Tell us which one matches your style.\n\n#ShirtStyle #Menswear",
    "schedule": "Draft only · sample Asia/Kolkata schedule",
    "required": [
      "Verified shop-owned Facebook Page access and Page publishing permission",
      "Explicit owner review, publishing quota and approved copy",
      "Page feed API confirmation plus remote receipt reconciliation"
    ],
    "adapter": "Meta Page feed publishing API",
    "warning": "Facebook Page text only. No personal profile posting, prices or unapproved sales claims."
  },
  {
    "id": "instagram-reel",
    "provider": "instagram",
    "name": "Instagram",
    "mediaKind": "video",
    "channel": "Professional account Reel",
    "title": "3 shirt colors in 30 seconds",
    "copy": "Which shirt is your mood today? 🖤💛💚\n\nBlack and cream • pale yellow and forest green • deep green and black.\n\nA 30-second product styling concept for our demo menswear brand.\n\n#ShirtStyle #Menswear #ReelIdeas",
    "schedule": "Draft only · sample Asia/Kolkata schedule",
    "required": [
      "Professional Instagram account with verified Page and publishing grant",
      "Rights-approved tenant-owned 9:16 MP4 from the existing RetailGrowthAI FFmpeg renderer",
      "Container creation, verified FINISHED status, media_publish and confirmed receipt"
    ],
    "adapter": "Instagram Reels container → status → media_publish",
    "warning": "Product-photo-inspired storyboard only; no MP4 or customer image has been uploaded or generated.",
    "media": {
      "kind": "video",
      "aspectRatio": "9:16",
      "durationSeconds": 30,
      "source": "Approved Part 1 private render (not provided in this sample)"
    }
  },
  {
    "id": "youtube-short",
    "provider": "youtube",
    "name": "YouTube",
    "mediaKind": "video",
    "channel": "Portrait video upload / Shorts candidate",
    "title": "3 Classic Shirt Colors | 30-Second Style Guide",
    "copy": "Explore three shirt styling directions from our demo collection: black with a light collar, soft yellow with deep green trim, and forest green with dark details.\n\nVisual product concepts only; no price, stock claim or brand endorsement.\n\n#Shorts #Menswear #StyleGuide",
    "schedule": "Draft only · sample Asia/Kolkata schedule",
    "required": [
      "Verified channel consent and required YouTube upload permission",
      "Owner-reviewed and commercially cleared portrait MP4 supplied by RetailGrowthAI media workflow",
      "Completed resumable binary upload, remote video ID and visibility check"
    ],
    "adapter": "YouTube videos.insert resumable upload",
    "warning": "Sample defaults to private visibility. No MP4 attached; YouTube decides Shorts classification.",
    "media": {
      "kind": "video",
      "aspectRatio": "9:16",
      "durationSeconds": 30,
      "source": "Approved Part 1 private render (not provided in this sample)"
    }
  }
])
