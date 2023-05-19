## Dependencies
1. Oracle database (COLIN data load)
2. Postgres database (LEAR data load)
3. Solr connection (sending data to here)

## Development Setup
1. run `make setup`
2. create your .env based on .env.sample
3. `. .venv/bin/activate`
4. run the importer
  - `./run.sh` OR
  - `python data_import_handler.py`

## Data information
*Notes on the data being pulled from COLIN and LEAR.*
### COLIN
Party types being pulled:
```
Code Description                   
---- ------------------------------------------------------------------
DIR  Director
FIO  Firm Individual Owner (Firm Owner / proprietor / partner)
FBO  Firm Business Owner (Firm Owner / proprietor / partner)
INC  Incorporator
OFF  Officer
ATT  Attorney

APP  Applicant
FCP  Firm Completing Party
LIQ  Liquidator
MGR  Manager
SOL  Solicitor
OTH  Other
RCM  Receiver Mgr (Receiver or Receiver Manager)
RCC  Rec Custodian (Person Having Custody Of Dissolved Company Records)
PSA  Partner Sign Auth (New West Partner signing authority no address info)
PDI  Partner DIRECTOR (New West Partner director for BN)
PAS  Partner ATT SK (New West Partner Saskatchewan only attorney)
TAP  TILMA Primary Attorney
TAA  TILMA Alternate Attorney
TSP  TILMA Submitting Party
RAD  Partner Reinstatement Applicant - Director of foreign entity (NWPTA)
RAO  Partner Reinstatement Applicant - Office of foreign entity (NWPTA)
RAS  Partner Reinstatement Applicant - Shareholder of foreign entity (NWPTA)
RAF  Partner Reinstatement Applicant - Foreign Entity Reinstated (NWPTA)
```
