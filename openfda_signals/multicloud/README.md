# openFDA multicloud portability slice (Bullet 6)

Proves one shared contract reconciles across **GCP BigQuery · Microsoft Fabric (OneLake) · AWS
(S3 + DynamoDB)** — not by copying a platform three times, but by validating that the same
record counts, business metrics, and contract-column schema survive each cloud-native load.

## Files
- `aws_portability.py` — land openFDA in S3 (typed parquet) + serve from DynamoDB (PAY_PER_REQUEST); `--teardown` to remove.
- `reconcile_3cloud.py` — read each cloud's ACTUAL schema (BQ / OneLake Delta / S3 Parquet), validate the
  contract columns present + correctly typed, fingerprint the projection, reconcile business metrics.
- `terraform/main.tf` — the AWS slice as IaC (S3 + DynamoDB, 30-day expiry). Validate in CI (`terraform validate`); this env has no terraform binary.
- `openfda_fact_contract_v1.0.0.json` — the canonical contract (read from file, not hardcoded).

## Run (creds: GCP SA + Fabric `az login` owner + AWS `~/.aws` default profile)
```bash
pip install -r ../requirements.txt
GCP_PROJECT_ID=<proj> AWS_REGION=us-east-1 python3 aws_portability.py     # S3 + DynamoDB
python3 reconcile_3cloud.py                                              # actual-schema + metric reconcile
```
Fabric OneLake reads require an interactive owner `az login`; run the Fabric leg where that token is available.

## Honest scope
The slice carries a **6-column projection** of the 9-column canonical contract. Those 6 columns are
present + identically typed across all three clouds (validated against the contract file); Fabric
additionally carries a benign `received_date` column (reported, not hidden). Cost < $0.0001, teardown documented.
