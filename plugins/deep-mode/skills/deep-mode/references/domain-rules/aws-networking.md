# AWS networking and cloud

Read when designing, changing, or debugging AWS infrastructure: VPCs, subnets, routing, gateways, firewalls, DNS, load balancers, cross-network links, IAM, cost, or picking an AWS service. Almost all of it is from AWS-NET; other source keys are marked. Keys are in `README.md`.

## Debug a connection (do this first on any "can't connect")

Follow the packet. Check in this order and stop at the first failure:

1. **Path and address.** The destination IP or name exists and resolves.
2. **Routes.** The source subnet's route table has a route to the destination, and the destination has a **return route** back. Peering failures are usually a missing return route.
3. **Security groups.** Ingress on the target, egress on the source.
4. **Network ACLs.** Both directions, including the ephemeral return ports.

Then read VPC Flow Logs for the interface:

| Flow log shows | Meaning | Look at |
|---|---|---|
| No record | Packet never reached the interface | Routing or addressing |
| `REJECT` | Arrived and was blocked | Security group or NACL |
| `ACCEPT` but the client times out | The network is fine | The host: service down, wrong port, or bound to `localhost` only |

Pair Flow Logs with CloudTrail, which records who changed a security group, route, or gateway and when.

## VPC and CIDR

- A VPC lives in one region and spans all of its Availability Zones.
- Take VPC ranges from RFC 1918 private space only: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.
- Size by prefix: /16 gives 65,536 addresses, /24 gives 256.
- AWS keeps 5 addresses in every subnet (the first four and the last), so a /24 has 251 usable.
- Never overlap CIDRs between VPCs, or between a VPC and on-premises. Overlapping ranges cannot be routed between, and fixing them later means renumbering. Plan the address map before the first VPC.
- Load balancers take private IPs in at least two AZs' subnets. Size subnets with room for them.

## Subnets and route tables

- Each subnet sits in exactly one AZ. Subnets are how you spread work across failure domains.
- "Public" is not a setting. A subnet is public only when its route table sends `0.0.0.0/0` to an Internet Gateway. Without that route it is private, even if an instance holds a public IP.
- Every route table has a local route for the VPC CIDR (for example `10.0.0.0/16 → local`). It cannot be deleted and lets all subnets talk.
- Create dedicated route tables and associate each subnet explicitly. Implicit fallback to the main table causes drift.
- Longest prefix wins. A specific route (local VPC, peering) beats `0.0.0.0/0`.
- Deleting or detaching a route's target (NAT gateway, peering link) leaves the entry as a **blackhole** route that silently drops matching traffic. Check for blackholes after any teardown.

## Internet access

- An instance is reachable from the IPv4 internet only when all four hold: an Internet Gateway is attached to the VPC, the subnet routes `0.0.0.0/0` to it, the instance has a public IPv4 or Elastic IP, and a security group allows the inbound port.
- A NAT Gateway gives private subnets outbound-only access (patches, external APIs). Put it in a public subnet with an Elastic IP.
- A NAT Gateway is zonal. Run one per AZ, each with its own private route table, or one AZ failure cuts egress for all.
- A self-managed NAT instance needs its interface's source/destination check disabled, or it drops forwarded traffic.
- IPv6 needs no translation. Use an Egress-Only Internet Gateway for outbound-only `::/0`.

## Security groups vs network ACLs

| | Security group | Network ACL |
|---|---|---|
| Attached to | Network interface (instance level) | Subnet boundary, checked first |
| State | Stateful: replies allowed automatically | Stateless: both directions need rules |
| Rules | Allow only; default deny; multiple groups union | Allow and deny; numbered, lowest first, first match wins; implicit final deny |
| Return traffic | Automatic | Outbound must allow ephemeral ports 1024–65535 |

- Write security group rules against other group IDs, not IPs. Example: the app group admits only the load balancer group, so new instances are covered without editing IP lists.

## DNS

- The VPC resolver is at the VPC base address plus two (`10.0.0.2` for `10.0.0.0/16`) and at `169.254.169.253` in every VPC.
- Private hostnames need both `enableDnsSupport` and `enableDnsHostnames` set to true.
- A Route 53 private hosted zone resolves only in VPCs explicitly associated with it.
- Before a DNS cutover, lower the record TTL and wait one old TTL. Raise it again afterward.
- Route 53 steers globally (latency, health-check failover, weighted) before traffic reaches a VPC or load balancer. (TOP10-AWS)

