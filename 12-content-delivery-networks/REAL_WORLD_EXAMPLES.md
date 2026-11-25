# Real-World Case Studies: Content Delivery Networks

> ✅ **Source-checked.** Each deep dive names its source, and we kept only what that source says. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

> Two ways to get content close to users: put servers inside the ISP (Netflix Open Connect, Google Global Cache), or run a large edge network and layer caches inside it (Cloudflare).

---

## 🎬 Deep Dive 1: Netflix Open Connect, Appliances Inside ISPs

> **Source:** Netflix's [Open Connect site](https://openconnect.netflix.com/en/), including its [appliances](https://openconnect.netflix.com/en/appliances/) and [peering](https://openconnect.netflix.com/en/peering/) pages. Everything in this section comes from those pages.

- **Free appliances for ISPs.** Open Connect Appliances (OCAs) "are provided to qualifying ISP partners at no charge". The ISP supplies "a small amount of data center rack space, power, and connectivity", and Netflix handles setup and monitoring. Netflix says it partners "with over a thousand ISPs".
- **Two ways to connect.** Appliances "can be embedded in your ISP network", or the ISP can peer with Netflix at internet exchange points, where traffic comes "from Netflix appliances that are located in local IXPs".
- **Content arrives ahead of demand.** Netflix "pre-fills them with the appropriate content for your geographical location", and the ISP enables "nightly content fills and updates".
- **What's inside.** OCAs "are based on commodity PC components, assembled in custom cases". They run FreeBSD and the NGINX web server. A storage appliance delivers about 200 Gbps with up to 120 TB of storage. A lower-cost global appliance delivers about 80 Gbps with up to 60 TB.

---

## 🌐 Deep Dive 2: Cloudflare, Tiered Caching and Smart Routing

> **Sources:** Cloudflare's [network page](https://www.cloudflare.com/network/), [Tiered Cache docs](https://developers.cloudflare.com/cache/how-to/tiered-cache/), [Argo Smart Routing docs](https://developers.cloudflare.com/argo-smart-routing/) and [Argo product page](https://www.cloudflare.com/application-services/products/argo-smart-routing/), read in November 2026. Everything in this section comes from those pages.

- **Size.** Cloudflare lists data centers in 348 cities in more than 100 countries, and says its network routes "an average of 115 million HTTP requests per second".
- **Tiered caching.** With Tiered Cache, "the lower-tier must ask an upper-tier to see if it has the content. If the upper-tier does not have the content, only the upper-tier can ask the origin for content." That shields the origin and raises cache hit ratios. Smart Tiered Cache "dynamically selects the single closest upper tier for each of your website's origins".
- **Routing around congestion.** For requests that must reach the origin, Argo Smart Routing "routes your web traffic across the most efficient network path, avoiding congestion", using real-time congestion data. Cloudflare's own figure is "30% (on average) faster web app performance".

---

## 🔍 Deep Dive 3: Google Global Cache, Google Content from Inside the ISP

> **Source:** Google's [Google Global Cache help page](https://support.google.com/interconnect/answer/9058809). Everything in this section comes from it.

- "Google Global Cache (GGC) allows ISPs to serve certain Google content from within their own networks."
- "Google provides the GGC hardware." The ISP provides rack space, power and a network connection.
- "Typically between 70-90% of cacheable traffic can be served from GGC."

---

> ℹ️ An earlier version of this page said Netflix delivers "15% of all downstream internet traffic" at "100+ Terabits per second", serves "95%+" of its traffic from OCAs, and "completely phased out" Akamai, Limelight and Level 3 in 2012. It also gave older Cloudflare figures. Netflix's Open Connect site doesn't state any of those, so we removed them and updated Cloudflare's numbers from its current pages.

## 🎯 System Design Interview Takeaways
1. **For large, predictable content, go inside the ISP.** Netflix and Google both place caches in ISP networks, so popular content never crosses the wider internet.
2. **Fill caches before demand.** Open Connect pre-fills appliances nightly, so peak-hour traffic is served from what's already there.
3. **Layer your caches.** Cloudflare's tiered caching means only an upper tier talks to the origin, so a miss at the edge doesn't always become an origin request.
4. **CDNs help uncacheable requests too.** Routing around congestion (Argo) speeds up requests that must reach the origin.
