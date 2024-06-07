## Setup a new VM at gcp and give the correct access
Our case as example. We created `data-fetcher` VM and defined a static external ip to make it easier to work on the machine through `VSCode SSH-Remote`Extention.

Criar uma Nova Rede:
gcloud compute networks create data-fetcher --subnet-mode=custom

Criar uma Nova Sub-rede:
gcloud compute networks subnets create data-fetcher-subnet \
    --network=data-fetcher \
    --range=10.0.0.0/24 \
    --region=us-central1

`
gcloud compute instances create data-fetcher \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --network-interface=network=data-fetcher,subnet=data-fetcher-subnet
`

`gcloud compute addresses create data-fetcher --region us-central1 `
`gcloud compute addresses describe data-fetcher --region us-central1`

Get the generated external ip address at `address:`.

`gcloud compute instances stop data-fetcher --zone=us-central1-a`

`
gcloud compute instances add-access-config data-fetcher \
    --zone=us-central1-a \
    --access-config-name=external-nat \
    --address=IP_ADDRESS
`

`gcloud compute instances start data-fetcher --zone=us-central1-a`

Create a Firewall Rule for SSH (port 22)

`gcloud compute firewall-rules create allow-ssh \
    --direction=INGRESS \
    --priority=1000 \
    --network=data-fetcher \
    --action=ALLOW \
    --rules=tcp:22 \
    --source-ranges=0.0.0.0/0 \
    --description="Allow SSH from anywhere"
`

## VSCode SSH-Remote Extension
Step 1: Install the SSH Remote Extension
Open Visual Studio Code.
Go to the Extensions view by clicking on the Extensions icon in the Activity Bar on the side of the window or pressing Ctrl+Shift+X.
Search for "Remote - SSH".
Click Install on the "Remote - SSH" extension.

Step 2: Add SSH Key to Your VM
Generate an SSH key pair
ssh-keygen -t rsa -b 2048 -f ~/.ssh/gcp_web3dev_vm-data-fetcher

Add the public key to your VM:
Read the content of the public key:
cat ~/.ssh/gcp_web3dev_vm-data-fetcher.pub
Add the public key to your VM using the Google Cloud CLI or Console:
gcloud compute ssh yan@data-fetcher --zone us-central1-a --ssh-key-file ~/.ssh/gcp_web3dev_vm-data-fetcher.pub

Step 3: Configure SSH in Visual Studio Code
Open Visual Studio Code.

Press F1 to open the command palette.

Type and select "Remote-SSH: Add New SSH Host...".

Step 4: Connect to Your VM Using SSH in Visual Studio Code
Press F1 to open the command palette.
Type and select "Remote-SSH: Connect to Host...".
Select the host you configured (e.g., your_vm_name).
VSCode will now open a new window and connect to your VM over SSH. You can start working on your VM directly from VSCode.

## Setup access to write at bigquery
Stop VM
gcloud compute instances stop data-fetcher --zone us-central1-a
Create one service account to read and write at BigQuery (Bigquery Editor) and Associate with this VM.

gcloud iam service-accounts create data-fetcher \
    --description="Service account for data fetching operations" \
    --display-name="Data Fetcher"

gcloud projects add-iam-policy-binding web3dev-scrapers \
    --member="serviceAccount:data-fetcher@web3dev-scrapers.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding web3dev-scrapers \
    --member="serviceAccount:data-fetcher@web3dev-scrapers.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataViewer"


OBS: This account must have access to read and write at the target bigquery project. If you are contributing to web3dev be sure you account has the proper access to succeed.

## Start Working
`sudo apt update`
`git clone https://github.com/w3b3d3v/web3-community-insights.git && cd web3-community-insights`
`sudo apt install -y python3-venv python3-pip`