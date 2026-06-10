# Open Questions

## Q1: Where do snapshots live?

**Status:** open
**Why it matters:** This is the most consequential architecture decision. The storage backend determines: setup friction, whether a server component is needed, what "credentials" means, cost, offline behavior, and how snapshot discovery works. Almost everything else follows from this choice.
**Strategy:** thinking

The main options identified so far:
- **Shared object store (S3 or compatible)** — configure a bucket once, push/pull by name. Works remotely, costs something, requires AWS/cloud credentials distributed to the team.
- **Shared NAS or internal server** — simpler if office-based/VPN; brittle for remote work.
- **Git LFS or blob store backed by git** — named and versioned naturally, but dumps can be large and git isn't designed for binary blobs of this size.
- **Custom backend (the tool owns the server)** — maximum control, but means building and hosting a server component.

Not yet discussed: whether S3-compatible self-hosted options (MinIO, Cloudflare R2) are in scope, or whether the team already has an AWS account that makes S3 the natural default.

## Q2: Restore semantics

**Status:** open
**Why it matters:** Determines what `snap pull` actually does and how safe it is. Replace the whole DB? Create a new DB alongside? What happens if local migrations are ahead of the snapshot's schema?
**Strategy:** thinking

Not yet discussed. At minimum the tool should not leave a broken DB on failure (already in requirements as a reliability constraint).
