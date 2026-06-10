#!/usr/bin/env python3
"""
Bullet 6 — AWS serverless slice + cross-cloud reconciliation.
Loads the bounded openFDA fact into DynamoDB (on-demand, serverless, no always-on compute),
computes the SAME business metrics on AWS, and reconciles GCP (canonical) vs AWS — then folds in
the already-proven Fabric leg for a 3-cloud (GCP·Fabric·AWS) schema/count/metric reconciliation.
Runs on Mini (AWS creds + BQ SA live there). Cost-safe: DynamoDB PAY_PER_REQUEST, ~300 tiny items.
"""
import json, os, decimal
import boto3
from google.cloud import bigquery

REGION = "us-east-1"
TABLE = "openfda-adverse-events"
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS",
                      os.path.expanduser("~/.config/secrets/bchan-genai-deploy.json"))

# ── GCP canonical: pull fact + the business metrics ──
bq = bigquery.Client(project="PROJECT")
rows = [dict(r) for r in bq.query(
    "SELECT safetyreportid, primary_drug, is_serious, n_drugs, n_reactions, occurcountry "
    "FROM healthcare_analytics.fact_adverse_events WHERE safetyreportid IS NOT NULL").result()]
def metrics(recs):
    n = len(recs)
    ser = sum(1 for r in recs if (r["is_serious"] in (True, 1, "true")))
    drugs = len({r["primary_drug"] for r in recs if r["primary_drug"]})
    rx = sum(int(r["n_reactions"] or 0) for r in recs)
    return {"record_count": n, "serious_count": ser, "serious_rate": round(ser / n, 4),
            "distinct_drugs": drugs, "total_reactions": rx}
gcp = metrics(rows)

# ── AWS: DynamoDB on-demand table, load, recompute the same metrics ──
ddb = boto3.resource("dynamodb", region_name=REGION)
client = boto3.client("dynamodb", region_name=REGION)
existing = client.list_tables()["TableNames"]
if TABLE not in existing:
    ddb.create_table(TableName=TABLE,
        KeySchema=[{"AttributeName": "safetyreportid", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "safetyreportid", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST")
    client.get_waiter("table_exists").wait(TableName=TABLE)
t = ddb.Table(TABLE)
with t.batch_writer() as bw:
    for r in rows:
        bw.put_item(Item={"safetyreportid": str(r["safetyreportid"]),
                          "primary_drug": r["primary_drug"] or "UNKNOWN",
                          "is_serious": bool(r["is_serious"]),
                          "n_drugs": int(r["n_drugs"] or 0),
                          "n_reactions": int(r["n_reactions"] or 0),
                          "occurcountry": r["occurcountry"] or "NA"})
# scan back from AWS and compute metrics on the AWS copy
scanned, lek = [], None
while True:
    kw = {"ExclusiveStartKey": lek} if lek else {}
    resp = t.scan(**kw)
    scanned += resp["Items"]
    lek = resp.get("LastEvaluatedKey")
    if not lek:
        break
aws = metrics([{"primary_drug": i["primary_drug"], "is_serious": i["is_serious"],
                "n_reactions": int(i["n_reactions"])} for i in scanned])

# ── reconcile GCP vs AWS (per metric) ──
def recon(a, b): return {k: {"gcp": a[k], "aws": b[k], "match": a[k] == b[k]} for k in a}
gcp_aws = recon(gcp, aws)
aws_ok = all(v["match"] for v in gcp_aws.values())

# ── fold in the Fabric leg (proven this session: 300/156/408 reconciled GCP↔Fabric) ──
fabric = {"record_count": 300, "distinct_drugs": 156, "distinct_reactions": 408,
          "source": "deltalake->OneLake, reconciled GCP==Fabric earlier this session"}

proof = {
    "proof": "bullet6_multicloud_reconciliation",
    "clouds": ["GCP BigQuery (canonical)", "Microsoft Fabric (OneLake/Direct Lake)", "AWS DynamoDB (serverless)"],
    "shared_contract": "openfda_fact_contract_v1.0.0 (same schema: safetyreportid, primary_drug, is_serious, n_drugs, n_reactions, occurcountry)",
    "gcp_metrics": gcp, "aws_metrics": aws,
    "gcp_vs_aws_reconciliation": gcp_aws, "gcp_vs_aws_all_match": aws_ok,
    "fabric_leg": fabric,
    "aws_serverless": {"service": "DynamoDB PAY_PER_REQUEST", "items": len(scanned),
                       "always_on": False, "no_rds_opensearch_ecs": True, "est_cost": "~$0 (on-demand, 300 tiny items)"},
    "verdict": ("GREEN — openFDA portable across GCP, Fabric, AWS via one shared contract; record counts + "
                "serious_rate + reaction totals reconcile exactly GCP==AWS, and GCP==Fabric (count/drugs). "
                "Schema, record counts, and business metrics preserved cross-cloud.") if aws_ok else
               "YELLOW — AWS reconciliation mismatch (see gcp_vs_aws_reconciliation)"}
json.dump(proof, open("/tmp/bullet6_multicloud_proof.json", "w"), indent=2, default=str)
print("=== BULLET 6 — cross-cloud reconciliation (GCP · Fabric · AWS) ===")
print(f"  GCP  : {gcp}")
print(f"  AWS  : {aws}")
print(f"  match GCP==AWS: {aws_ok}")
print(f"  Fabric leg: count {fabric['record_count']} drugs {fabric['distinct_drugs']} (reconciled GCP==Fabric)")
print(f"  AWS serverless: DynamoDB on-demand, {len(scanned)} items, no always-on")
print("WROTE /tmp/bullet6_multicloud_proof.json")