## Load balancers

- ALB is layer 7: routes HTTP/HTTPS by path or host header.
- NLB is layer 4: raw TCP/UDP, very high throughput, very low latency.
- Health checks pull failing targets out of rotation automatically.
- An internal load balancer with private IPs, in private subnets, balances between backend services without internet exposure.

## Connecting networks

- **VPC peering** is one-to-one and not transitive. A cannot reach C through B. Each pair needs its own peering plus routes on both sides. A full mesh of N VPCs needs N(N−1)/2 links (10 VPCs need 45). Past a handful, use Transit Gateway.
- **Transit Gateway** is a hub that attaches VPCs, VPNs, and Direct Connect, with one attachment interface per AZ. It routes transitively. Separate environments with multiple TGW route tables.
- **Gateway endpoints** cover S3 and DynamoDB only. They are free and add prefix-list routes so that traffic skips the NAT Gateway.
- **Interface endpoints (PrivateLink)** put an ENI with a private IP in your subnets for nearly every other AWS or partner service. They are billed hourly plus per GB.
- To share your own service privately, put it behind an NLB, publish an endpoint service, and consumers connect through PrivateLink with no peering or route exchange.
- Restrict endpoints with endpoint policies, for example only specific S3 buckets.
- **Site-to-Site VPN**: IPsec from an on-premises customer gateway to a Virtual Private Gateway or Transit Gateway. It always provisions two tunnels; configure both.
- **Direct Connect**: dedicated physical circuit for steady latency and high throughput. Keep a VPN as automatic backup.
- **Client VPN** gives individual remote users subnet access under authorization rules. For a shell on one instance, use Systems Manager Session Manager and open no inbound SSH.

## Three-tier reference architecture

- VPC `10.0.0.0/16` across 2 AZs with 6 subnets: 2 public (ALB, NAT Gateways), 2 private app, 2 private database.
- 4 route tables: 1 public (`0.0.0.0/0 → IGW`), 2 private app (each `0.0.0.0/0 →` its own AZ's NAT), 1 database with local routes only. The database has no path to the internet.
- 3 security groups: ALB admits 443 from the internet; app admits only the ALB group; database admits only the app group on the database port.
- When one AZ fails, the ALB drops the dead targets, app instances in the healthy AZ egress through their own NAT, and the database fails over to its standby replica.

## Cost traps

- Every public IPv4 address bills hourly, including unattached Elastic IPs. Release idle ones.
- NAT Gateways bill per hour plus per GB processed. Large S3 or internal AWS traffic through NAT is a classic surprise bill. Move it to gateway endpoints.
- Inbound data to AWS is free. Outbound to the internet, cross-AZ, and inter-region transfer all cost. (AWS-SENSE)
- A stopped EC2 instance stops compute billing, but its EBS volumes keep billing until deleted. (AWS-SENSE)
- On day one, create AWS Budgets alerts (for example at 85% and 100%). Tear down experiments before weekends. (AWS-SENSE)

## IAM and security

- Do not use the root user for daily work. Give it a strong password and MFA, then work through least-privilege IAM users or roles. (AWS-SENSE)
- Split network power: developers can read networks and attach security groups; only the platform team can edit route tables, create gateways, or delete VPCs.
- Shared responsibility: AWS secures the physical facilities, virtualization, and hardware. You secure IAM, OS patching, encryption, and firewall rules. (AWS-SENSE)

## Picking a service

| Need | Service |
|---|---|
| Full OS control, custom kernel or tuning, legacy monolith | EC2 (TOP10-AWS) |
| Run code on events (S3 upload, API call, queue message) with no servers | Lambda (TOP10-AWS) |
| Containers: simple and AWS-native | ECS (CLOUD-10) |
| Containers: complex orchestration or multi-cloud | EKS (CLOUD-10) |
| Static assets, backups, logs, data lake, large files | S3 (TOP10-AWS) |
| Relational, transactional, ACID (Postgres, MySQL, SQL Server, Oracle) | RDS (DB-LAWS) |
| Key-value or document at single-digit-ms latency, huge scale (sessions, carts, leaderboards) | DynamoDB (TOP10-AWS) |
| Decouple services and absorb spikes | SQS (TOP10-AWS) |
| Cache static content at the edge in front of S3 or an ALB | CloudFront (TOP10-AWS) |
